"""
detector.py — Production-optimized bird detector for Raspberry Pi 4
Terintegrasi dengan Cloudflare Tunnels via Flask Micro-Server (Port 8080)
"""
import cv2
import serial
import threading
import time
import logging
import os
import subprocess
from dotenv import load_dotenv
from ultralytics import YOLO
from flask import Flask, Response, jsonify, request



# Load environment variables
load_dotenv()

# ==============================
# KONFIGURASI DARI .ENV
# ==============================
ENABLE_ESP32 = os.getenv("ENABLE_ESP32", "False").lower() in ("true", "1", "t", "yes")
ESP32_SERIAL_PORT = os.getenv("ESP32_SERIAL_PORT", "/dev/ttyUSB0")
CAMERA_SRC  = os.getenv("CAMERA_SRC", "0") 
MODEL_PATH  = os.getenv("MODEL_PATH", "best.pt")
SHOW_UI     = os.getenv("SHOW_UI", "False").lower() in ("true", "1", "t", "yes")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "MATAPADI-SECRET-99X")

if CAMERA_SRC.isdigit():
    CAMERA_SRC = int(CAMERA_SRC)

CONF_THRESHOLD   = float(os.getenv("CONF_THRESHOLD", "0.45"))
TRIGGER_DELAY_S  = float(os.getenv("TRIGGER_DELAY_S", "3.0"))
INFER_INTERVAL_S = float(os.getenv("INFER_INTERVAL_S", "0.4"))
INFER_IMGSZ      = int(os.getenv("INFER_IMGSZ", "320"))

# ==============================
# LOGGING TERSTRUKTUR
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)
log = logging.getLogger("sparrow-detector")

# ==============================
# GLOBAL STATE (Untuk Web Server)
# ==============================
latest_jpeg = None
jpeg_lock = threading.Lock()
system_stats = {
    "status": "online",
    "sparrows_detected_total": 0,
    "buzzer_active": False,
    "cpu_temp": "N/A",
    "buzzer_mode": "auto"
}

app = Flask(__name__)
global_buzzer = None

def get_cpu_temp():
    try:
        temp = subprocess.check_output(['vcgencmd', 'measure_temp']).decode('utf-8')
        return temp.replace("temp=", "").strip()
    except:
        return "N/A"

@app.route('/')
def index():
    return jsonify({"message": "Sparrow Embedded System API", "status": "200 OK"})

@app.before_request
def require_api_key():
    # Izinkan /stream terbuka (karena diakses via tag <img> HTML) dan rute utama /
    if request.path in ['/stream', '/']:
        return
        
    api_key = request.headers.get('x-api-key')
    if api_key != API_SECRET_KEY:
        log.warning(f"Unauthorized access attempt to {request.path} from {request.remote_addr}")
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/stats')
def stats():
    system_stats["cpu_temp"] = get_cpu_temp()
    return jsonify(system_stats)

@app.route('/api/buzzer', methods=['POST'])
def control_buzzer():
    global global_buzzer
    if global_buzzer is None:
        return jsonify({"error": "Buzzer not initialized"}), 500
        
    data = request.json or {}
    mode = data.get("mode")
    
    if mode == "force_on":
        global_buzzer.set_manual(True, True)
        return jsonify({"status": "forced_on"})
    elif mode == "auto":
        global_buzzer.set_manual(False, False)
        return jsonify({"status": "auto_restored"})
        
    return jsonify({"error": "Invalid mode"}), 400

def generate_mjpeg():
    """Generator MJPEG — Flask thread hanya membaca bytes, TANPA memanggil OpenCV."""
    global latest_jpeg, jpeg_lock
    while True:
        with jpeg_lock:
            if latest_jpeg is None:
                time.sleep(0.1)
                continue
            frame_bytes = latest_jpeg
        
        # Kirim byte stream ke browser
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        # Limit frame rate stream ke ~15 FPS agar tidak menyiksa CPU & Jaringan
        time.sleep(0.06)

@app.route('/stream')
def stream():
    return Response(generate_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=frame')


# ==============================
# STATE MESIN BUZZER (thread-safe)
# ==============================
class BuzzerController:
    def __init__(self, port: str):
        self._port = port
        self._is_on = False
        self._last_trigger = 0.0
        self._manual_override = False
        self._lock = threading.Lock()
        self._serial = None
        
        if ENABLE_ESP32:
            try:
                self._serial = serial.Serial(self._port, 115200, timeout=1)
                log.info("Berhasil membuka Serial Port: %s", self._port)
            except serial.SerialException as e:
                log.error("Gagal membuka Serial Port %s: %s", self._port, e)

    def set_manual(self, manual: bool, state: bool):
        global system_stats
        with self._lock:
            self._manual_override = manual
            system_stats["buzzer_mode"] = "manual" if manual else "auto"
            
            if manual:
                if state and not self._is_on:
                    if self._send("ON"):
                        self._is_on = True
                        system_stats["buzzer_active"] = True
            else:
                if self._is_on:
                    if self._send("OFF"):
                        self._is_on = False
                        system_stats["buzzer_active"] = False

    def update(self, detected: bool) -> None:
        global system_stats
        with self._lock:
            if self._manual_override:
                return # AI diabaikan saat Override
            
            now = time.time()
            if detected and not self._is_on:
                if (now - self._last_trigger) >= TRIGGER_DELAY_S:
                    if self._send("ON"):
                        self._is_on = True
                        self._last_trigger = now
                        system_stats["buzzer_active"] = True
            elif not detected and self._is_on:
                if self._send("OFF"):
                    self._is_on = False
                    system_stats["buzzer_active"] = False

    def _send(self, command: str) -> bool:
        if not ENABLE_ESP32 or self._serial is None:
            return True
            
        try:
            pesan = command + "\n"
            self._serial.write(pesan.encode('utf-8'))
            log.info("ESP32 dikirimi sinyal Serial: %s", command)
            return True
        except serial.SerialException as e:
            log.warning("Kabel USB ESP32 terputus atau gagal mengirim: %s", e)
            return False

    def force_off(self) -> None:
        self._send("OFF")
        self._is_on = False
        if self._serial:
            self._serial.close()


# ==============================
# MAIN DETECTOR
# ==============================
def main():
    global latest_jpeg, jpeg_lock, system_stats

    log.info("Memuat model YOLO dari: %s", MODEL_PATH)
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        log.error("Gagal memuat model. Apakah file %s ada? Error: %s", MODEL_PATH, e)
        return

    buzzer = BuzzerController(ESP32_SERIAL_PORT)
    global global_buzzer
    global_buzzer = buzzer

    log.info("Membuka sumber kamera/video: %s", CAMERA_SRC)
    cap = cv2.VideoCapture(CAMERA_SRC)
    if not cap.isOpened():
        log.error("Gagal membuka kamera/video. Periksa CAMERA_SRC di .env!")
        return

    # Optimasi latensi: minimalkan buffer internal OpenCV untuk RTSP
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if isinstance(CAMERA_SRC, int):
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Menyalakan FLASK SERVER di Background Thread
    flask_thread = threading.Thread(target=app.run, kwargs={"host":"0.0.0.0", "port":8080, "debug":False, "use_reloader":False})
    flask_thread.daemon = True # Agar thread ikut mati jika program utama dihentikan
    flask_thread.start()
    log.info("🌐 Web Server API & Video Streaming AKTIF di port 8080")

    log.info("Sistem deteksi burung aktif. Tekan Ctrl+C di terminal untuk berhenti.")
    last_infer_time = 0.0
    last_jpeg_time = 0.0
    JPEG_INTERVAL_S = 0.1  # Max 10 FPS untuk streaming

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if isinstance(CAMERA_SRC, str):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    log.warning("Kamera terputus.")
                    break

            now = time.time()

            if (now - last_infer_time) < INFER_INTERVAL_S:
                if SHOW_UI:
                    cv2.imshow("Deteksi Burung Pipit", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # BATASI ENCODE JPEG MAX 10 FPS AGAR LOOP BISA MEMBUANG FRAME LAMA DGN CEPAT
                if (now - last_jpeg_time) >= JPEG_INTERVAL_S:
                    ret_enc, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                    if ret_enc:
                        with jpeg_lock:
                            latest_jpeg = jpeg.tobytes()
                    last_jpeg_time = now
                continue

            last_infer_time = now

            # NCNN mengharuskan ukuran array mutlak persegi, jika tidak ia akan crash (502)
            infer_frame = cv2.resize(frame, (INFER_IMGSZ, INFER_IMGSZ))
            
            t0 = time.perf_counter()
            results = model(infer_frame, verbose=False, imgsz=INFER_IMGSZ)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            detected = False
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    label  = r.names[cls_id].lower()
                    conf   = float(box.conf[0])
                    
                    if conf >= CONF_THRESHOLD:
                        detected = True
                        system_stats["sparrows_detected_total"] += 1
                        log.info("🕊️ DETECTED %s conf=%.2f inference_ms=%.1f", label, conf, elapsed_ms)
                        
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        h, w, _ = frame.shape
                        scale_x, scale_y = w / INFER_IMGSZ, h / INFER_IMGSZ
                        x1, y1 = int(x1 * scale_x), int(y1 * scale_y)
                        x2, y2 = int(x2 * scale_x), int(y2 * scale_y)
                        
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        break
                if detected:
                    break

            buzzer.update(detected)

            fps_text = f"Infer: {elapsed_ms:.1f}ms | Buzzer: {'ON' if buzzer._is_on else 'OFF'}"
            cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Encode JPEG di main thread dan simpan untuk Web Streaming
            if (now - last_jpeg_time) >= JPEG_INTERVAL_S:
                ret_enc, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                if ret_enc:
                    with jpeg_lock:
                        latest_jpeg = jpeg.tobytes()
                last_jpeg_time = now

            if SHOW_UI:
                cv2.imshow("Deteksi Burung Pipit", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    log.info("Keluar (dihentikan oleh user).")
                    break

    except KeyboardInterrupt:
        log.info("Shutdown signal diterima (Ctrl+C).")
    finally:
        log.info("Mematikan buzzer dan cleanup...")
        try:
            buzzer.force_off()
        except Exception as e:
            log.warning("Abaikan error jaringan saat mematikan buzzer: %s", e)
            
        try:
            cap.release()
            if SHOW_UI:
                cv2.destroyAllWindows()
        except Exception:
            pass
        log.info("Sistem berhenti. ✅")

if __name__ == "__main__":
    main()

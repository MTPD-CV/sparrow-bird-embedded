"""
detector.py — Production-optimized bird detector for Raspberry Pi 3
Menggabungkan best practices dari sparow.py + deteksi_burung.py
dengan semua optimasi untuk embedded ARM deployment.
"""
import cv2
import requests
import threading
import time
import logging
import os
from dotenv import load_dotenv
from ultralytics import YOLO

# Load environment variables
load_dotenv()

# ==============================
# KONFIGURASI DARI .ENV
# ==============================
ENABLE_ESP32 = os.getenv("ENABLE_ESP32", "False").lower() in ("true", "1", "t", "yes")
ESP32_URL   = os.getenv("ESP32_URL", "http://192.168.1.100")
CAMERA_SRC  = os.getenv("CAMERA_SRC", "0") 
MODEL_PATH  = os.getenv("MODEL_PATH", "best.pt")

# Ubah tipe data untuk CAMERA_SRC jika berupa angka (webcam index)
if CAMERA_SRC.isdigit():
    CAMERA_SRC = int(CAMERA_SRC)

CONF_THRESHOLD   = float(os.getenv("CONF_THRESHOLD", "0.45"))
TRIGGER_DELAY_S  = float(os.getenv("TRIGGER_DELAY_S", "3.0"))
INFER_INTERVAL_S = float(os.getenv("INFER_INTERVAL_S", "0.4"))
INFER_IMGSZ      = int(os.getenv("INFER_IMGSZ", "320"))

HTTP_TIMEOUT_S   = 1.5    # Timeout HTTP ke ESP32
MAX_RETRIES      = 2      # Retry HTTP sebelum skip

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
# STATE MESIN BUZZER (thread-safe)
# ==============================
class BuzzerController:
    def __init__(self, base_url: str):
        self._url = base_url
        self._is_on = False
        self._last_trigger = 0.0
        self._lock = threading.Lock()

    def update(self, detected: bool) -> None:
        """Kirim sinyal ke ESP32 hanya jika state berubah atau butuh direfresh."""
        with self._lock:
            now = time.time()
            if detected and not self._is_on:
                if (now - self._last_trigger) >= TRIGGER_DELAY_S:
                    if self._send("buzzer_on"):
                        self._is_on = True
                        self._last_trigger = now
            elif not detected and self._is_on:
                if self._send("buzzer_off"):
                    self._is_on = False

    def _send(self, command: str) -> bool:
        if not ENABLE_ESP32:
            return True
            
        for attempt in range(MAX_RETRIES):
            try:
                r = requests.get(f"{self._url}/{command}", timeout=HTTP_TIMEOUT_S)
                log.info("ESP32 command=%s status=%d", command, r.status_code)
                return r.status_code == 200
            except requests.exceptions.RequestException as e:
                log.warning("ESP32 send attempt %d/%d failed: %s", attempt+1, MAX_RETRIES, e)
        return False

    def force_off(self) -> None:
        """Dipanggil saat shutdown — pastikan buzzer mati."""
        self._send("buzzer_off")
        self._is_on = False

# ==============================
# MAIN DETECTOR
# ==============================
def main():
    log.info("Memuat model YOLO dari: %s", MODEL_PATH)
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        log.error("Gagal memuat model. Apakah file %s ada? Error: %s", MODEL_PATH, e)
        return

    buzzer = BuzzerController(ESP32_URL)

    log.info("Membuka sumber kamera/video: %s", CAMERA_SRC)
    cap = cv2.VideoCapture(CAMERA_SRC)
    if not cap.isOpened():
        log.error("Gagal membuka kamera/video. Periksa CAMERA_SRC di .env!")
        return

    # Jika memakai webcam (index numerik), atur resolusi kamera
    if isinstance(CAMERA_SRC, int):
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    log.info("Sistem deteksi burung aktif. Tekan 'q' di jendela video atau Ctrl+C di terminal untuk berhenti.")
    last_infer_time = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                # Jika input berupa file video (looping)
                if isinstance(CAMERA_SRC, str):
                    log.info("Video selesai. Mengulang kembali...")
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    log.warning("Kamera terputus.")
                    break

            now = time.time()

            # ✅ Frame skipping — hanya inferensi setiap INFER_INTERVAL_S
            if (now - last_infer_time) < INFER_INTERVAL_S:
                # Kita tetap harus memproses UI OpenCV agar tidak not-responding
                cv2.imshow("Deteksi Burung Pipit", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            last_infer_time = now

            # ✅ Resize frame untuk mempercepat inferensi (sangat krusial di ARM RPi)
            infer_frame = cv2.resize(frame, (INFER_IMGSZ, INFER_IMGSZ))

            # ✅ Inferensi YOLO
            t0 = time.perf_counter()
            results = model(infer_frame, verbose=False, imgsz=INFER_IMGSZ)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            detected = False
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    label  = r.names[cls_id].lower()
                    conf   = float(box.conf[0])
                    
                    if label == "sparrow" and conf >= CONF_THRESHOLD:
                        detected = True
                        log.info("🕊️ DETECTED sparrow conf=%.2f inference_ms=%.1f", conf, elapsed_ms)
                        
                        # Ambil bounding box untuk digambar
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        # Mengembalikan skala ke ukuran frame asli
                        h, w, _ = frame.shape
                        scale_x, scale_y = w / INFER_IMGSZ, h / INFER_IMGSZ
                        x1, y1 = int(x1 * scale_x), int(y1 * scale_y)
                        x2, y2 = int(x2 * scale_x), int(y2 * scale_y)
                        
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, f"Sparrow {conf:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        break
                if detected:
                    break

            if not detected:
                log.debug("No detection | inference_ms=%.1f", elapsed_ms)

            # ✅ Kontrol ESP32 (State Machine, bukan flood/spam)
            buzzer.update(detected)

            # Menampilkan FPS Info di layar
            fps_text = f"FPS Limit: {1/INFER_INTERVAL_S:.1f} | Infer: {elapsed_ms:.1f}ms"
            cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Tampilkan hasil di jendela OpenCV
            cv2.imshow("Deteksi Burung Pipit", frame)

            # Tekan 'q' untuk keluar
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
            cv2.destroyAllWindows()
        except Exception:
            pass
        log.info("Sistem berhenti. ✅")

if __name__ == "__main__":
    main()

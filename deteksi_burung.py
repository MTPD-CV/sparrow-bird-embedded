import cv2
import requests
import threading
import time
from ultralytics import YOLO

# ==============================
# Konfigurasi
# ==============================
ESP32_URL = "http://192.168.1.100"  # Ganti dengan IP ESP32
VIDEO_PATH = "sparow.mp4"           # Video burung lokal
MODEL_PATH = "best.pt"              # Model YOLOv8 custom
# ==============================

# Inisialisasi YOLOv8
model = YOLO(MODEL_PATH)

frame = None
lock = threading.Lock()
running = True

# ==============================
# Fungsi untuk membaca frame video (loop terus-menerus)
# ==============================
def capture_frames():
    global frame, running
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("❌ Gagal membuka video, periksa file path!")
        running = False
        return

    while running:
        ret, new_frame = cap.read()

        # Jika video selesai, ulangi dari awal
        if not ret:
            print("🔄 Video selesai, mengulang dari awal...")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        with lock:
            frame = new_frame

        time.sleep(0.03)  # jeda 30ms ~ 33 FPS

    cap.release()

# ==============================
# Fungsi kirim sinyal ke ESP32
# ==============================
def send_signal_to_esp32(command):
    try:
        requests.get(f"{ESP32_URL}/{command}", timeout=1)
        print(f"📡 Sinyal terkirim ke ESP32: {command}")
    except Exception as e:
        print(f"⚠ Error kirim ke ESP32: {e}")

# ==============================
# Jalankan thread video
# ==============================
thread = threading.Thread(target=capture_frames)
thread.start()

# ==============================
# Proses utama deteksi
# ==============================
try:
    while running:
        with lock:
            current_frame = frame.copy() if frame is not None else None

        if current_frame is None:
            time.sleep(0.05)
            continue

        # Resize agar lebih ringan
        resized_frame = cv2.resize(current_frame, (640, 480))
        start_time = time.time()

        # Jalankan deteksi YOLO
        results = model(resized_frame)
        end_time = time.time()

        detected = False
        for r in results:
            for box in r.boxes:
                class_id = int(box.cls[0])
                label = r.names[class_id]
                conf = float(box.conf[0])

                # Ambil koordinat bounding box
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Gambar kotak di frame
                cv2.rectangle(resized_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    resized_frame,
                    f"{label} {conf:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

                # Deteksi hanya burung "sparrow"
                if label.lower() == "sparrow" and conf > 0.5:
                    detected = True
                    print(f"🕊️ Burung terdeteksi! Confidence: {conf:.2f}")

        print(f"Detected: {detected} | FPS: {1 / (end_time - start_time):.2f}")

        # Kontrol ESP32
        if detected:
            send_signal_to_esp32("buzzer_on")
        else:
            send_signal_to_esp32("buzzer_off")

        # Tampilkan hasil di jendela OpenCV
        cv2.imshow("Deteksi Burung", resized_frame)

        # Tekan ESC (27) untuk keluar
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            print("❌ Program dihentikan oleh user (ESC).")
            # Matikan buzzer sebelum keluar
            send_signal_to_esp32("buzzer_off")
            running = False
            break

finally:
    # Pastikan semua bersih saat keluar
    running = False
    thread.join()

    # Matikan buzzer jika masih menyala
    send_signal_to_esp32("buzzer_off")

    cv2.destroyAllWindows()
    print("Program selesai dan sistem berhenti mendeteksi. ✅")

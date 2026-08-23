import cv2
import requests
import time
from ultralytics import YOLO

# ======= KONFIGURASI =======
VIDEO_PATH = "sparow.mp4"
MODEL_PATH = "best.pt"
ESP32_URL = "http://192.168.1.100"  # IP ESP32 (pastikan benar)  
DETEKSI_LABEL = ["sparrow"]
TRIGGER_DELAY = 5  # detik antara sinyal ON
DETEKSI_CONF_THRESHOLD = 0.4  # Confidence minimal

# ======= INISIALISASI =======
model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("❌ Gagal membuka video.")
    exit()

last_trigger_time = 0
buzzer_is_on = False  # Status terakhir buzzer

# ======= FUNGSI KIRIM KE ESP32 =======
def send_signal_to_esp32(state):
    try:
        url = f"{ESP32_URL}/{state}"
        response = requests.get(url, timeout=2)
        print(f"📡 Kirim ke ESP32: {state} -> {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Gagal kirim ke ESP32: {e}")
        return False

# ======= LOOP DETEKSI =======
print("🚀 Mulai deteksi burung dari video... Tekan 'Q' untuk keluar.")
while True:
    ret, frame = cap.read()
    if not ret:
        print("✅ Video selesai.")
        break

    frame = cv2.resize(frame, (640, 480))
    results = model(frame, verbose=False)

    detected = False
    for r in results:
        for box in r.boxes:
            class_id = int(box.cls[0])
            label = r.names[class_id].lower()
            conf = float(box.conf[0])

            if label in DETEKSI_LABEL and conf > DETEKSI_CONF_THRESHOLD:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                detected = True

    # Kirim sinyal ke ESP32 hanya jika status berubah
    now = time.time()
    if detected:
        if not buzzer_is_on and (now - last_trigger_time > TRIGGER_DELAY):
            if send_signal_to_esp32("buzzer_on"):
                buzzer_is_on = True
                last_trigger_time = now
    else:
        if buzzer_is_on:
            if send_signal_to_esp32("buzzer_off"):
                buzzer_is_on = False

    # Tampilkan hasil
    cv2.imshow("Deteksi Burung", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print("🛑 Deteksi dihentikan oleh user. Mematikan buzzer...")
        send_signal_to_esp32("buzzer_off")
        break

cap.release()
cv2.destroyAllWindows()

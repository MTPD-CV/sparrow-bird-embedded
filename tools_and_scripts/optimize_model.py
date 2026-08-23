"""
optimize_model.py — Script untuk mengekspor model PyTorch (.pt) ke NCNN INT8
Didesain untuk diproses di laptop sebelum di-deploy ke Raspberry Pi.

PRASYARAT:
1. Pastikan ultralytics terinstall: pip install ultralytics
2. Model 'best.pt' Anda harus berada di direktori yang sama.
"""

import os
import time
from ultralytics import YOLO
from dotenv import load_dotenv

# Load env variables untuk mendapatkan path model (opsional)
load_dotenv()
MODEL_PATH = os.getenv("MODEL_PATH", "best.pt")

def export_to_ncnn():
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Model {MODEL_PATH} tidak ditemukan.")
        print("Silakan pastikan best.pt ada di direktori ini.")
        return

    print("==================================================")
    print(f"🚀 Memulai proses eksportasi {MODEL_PATH} ke NCNN INT8")
    print("==================================================")
    print("Mengekspor model ini akan memakan waktu beberapa menit.")
    print("Model NCNN INT8 dioptimasi khusus untuk CPU ARM (Raspberry Pi),")
    print("ukuran model akan turun secara drastis dari ~50MB menjadi ~5-15MB.")

    try:
        # Load model PyTorch standar
        model = YOLO(MODEL_PATH)
        
        t0 = time.time()
        # Ekspor ke format NCNN dengan Kuantisasi FP16 (half=True)
        # imgsz=320 adalah best practice untuk RPi (keseimbangan akurasi & FPS)
        exported_path = model.export(
            format="ncnn", 
            half=True,       # Enable FP16 quantization (INT8 tidak disupport otomatis oleh Ultralytics ncnn)
            imgsz=320        # Resize input
        )
        t1 = time.time()

        print("\n==================================================")
        print("✅ PROSES EKSPOR BERHASIL!")
        print(f"⏳ Waktu proses: {t1 - t0:.1f} detik")
        print(f"📂 Lokasi output: {exported_path}")
        print("==================================================")
        print("Langkah selanjutnya:")
        print("1. Ubah MODEL_PATH di file .env Anda menjadi path folder output di atas")
        print("   Contoh: MODEL_PATH=best_ncnn_model")
        print("2. Uji jalankan skrip detector.py")
        print("3. Pindahkan seluruh folder model NCNN tersebut ke Raspberry Pi 3.")

    except Exception as e:
        print("\n❌ Gagal melakukan eksportasi model!")
        print("Error message:", e)
        print("\nJika error terkait ketiadaan library ncnn, jalankan:")
        print("pip install ncnn ultralytics[export]")

if __name__ == "__main__":
    export_to_ncnn()

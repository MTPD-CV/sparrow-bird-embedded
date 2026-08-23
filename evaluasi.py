import os
import shutil
from dotenv import load_dotenv
from roboflow import Roboflow
from ultralytics import YOLO

def main():
    print("="*50)
    print("🚀 Memulai Proses Evaluasi Model (Confusion Matrix)")
    print("="*50)

    # 1. Load API Key
    load_dotenv()
    rf_key = os.getenv("ROBOFLOW_API_KEY")
    if not rf_key:
        print("❌ Error: ROBOFLOW_API_KEY tidak ditemukan di file .env!")
        return

    # 2. Download Dataset
    print("\n📦 Mengunduh dataset dari Roboflow (Mohon tunggu)...")
    rf = Roboflow(api_key=rf_key)
    project = rf.workspace("burung-e-0dpq0").project("sparrow-izsmx")
    version = project.version(1)
    dataset = version.download("yolov8")
    
    print(f"✅ Dataset tersimpan di: {dataset.location}")

    # 3. Jalankan Validasi
    print("\n🔍 Memulai proses validasi model (best.pt)...")
    print("⏳ Proses ini memakan waktu beberapa menit tergantung kecepatan laptop Anda.")
    
    model = YOLO('best.pt')
    
    # model.val() akan otomatis mengevaluasi model dan menyimpan hasilnya
    metrics = model.val(data=f"{dataset.location}/data.yaml", imgsz=320)
    
    # 4. Ambil dan pindahkan Confusion Matrix agar mudah diakses
    save_dir = metrics.save_dir
    matrix_path = os.path.join(save_dir, 'confusion_matrix.png')
    
    if os.path.exists(matrix_path):
        # Salin confusion matrix ke folder utama burung-pipit agar langsung terlihat
        output_path = "hasil_confusion_matrix.png"
        shutil.copy(matrix_path, output_path)
        print("\n" + "="*50)
        print("🎉 EVALUASI SELESAI!")
        print(f"✅ Gambar Confusion Matrix berhasil diekstrak.")
        print(f"👉 Silakan klik 2x file bernama: '{output_path}' yang baru saja muncul di folder Anda.")
        print("="*50)
    else:
        print("\n❌ Gagal menemukan file Confusion Matrix. Silakan cek pesan log di atas.")

if __name__ == "__main__":
    main()

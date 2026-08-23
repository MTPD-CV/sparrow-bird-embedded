import cv2
import os

def extract_frames(video_path, output_folder, frame_interval=30):
    """
    Mengekstrak frame dari video untuk dijadikan dataset.
    frame_interval = 30 artinya mengambil 1 gambar setiap 30 frame (sekitar 1 gambar per detik).
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📁 Membuat folder baru: {output_folder}")
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Error: Tidak bisa membuka video '{video_path}'. Pastikan nama file benar!")
        return
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"🎥 Membaca video (FPS: {fps}). Mengekstrak setiap {frame_interval} frame...")
    
    frame_count = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break # Video habis
            
        # Simpan gambar setiap kelipatan frame_interval
        if frame_count % frame_interval == 0:
            filename = os.path.join(output_folder, f"bg_negatif_{saved_count:04d}.jpg")
            cv2.imwrite(filename, frame)
            saved_count += 1
            
        frame_count += 1
        
    cap.release()
    print(f"✅ Selesai! {saved_count} gambar berhasil diekstrak dan disimpan di folder '{output_folder}'.")

if __name__ == "__main__":
    # --- PENGATURAN ---
    NAMA_VIDEO = "video_sawah.mp4" # Ganti dengan nama video Anda
    NAMA_FOLDER = "dataset_negatif"
    INTERVAL = 30 # Jika video 30 FPS, nilai 30 = ambil 1 foto tiap detik
    
    print("Mulai mengekstrak dataset...")
    extract_frames(NAMA_VIDEO, NAMA_FOLDER, INTERVAL)

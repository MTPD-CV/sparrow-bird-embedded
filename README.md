# 🐦 Edge-AI Sparrow Detection System

Sistem Visi Komputer (*Computer Vision*) produksi yang dioptimasi khusus untuk perangkat *Edge* **Raspberry Pi 4 (RAM 4GB)**. Sistem ini menggunakan model kecerdasan buatan **YOLOv8** untuk mendeteksi hama burung pipit di area persawahan secara *real-time*, lalu secara otomatis mengirimkan sinyal ke mikrokontroler **ESP32** untuk membunyikan alarm/buzzer pengusir burung.

## 🏗️ Arsitektur Sistem

*   **Model AI:** Ultralytics YOLOv8 (Dikuantisasi ke format NCNN FP16 untuk performa maksimal di prosesor ARM Cortex-A72).
*   **Edge Processor:** Raspberry Pi 4 Model B (4GB RAM).
*   **Sistem Operasi Wajib:** Raspberry Pi OS Lite 64-bit (Sangat penting agar NCNN bisa berjalan dengan performa maksimal).
*   **Actuator (Alarm):** ESP32 Module.
*   **Protokol Komunikasi:** HTTP REST API (Dilengkapi sistem *Frame Skipping* dan *Thread Lock* anti-DDoS).

---

## 📂 Struktur Direktori Proyek

Semua skrip di dalam proyek ini telah menerapkan prinsip *Clean Code*, *Error Handling* produksi, dan *Structured Logging*.

1.  **`detector.py`** 🚀 **(CORE / PRODUCTION)**
    Skrip utama yang akan dijalankan 24/7 di Raspberry Pi. Skrip ini membaca *feed* kamera, menjalankan inferensi YOLOv8 dengan format NCNN yang sangat ringan, dan mengatur logika "kapan alarm ESP32 harus berbunyi" secara pintar (mencegah *spam* sinyal).
2.  **`optimize_model.py`** ⚙️
    Skrip utilitas untuk menerjemahkan dan mengkuantisasi (*compress*) model `best.pt` asli Anda menjadi format `NCNN FP16`. Ini menurunkan ukuran model hingga 50% dan meningkatkan kecepatan inferensi (FPS) secara drastis tanpa mengorbankan akurasi.
3.  **`evaluasi.py`** 📊
    Skrip otomatisasi untuk memvalidasi model Anda secara lokal (Confusion Matrix).
4.  **`unsplash.py`** 🖼️
    Skrip ekstra untuk mengumpulkan *raw dataset* tambahan dari API Unsplash.
5.  **`.env`** 🔐
    File konfigurasi terpusat. Berisi seluruh API Key rahasia dan parameter *tuning* perangkat keras.

---

## 💾 PANDUAN INSTALASI OS RASPBERRY PI 4 (HEADLESS)

Karena RPi 4 Anda saat ini kosong (tanpa OS) dan kita ingin menjadikannya server tanpa layar (*Headless*), ikuti panduan rahasia ini menggunakan komputer Windows Anda:

1. Siapkan **MicroSD Card (Minimal 16GB)** dan colokkan ke laptop Anda.
2. Download dan buka aplikasi **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)**.
3. Di dalam aplikasi Imager:
   * **Choose Device:** Pilih *Raspberry Pi 4*.
   * **Choose OS:** Pilih *Raspberry Pi OS (Other)* -> **Raspberry Pi OS Lite (64-bit)**. (JANGAN pilih yang 32-bit).
   * **Choose Storage:** Pilih MicroSD Anda.
4. **⚠️ LANGKAH PALING PENTING (OS Customization):**
   Klik tombol gerigi (Settings) atau tekan tombol `CTRL + SHIFT + X` di keyboard Anda, lalu isikan data berikut:
   * Centang **Enable SSH** -> Gunakan opsi *Use password authentication*.
   * Centang **Set username and password** -> Isi *Username* (misal: `pi`) dan *Password* yang mudah diingat.
   * Centang **Configure wireless LAN** -> Isi *SSID* dan *Password* Wi-Fi rumah tangga/Hotspot HP Anda (Pastikan laptop dan RPi nanti terhubung di Wi-Fi yang sama!). Ubah *Wireless LAN country* menjadi `ID`.
   * Centang **Set locale settings** -> Time zone: `Asia/Jakarta`.
   * Klik **Save**.
5. Klik **WRITE** dan tunggu sampai proses instalasi selesai.
6. Cabut MicroSD, masukkan ke slot di Raspberry Pi 4, lalu colokkan kabel *Power* (USB Type-C) ke RPi 4.
7. RPi 4 Anda akan menyala, mengonfigurasi dirinya sendiri, dan otomatis terhubung ke Wi-Fi Anda.

---

## 🛠️ Instalasi Proyek (Local / RPi)

1.  **Buat Virtual Environment:**
    ```bash
    python -m venv .venv
    ```
2.  **Aktifkan Virtual Environment:**
    *   Windows: `.\.venv\Scripts\Activate.ps1`
    *   Linux/RPi: `source .venv/bin/activate`
3.  **Instal Dependensi:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Jalankan Sistem Produksi:**
    ```bash
    python detector.py
    ```

---

## ⚠️ Catatan Stabilitas RPi 4

*   **Pendingin:** Walaupun sangat *powerful*, chip Cortex-A72 milik RPi 4 menghasilkan panas yang ekstrem. **SANGAT DIWAJIBKAN** menggunakan *Heatsink* dan Kipas (*Fan*) aktif pada RPi 4 Anda. Tanpa kipas, sistem akan mengalami *Thermal Throttling* (penurunan performa paksa) dalam waktu 5 menit saat menjalankan YOLO.
*   **Kecepatan (`.env`):** Fitur pembatasan kecepatan di `.env` (`INFER_INTERVAL_S=0.1`) sudah diatur agar aplikasi berjalan di 10 FPS secara mulus.

# 🌾 Sparrow Bird Embedded - Enterprise Off-Grid IoT System

![Status](https://img.shields.io/badge/Status-Production%20Ready-success)
![Hardware](https://img.shields.io/badge/Hardware-Raspberry%20Pi%20%7C%20ESP32-blue)
![AI Framework](https://img.shields.io/badge/AI-YOLOv8%20%7C%20NCNN-orange)

Sistem Visi Komputer (*Computer Vision*) produksi yang dioptimasi khusus untuk perangkat *Edge* **Raspberry Pi 4**. Sistem ini menggunakan model kecerdasan buatan **YOLOv8 (NCNN)** untuk mendeteksi hama burung pipit di area persawahan secara *real-time*.

Proyek ini dirancang sebagai sistem **Off-Grid Mandiri 100% (Tenaga Surya)** yang mampu bertahan hidup 24 jam di tengah area pertanian tanpa aliran listrik PLN maupun jaringan internet kabel.

---

## 🏗️ Arsitektur Sistem (Hardware & Power)

Sistem ini menggunakan topologi kelistrikan kelas industri berat untuk memastikan tidak ada komponen yang terbakar akibat perbedaan tegangan (9V, 5V, dan 12V).

*   **Pusat Tenaga Surya (Off-Grid):** 
    *   2x Panel Surya Mono Crystal (Paralel)
    *   Solar Charge Controller (SCC)
    *   Baterai Aki DC 12V (22Ah) -> Kapasitas super besar untuk ketahanan 24/7.
    *   MCB DC (Sebagai Saklar Utama & Pengaman)
*   **Sistem Jaringan (9V):**
    *   Router Advan CPE (Disuplai oleh Step-Down Buck Converter 9V)
    *   Kamera IPcam RTSP (Disuplai oleh Step-Down Buck Converter 9V)
*   **Sistem Komputasi AI (5V):**
    *   **Otak Utama:** Raspberry Pi 4 (Disuplai oleh Step-Down Buck Converter 5V)
    *   **Tangan Pekerja:** ESP32 Module (Dihidupkan langsung lewat kabel USB dari Raspberry Pi)
*   **Sistem Peringatan / Aktuator (12V):**
    *   Speaker Piezoelektrik 12V (Input tenaga langsung dari MCB 12V, namun sinyal *trigger data* mengambil 3.3V dari Pin ESP32).

---

## 📡 Alur Komunikasi Data

Karena alat diletakkan di lapangan terbuka, stabilitas data sangat diutamakan:
1.  **IPcam** menangkap video sawah dan mengirimkannya ke **Router Advan** via Wi-Fi/LAN.
2.  **Raspberry Pi** menyedot arus video RTSP tersebut dari Router menggunakan **Kabel LAN** (Untuk mencegah *overheat* pada chip Wi-Fi RPi).
3.  Model **YOLOv8 (format NCNN)** di dalam Raspberry Pi menganalisis *frame* video dalam hitungan milidetik.
4.  Jika burung pipit terdeteksi dengan *Confidence Threshold* di atas ambang batas (Sweet Spot), RPi menembakkan pesan teks `ON` lewat **Kabel USB (Serial)** ke ESP32.
5.  **ESP32** bereaksi instan dan mengalirkan sinyal data 3.3V ke **Speaker 12V** untuk mengusir burung.

---

## 📂 Struktur Direktori

Semua skrip di dalam proyek ini telah menerapkan prinsip *Clean Code*, *Error Handling* produksi, dan pembatasan beban memori.

1.  **`deploy_rpi/detector.py`** 🚀 **(CORE / PRODUCTION)**
    Skrip utama yang dijalankan di Raspberry Pi. Menggabungkan pembacaan kamera RTSP, inferensi AI berkecepatan tinggi, dan komunikasi Serial dengan ESP32.
2.  **`deploy_rpi/.env`** 🔐
    File konfigurasi lingkungan. Berisi pengaturan alamat RTSP, port USB (`/dev/ttyUSB0`), dan parameter *threshold* AI. *(Tidak diunggah ke Git demi keamanan).*
3.  **`optimize_model.py`** ⚙️
    Skrip untuk mengekspor dan mengompresi model dari PyTorch (`.pt`) menjadi format Tencent NCNN. Memangkas waktu inferensi secara radikal di prosesor ARM.
4.  **`evaluasi.py`** 📊
    Skrip untuk mengukur tingkat keakuratan (*Confusion Matrix*) dari model yang dilatih.

---

## 🛠️ Panduan Instalasi (Software)

1.  **Kloning Repositori:**
    ```bash
    git clone https://github.com/MTPD-CV/sparrow-bird-embedded.git
    cd sparrow-bird-embedded
    ```

2.  **Siapkan Virtual Environment (Sangat Disarankan di RPi):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instal Library AI:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Konfigurasi Sistem:**
    Buat file `.env` (bisa menyalin dari `.env.example`) dan sesuaikan alamat RTSP IPcam serta Port USB ESP32 Anda.

5.  **Jalankan Sistem Penjaga Sawah:**
    ```bash
    cd deploy_rpi
    python detector.py
    ```

---
*Dikembangkan secara khusus untuk ketahanan sistem pertanian cerdas (Smart Agriculture).*

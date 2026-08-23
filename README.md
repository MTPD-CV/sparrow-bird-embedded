# 🌾 Sparrow Bird Embedded - Enterprise Off-Grid IoT System

![Status](https://img.shields.io/badge/Status-Production%20Ready-success)
![Hardware](https://img.shields.io/badge/Hardware-Raspberry%20Pi%20%7C%20ESP32-blue)
![AI Framework](https://img.shields.io/badge/AI-YOLOv8%20%7C%20NCNN-orange)
![Networking](https://img.shields.io/badge/Network-Cloudflare%20Zero%20Trust-black)

Sistem Visi Komputer (*Computer Vision*) produksi yang dioptimasi khusus untuk perangkat *Edge* **Raspberry Pi 4**. Sistem ini menggunakan model kecerdasan buatan **YOLOv8 (NCNN)** untuk mendeteksi hama burung pipit di area persawahan secara *real-time*.

Proyek ini dirancang sebagai sistem **Off-Grid Mandiri 100% (Tenaga Surya)** yang mampu bertahan hidup 24 jam di tengah area pertanian tanpa aliran listrik PLN maupun jaringan internet kabel.

---

## 🏗️ Arsitektur Jaringan (Zero Trust Cloudflare Mesh)

Karena perangkat RPi diletakkan di lapangan menggunakan internet seluler (4G/LTE), IP Publik tidak tersedia akibat *Carrier-Grade NAT* (CGNAT). Sistem ini memecahkan masalah tersebut dengan arsitektur **Zero Trust Mesh Network**.

*   **Cloudflared Daemon:** Berjalan 24/7 di latar belakang Raspberry Pi.
*   **Tunneling:** RPi membangun lorong rahasia langsung ke *Edge Server* Cloudflare tanpa perlu membuka *port* pada *Router* (Aman dari serangan luar).
*   **Akses Global:** RPi dapat diakses dari manapun menggunakan domain khusus (`*.matapadi.biz.id`) untuk keperluan *monitoring Dashboard* dan pemeliharaan jarak jauh.

---

## ⚡ Arsitektur Kelistrikan (Hardware)

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
    *   **Tangan Pekerja:** ESP32 Module (Dihidupkan langsung lewat kabel USB Serial dari Raspberry Pi)
*   **Sistem Peringatan / Aktuator (12V):**
    *   Speaker Piezoelektrik 12V (Input tenaga langsung dari MCB 12V, namun sinyal *trigger data* mengambil 3.3V dari Pin D4 ESP32).

---

## 📡 Alur Komunikasi Data

Karena alat diletakkan di lapangan terbuka, stabilitas data sangat diutamakan:
1.  **IPcam** menangkap video sawah dan mengirimkannya ke **Router Advan** via Wi-Fi/LAN.
2.  **Raspberry Pi** menyedot arus video RTSP tersebut dari Router menggunakan **Kabel LAN** (Untuk mencegah *overheat* pada chip Wi-Fi RPi).
3.  Model **YOLOv8** di dalam Raspberry Pi menganalisis *frame* video dalam hitungan milidetik.
4.  Jika burung pipit terdeteksi dengan *Confidence Threshold* yang sesuai, RPi menembakkan pesan teks `ON` (beserta `\n`) lewat **Kabel USB Serial** ke ESP32 (`/dev/ttyUSB0`).
5.  **ESP32** bereaksi instan dan mengalirkan sinyal data 3.3V ke **Speaker 12V** untuk membunyikan alarm/suara predator.

---

## 📂 Struktur Direktori

Semua skrip di dalam proyek ini telah menerapkan prinsip *Clean Code*, *Error Handling* produksi, dan pembatasan beban memori.

1.  **`deploy_rpi/detector.py`** 🚀 **(CORE / PRODUCTION)**
    Skrip utama yang dijalankan di Raspberry Pi. Menggabungkan pembacaan kamera RTSP, inferensi AI berkecepatan tinggi, dan komunikasi Serial USB dengan ESP32.
2.  **`esp32_actuator/esp32_actuator.ino`** 🎛️
    Firmware C++ untuk dipasang di dalam ESP32. Bertugas menerjemahkan perintah Serial dari RPi menjadi tegangan kelistrikan.
3.  **`deploy_rpi/.env`** 🔐
    File konfigurasi lingkungan. Berisi pengaturan alamat RTSP, port USB, dan parameter *threshold* AI. *(Tidak diunggah ke Git demi keamanan).*
4.  **`web-app-sparrow/`** 🌐
    (Dalam Pengembangan) - Modul antarmuka web (*Dashboard*) berbasis *Modular Monolith* (Next.js) untuk pemantauan kamera jarak jauh via Cloudflare.

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

3.  **Instal Library Utama:**
    ```bash
    pip install -r requirements.txt
    pip install pyserial
    ```

4.  **Izin Akses Serial (Penting):**
    Pastikan *user* RPi Anda (misal `matapadi`) memiliki izin untuk mengakses perangkat USB.
    ```bash
    sudo usermod -a -G dialout matapadi
    ```

5.  **Jalankan Sistem Penjaga Sawah:**
    ```bash
    cd deploy_rpi
    python detector.py
    ```

---
*Dikembangkan secara khusus untuk ketahanan sistem pertanian cerdas (Smart Agriculture).*

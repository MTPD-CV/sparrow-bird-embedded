#include <Arduino.h>
// ==========================================
// MTPD-CV : ESP32 Actuator Controller
// Fungsi : Menerima perintah dari Serial USB (Raspberry Pi)
//          Lalu menyalakan/mematikan Pin D4 (Ke Speaker Piezo)
// ==========================================

const int SPEAKER_PIN = 4; // Pin D4 pada ESP32 (Sesuaikan jika Anda memakai pin lain)

void setup() {
  // Buka jalur komunikasi USB dengan kecepatan 115200 (Harus sama dengan RPi)
  Serial.begin(115200);
  
  // Atur Pin 4 sebagai Jalur Keluar (Output 3.3V)
  pinMode(SPEAKER_PIN, OUTPUT);
  
  // Pastikan Speaker mati saat pertama kali menyala
  digitalWrite(SPEAKER_PIN, LOW);
  
  // Berikan sinyal ke RPi bahwa ESP32 sudah siap kerja
  Serial.println("ESP32_READY");
}

void loop() {
  // Jika ada pesan masuk dari kabel USB (dikirim oleh Raspberry Pi)
  if (Serial.available() > 0) {
    // Baca pesan sampai karakter enter/newline
    String pesan = Serial.readStringUntil('\n');
    pesan.trim(); // Bersihkan spasi kosong
    
    // Logika Eksekutor
    if (pesan == "ON") {
      digitalWrite(SPEAKER_PIN, HIGH); // Tembak 3.3V (Speaker Nyala!)
      Serial.println("SPEAKER_IS_ON");
    } 
    else if (pesan == "OFF") {
      digitalWrite(SPEAKER_PIN, LOW);  // Matikan 3.3V (Speaker Mati)
      Serial.println("SPEAKER_IS_OFF");
    }
  }
}

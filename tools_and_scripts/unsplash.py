import requests
import os
import logging
from dotenv import load_dotenv

# Konfigurasi Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)
log = logging.getLogger("unsplash-scraper")

load_dotenv()  # Load API keys dari .env file

def download_images_from_api(search_query: str, download_path: str, per_page: int = 30, total_images: int = 200):
    """
    Download gambar dari Unsplash API dengan error handling & optimasi rate limit.
    """
    access_key = os.getenv('UNSPLASH_API_KEY')
    if not access_key:
        log.error("UNSPLASH_API_KEY tidak ditemukan di .env file.")
        return

    total_downloaded = 0
    page = 1
    
    if not os.path.exists(download_path):
        os.makedirs(download_path)
        log.info("Membuat direktori: %s", download_path)

    log.info("Mulai mengunduh %d gambar '%s'...", total_images, search_query)

    while total_downloaded < total_images:
        url = f"https://api.unsplash.com/search/photos/?query={search_query}&client_id={access_key}&page={page}&per_page={per_page}"
        
        try:
            response = requests.get(url, timeout=10)
            
            # Cek limit API Unsplash (Rate limit: 50 requests/hour untuk versi gratis)
            if response.status_code == 403:
                log.error("Rate limit Unsplash tercapai atau API Key tidak valid. Berhenti.")
                break
                
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            if not results:
                log.warning("Tidak ada lagi gambar yang ditemukan untuk '%s' di halaman %d.", search_query, page)
                break

            for photo in results:
                if total_downloaded >= total_images:
                    break
                    
                img_url = photo['urls']['regular']
                img_name = f"{search_query.replace(' ', '_')}_{total_downloaded + 1}.jpg"
                img_path = os.path.join(download_path, img_name)
                
                # Download gambar aktual
                try:
                    img_data = requests.get(img_url, timeout=15).content
                    with open(img_path, 'wb') as img_file:
                        img_file.write(img_data)
                    log.info("Downloaded [%d/%d]: %s", total_downloaded + 1, total_images, img_name)
                    total_downloaded += 1
                except requests.exceptions.RequestException as e:
                    log.error("Gagal mengunduh %s: %s", img_url, e)

            page += 1

        except requests.exceptions.RequestException as e:
            log.error("Error saat memanggil Unsplash API: %s", e)
            break

    log.info("✅ Selesai. Total gambar yang diunduh: %d", total_downloaded)

if __name__ == "__main__":
    SEARCH_QUERY = "sparrow"
    DOWNLOAD_PATH = "sparrow"
    
    # Unsplash membatasi per_page maksimal 30
    download_images_from_api(
        search_query=SEARCH_QUERY, 
        download_path=DOWNLOAD_PATH, 
        per_page=30, 
        total_images=200
    )

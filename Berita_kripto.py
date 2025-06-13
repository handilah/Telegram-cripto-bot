# Install semua dependensi yang diperlukan
!pip install -q feedparser googletrans==4.0.0-rc1 pytz requests
import feedparser
from googletrans import Translator
import requests
from datetime import datetime
import pytz
import logging
import json
import html

# === KONFIGURASI ===
BOT_TOKEN = '7918492196:AAGnKpqhmJu8hocEeGm06jKreQYUdbP0g7Y'
CHAT_ID = '7666365405'  # Ganti jika perlu

# Sumber RSS berita kripto
rss_feeds = {
    "Cointelegraph": "https://cointelegraph.com/rss",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Decrypt": "https://decrypt.co/feed"
}

# Kata kunci untuk klasifikasi berita
kata_baik = ['pump', 'bullish', 'surge', 'naik', 'record', 'approve', 'etf', 'institutional', 'gain', 'positive']
kata_buruk = ['dump', 'crash', 'bearish', 'scam', 'hack', 'hacked', 'delisted', 'loss', 'down']
kata_peringatan = ['sec', 'regulation', 'ban', 'warning', 'lawsuit', 'fud', 'investigation', 'fine']

# Daftar koin utama untuk filter
koin_teratas = [
    'bitcoin', 'btc', 'ethereum', 'eth', 'bnb', 'solana', 'sol', 'ripple', 'xrp',
    'toncoin', 'ton', 'cardano', 'ada', 'dogecoin', 'doge', 'avalanche', 'avax', 'tron', 'trx'
]

# Inisialisasi translator dan logging
translator = Translator()
logging.basicConfig(level=logging.INFO)

# Muat daftar berita yang sudah dikirim sebelumnya
def muat_dikirim():
    try:
        with open('dikirim.json') as f:
            return set(json.load(f))
    except:
        return set()

# Simpan berita yang sudah dikirim
def simpan_dikirim():
    with open('dikirim.json', 'w') as f:
        json.dump(list(dikirim), f)

# Klasifikasi berdasarkan isi judul
def klasifikasi_berita(judul):
    teks = judul.lower()
    if any(k in teks for k in kata_baik):
        return "✅ Berita Baik"
    elif any(k in teks for k in kata_buruk):
        return "❌ Berita Buruk"
    elif any(k in teks for k in kata_peringatan):
        return "⚠️ Peringatan"
    return "ℹ️ Berita Umum"

# Cek apakah relevan dengan koin besar
def relevan_dengan_koin(judul):
    teks = judul.lower()
    return any(k in teks for k in koin_teratas)

# Waktu lokal Waktu Indonesia Barat
def jam_sekarang_wib():
    tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(tz).strftime('%Y-%m-%d %H:%M WIB')

# Terjemahkan ke Bahasa Indonesia
def terjemahkan_ke_id(teks):
    try:
        hasil = translator.translate(teks, src='en', dest='id').text
        return hasil
    except Exception as e:
        logging.warning(f"Gagal menerjemahkan: {e}")
        return teks

# Kirim ke Telegram
def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": pesan, "parse_mode": "HTML"}
    response = requests.post(url, data=data)
    if response.status_code != 200:
        logging.error(f"Gagal mengirim pesan: {response.text}")

# Ambil berita dari RSS, terjemahkan, klasifikasi, dan kirim
def ambil_dan_kirim_berita():
    global dikirim
    logging.info("🔁 Mengambil dan mengirim berita...")
    for sumber, url in rss_feeds.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:4]:  # Batas 4 berita per sumber
            berita_id = entry.get("id") or entry.link
            if berita_id in dikirim or not entry.get("title"):
                continue
            judul_en = entry.title
            link = entry.link
            if relevan_dengan_koin(judul_en):
                label = klasifikasi_berita(judul_en)
                judul_id = terjemahkan_ke_id(judul_en)
                judul_id = html.escape(judul_id)
                waktu = jam_sekarang_wib()
                pesan = (
                    f"<b>{label}</b>\n"
                    f"<b>Sumber:</b> {sumber}\n"
                    f"📌 <b>{judul_id}</b>\n"
                    f"🔗 {link}\n"
                    f"🕒 {waktu}"
                )
                kirim_telegram(pesan)
                dikirim.add(berita_id)
                simpan_dikirim()
                logging.info(f"✅ Dikirim: {judul_id}")
    logging.info("✅ Selesai kirim berita.")

# === Mulai ambil dan kirim berita ===
dikirim = muat_dikirim()
ambil_dan_kirim_berita()

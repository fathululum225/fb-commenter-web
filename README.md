# Facebook Auto Commenter

Web app untuk auto-comment Facebook Reels dengan multiple accounts.

## Fitur

- 🔐 Multiple akun (isi cookie per akun)
- 🎯 Target username custom
- 📊 Atur jumlah reel & komentar
- ⏱️ Atur delay untuk keamanan
- ❤️ Auto-like setiap reel
- 📋 Live log via Server-Sent Events

## Cara Ambil Cookie Facebook

1. Login Facebook di Chrome
2. Tekan F12 → tab **Application** → **Storage** → **Cookies** → `https://www.facebook.com`
3. Copy value:
   - `c_user` → ID user (angka)
   - `xs` → session token (wajib)
   - `datr` → device token (opsional)
   - `fr` → fingerprint (opsional)

## Deploy ke Railway

1. Fork repo ini ke GitHub
2. Buka [railway.app](https://railway.app)
3. **New Project** → **Deploy from GitHub repo**
4. Pilih repo ini
5. Railway otomatis detect `Dockerfile` dan deploy
6. Setelah selesai, klik **Settings → Networking → Generate Domain**
7. Buka URL public → selesai!

## Local Testing

```bash
pip install -r requirements.txt
playwright install chromium
python app.py
# 🎵 Spotify → MP3  —  Desplegament a Render

App web per descarregar playlists, àlbums i cançons de Spotify com a MP3.
Usa **spotdl** + **yt-dlp** + **YouTube** com a font d'àudio. Sense API key.

---

## 📁 Estructura del projecte

```
spotify-web/
├── app.py            ← Servidor Flask (backend)
├── templates/
│   └── index.html    ← Interfície web
├── requirements.txt  ← Dependències Python
├── build.sh          ← Script d'instal·lació per a Render
├── Procfile          ← Comanda d'inici per a Render
└── render.yaml       ← Configuració automàtica de Render
```

---

## 🚀 Passos per pujar a Render

### 1. Crea un repositori a GitHub

1. Ves a [github.com](https://github.com) i inicia sessió
2. Clica **New repository**
3. Posa-li un nom (ex: `spotify-mp3`)
4. Deixa-ho en **Public** i clica **Create repository**

### 2. Puja els fitxers

Tens dues opcions:

**Opció A — Des del navegador (més fàcil):**
1. A la pàgina del repositori, clica **Add file → Upload files**
2. Arrossega tots els fitxers d'aquesta carpeta
3. Clica **Commit changes**
4. Repeteix el pas per crear la carpeta `templates/` i pujar `index.html`

**Opció B — Des de la terminal:**
```bash
cd spotify-web
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/EL_TEU_USUARI/spotify-mp3.git
git push -u origin main
```

### 3. Connecta a Render

1. Ves a [render.com](https://render.com) i crea un compte (gratis)
2. Clica **New → Web Service**
3. Connecta el teu compte de GitHub quan et demani
4. Selecciona el repositori `spotify-mp3`
5. Render detectarà el `render.yaml` automàticament

### 4. Configura el servei

Si no detecta el `render.yaml`, configura manualment:

| Camp | Valor |
|------|-------|
| **Name** | spotify-mp3 |
| **Environment** | Python 3 |
| **Build Command** | `./build.sh` |
| **Start Command** | `gunicorn app:app --workers 2 --threads 4 --timeout 300 --bind 0.0.0.0:$PORT` |
| **Plan** | Free |

### 5. Desplega

1. Clica **Create Web Service**
2. Espera 3-5 minuts mentre s'instal·la tot
3. Render et donarà una URL tipus: `https://spotify-mp3.onrender.com`

---

## ⚠️ Limitacions del pla gratuït de Render

- El servidor **s'adorm** després de 15 minuts d'inactivitat
- La primera petició pot trigar **30-60 segons** (desperta el servidor)
- **750 hores/mes** gratuïtes (suficient per ús personal)
- Els fitxers descarregats s'emmagatzemen a `/tmp` i **s'esborren** quan el servidor es reinicia

---

## 🔧 Ús local (sense Render)

```bash
# Instal·lar dependències
pip install -r requirements.txt
python -m spotdl --download-ffmpeg

# Iniciar el servidor
python app.py

# Obre el navegador a:
# http://localhost:5000
```

---

## 📝 Notes

- Les descàrregues provenen de **YouTube Music** (no directament de Spotify)
- La qualitat màxima disponible depèn de YouTube, no de Spotify
- Algunes cançons exclusives de Spotify poden no estar disponibles

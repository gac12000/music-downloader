import os, uuid, threading, shutil, json, sys, time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

DOWNLOAD_DIR = Path("/tmp/downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Estat en memòria (únic worker, no cal fitxer)
jobs = {}
jobs_lock = threading.Lock()

SERVER_START = time.time()  # Per detectar reinicis


def get_spotdl_cmd():
    if shutil.which("spotdl"):
        return ["spotdl"]
    return [sys.executable, "-m", "spotdl"]


def find_ffmpeg():
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    candidates = [
        Path.home() / ".spotdl" / "ffmpeg",
        Path("/opt/render/project/src/.spotdl/ffmpeg"),
        Path("/root/.spotdl/ffmpeg"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    # Cerca recursiva
    try:
        import subprocess
        r = subprocess.run(["find", str(Path.home()), "-name", "ffmpeg", "-type", "f"],
                           capture_output=True, text=True, timeout=5)
        lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
        if lines:
            return lines[0]
    except Exception:
        pass
    return None


def run_download(job_id, url, fmt, bitrate):
    import subprocess
    job_dir = DOWNLOAD_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    def log(msg):
        with jobs_lock:
            if job_id in jobs:
                jobs[job_id]["log"].append(msg)

    def set_status(s):
        with jobs_lock:
            if job_id in jobs:
                jobs[job_id]["status"] = s

    log(f"Python: {sys.executable}")
    ffmpeg = find_ffmpeg()
    log(f"ffmpeg: {ffmpeg or 'NO TROBAT — intentant descarregar...'}")

    if not ffmpeg:
        try:
            r = subprocess.run(
                [sys.executable, "-m", "spotdl", "--download-ffmpeg"],
                input="y\n", capture_output=True, text=True, timeout=120
            )
            ffmpeg = find_ffmpeg()
            log(f"ffmpeg després de descàrrega: {ffmpeg or 'ENCARA NO TROBAT'}")
            if r.stderr:
                log(f"stderr: {r.stderr[-200:]}")
        except Exception as e:
            log(f"Error descarregant ffmpeg: {e}")

    cmd = get_spotdl_cmd() + [url, "--output", str(job_dir),
                               "--format", fmt, "--bitrate", bitrate, "--threads", "2"]
    if ffmpeg:
        cmd += ["--ffmpeg", ffmpeg]

    log(f"CMD: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, bufsize=1)
        for line in process.stdout:
            line = line.strip()
            if line:
                log(line)
        process.wait()
        log(f"Exit code: {process.returncode}")

        files = list(job_dir.glob(f"*.{fmt}"))
        with jobs_lock:
            jobs[job_id]["files"] = [f.name for f in files]
            if files:
                jobs[job_id]["status"] = "done"
            else:
                jobs[job_id]["status"] = "error"
                jobs[job_id]["error"] = "No s'han creat fitxers. Mira el log."
    except Exception as e:
        log(f"Excepció: {e}")
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ping")
def ping():
    return jsonify({"start": SERVER_START})


@app.route("/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    fmt = data.get("format", "mp3")
    bitrate = data.get("bitrate", "320k")
    if "spotify.com" not in url:
        return jsonify({"error": "URL no vàlida"}), 400
    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {"status": "running", "log": [], "files": [], "error": None}
    t = threading.Thread(target=run_download, args=(job_id, url, fmt, bitrate), daemon=True)
    t.start()
    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job no trobat (potser el servidor s'ha reiniciat)"}), 404
    return jsonify(job)


@app.route("/file/<job_id>/<filename>")
def download_file(job_id, filename):
    path = DOWNLOAD_DIR / job_id / filename
    if not path.exists():
        return "Fitxer no trobat", 404
    return send_file(path, as_attachment=True)


@app.route("/cleanup/<job_id>", methods=["DELETE"])
def cleanup(job_id):
    job_dir = DOWNLOAD_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir)
    with jobs_lock:
        jobs.pop(job_id, None)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

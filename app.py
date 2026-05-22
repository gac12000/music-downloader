import os
import uuid
import threading
import shutil
import json
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

DOWNLOAD_DIR = Path("/tmp/downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
JOBS_DIR = Path("/tmp/jobs")
JOBS_DIR.mkdir(exist_ok=True)


def job_path(job_id):
    return JOBS_DIR / f"{job_id}.json"

def read_job(job_id):
    p = job_path(job_id)
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)

def write_job(job_id, data):
    with open(job_path(job_id), "w") as f:
        json.dump(data, f)

def find_ffmpeg():
    """Busca ffmpeg a totes les rutes possibles."""
    # 1. PATH normal
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    # 2. Rutes on spotdl el descarrega
    candidates = [
        Path.home() / ".spotdl" / "ffmpeg",
        Path.home() / ".spotdl" / "ffmpeg.exe",
        Path("/opt/render/project/src/.spotdl/ffmpeg"),
        Path("/opt/render/project/.spotdl/ffmpeg"),
        Path("/root/.spotdl/ffmpeg"),
        Path("/home/render/.spotdl/ffmpeg"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    # 3. Busca recursivament a home
    try:
        import subprocess
        result = subprocess.run(["find", str(Path.home()), "-name", "ffmpeg", "-type", "f"],
                                capture_output=True, text=True, timeout=5)
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        if lines:
            return lines[0]
    except Exception:
        pass
    return None

def get_spotdl_cmd():
    if shutil.which("spotdl"):
        return ["spotdl"]
    return [sys.executable, "-m", "spotdl"]

def run_download(job_id, url, fmt, bitrate):
    import subprocess
    job_dir = DOWNLOAD_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    job = {"status": "running", "log": [], "files": [], "error": None}
    write_job(job_id, job)

    def log(msg):
        job["log"].append(msg)
        write_job(job_id, job)

    # Diagnosi: mostra info d'entorn
    log(f"Python: {sys.executable}")
    log(f"Home: {Path.home()}")

    ffmpeg = find_ffmpeg()
    log(f"ffmpeg: {ffmpeg or 'NO TROBAT'}")

    if not ffmpeg:
        # Intenta descarregar-lo ara
        log("Intentant descarregar ffmpeg...")
        try:
            import subprocess as sp
            r = sp.run([sys.executable, "-m", "spotdl", "--download-ffmpeg"],
                       input="y\n", capture_output=True, text=True, timeout=120)
            log(r.stdout[-300:] if r.stdout else "")
            log(r.stderr[-300:] if r.stderr else "")
            ffmpeg = find_ffmpeg()
            log(f"ffmpeg després de descàrrega: {ffmpeg or 'ENCARA NO TROBAT'}")
        except Exception as e:
            log(f"Error descarregant ffmpeg: {e}")

    cmd = get_spotdl_cmd() + [
        url,
        "--output", str(job_dir),
        "--format", fmt,
        "--bitrate", bitrate,
        "--threads", "2",
    ]
    if ffmpeg:
        cmd += ["--ffmpeg", ffmpeg]

    log(f"Executant: {' '.join(cmd)}")

    try:
        import subprocess as sp
        process = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            line = line.strip()
            if line:
                log(line)
        process.wait()
        log(f"Codi de sortida: {process.returncode}")

        files = list(job_dir.glob(f"*.{fmt}"))
        job["files"] = [f.name for f in files]
        job["status"] = "done" if files else "error"
        if not files:
            job["error"] = "No s'han trobat fitxers. Mira el log per més detalls."
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        log(f"Excepció: {e}")

    write_job(job_id, job)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    fmt = data.get("format", "mp3")
    bitrate = data.get("bitrate", "320k")
    if "spotify.com" not in url:
        return jsonify({"error": "URL no vàlida"}), 400
    job_id = str(uuid.uuid4())
    t = threading.Thread(target=run_download, args=(job_id, url, fmt, bitrate), daemon=True)
    t.start()
    return jsonify({"job_id": job_id})

@app.route("/status/<job_id>")
def status(job_id):
    job = read_job(job_id)
    if not job:
        return jsonify({"error": "Job no trobat"}), 404
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
    p = job_path(job_id)
    if p.exists():
        p.unlink()
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


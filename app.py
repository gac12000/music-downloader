import os
import uuid
import threading
import shutil
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import sys

app = Flask(__name__)

DOWNLOAD_DIR = Path("/tmp/downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Store job status in memory
jobs = {}

def run_download(job_id, url, fmt="mp3", bitrate="320k"):
    job_dir = DOWNLOAD_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    jobs[job_id] = {"status": "running", "log": [], "files": [], "error": None}

    spotdl_cmd = [sys.executable, "-m", "spotdl", url,
                  "--output", str(job_dir),
                  "--format", fmt,
                  "--bitrate", bitrate,
                  "--threads", "4"]

    try:
        process = subprocess.Popen(
            spotdl_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in process.stdout:
            line = line.strip()
            if line:
                jobs[job_id]["log"].append(line)
        process.wait()

        files = list(job_dir.glob(f"*.{fmt}"))
        jobs[job_id]["files"] = [f.name for f in files]
        jobs[job_id]["status"] = "done" if files else "error"
        if not files:
            jobs[job_id]["error"] = "No s'han trobat fitxers descarregats."
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


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
    job = jobs.get(job_id)
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
    jobs.pop(job_id, None)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

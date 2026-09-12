#!/usr/bin/env python3
"""
Facebook Auto Commenter - Web App
Flask backend dengan SSE untuk streaming log real-time
"""

import os
import uuid
import time
import queue
import threading
import asyncio
from flask import Flask, render_template, request, jsonify, Response
from worker import run_job

app = Flask(__name__)

# Job storage (in-memory)
JOBS = {}
JOB_LOGS = {}
JOBS_LOCK = threading.Lock()


def create_log_callback(job_id):
    def callback(msg):
        with JOBS_LOCK:
            if job_id in JOB_LOGS:
                JOB_LOGS[job_id].put(str(msg))
    return callback


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def start_job():
    """Mulai job baru."""
    try:
        config = request.get_json(force=True)
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {e}"}), 400

    target = config.get("target_username", "").strip().lstrip("@")
    accounts = config.get("accounts", [])

    if not target:
        return jsonify({"error": "Target username wajib diisi"}), 400

    valid_accounts = [
        a for a in accounts
        if a.get("c_user", "").strip() and a.get("xs", "").strip()
    ]
    if not valid_accounts:
        return jsonify({"error": "Minimal 1 akun dengan c_user & xs"}), 400

    job_id = str(uuid.uuid4())[:8]

    with JOBS_LOCK:
        JOBS[job_id] = {
            "status": "running",
            "started_at": time.time(),
            "finished_at": None,
            "config": config,
            "result": None,
            "error": None,
        }
        JOB_LOGS[job_id] = queue.Queue()

    log_cb = create_log_callback(job_id)

    def run_job_in_thread():
        try:
            result = asyncio.run(run_job(config, log_cb))
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "done"
                JOBS[job_id]["result"] = result
                JOBS[job_id]["finished_at"] = time.time()
        except Exception as e:
            import traceback
            err = f"{type(e).__name__}: {e}"
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "error"
                JOBS[job_id]["error"] = err
                JOBS[job_id]["finished_at"] = time.time()
            log_cb(f"\n❌ ERROR: {err}")
            log_cb(traceback.format_exc())
        finally:
            log_cb("__END__")

    threading.Thread(target=run_job_in_thread, daemon=True).start()

    return jsonify({"job_id": job_id})


@app.route("/api/logs/<job_id>")
def stream_logs(job_id):
    """Server-Sent Events untuk streaming log."""
    def generate():
        with JOBS_LOCK:
            q = JOB_LOGS.get(job_id)

        if not q:
            yield f"data: Job {job_id} tidak ditemukan\n\n"
            yield "data: __END__\n\n"
            return

        while True:
            try:
                msg = q.get(timeout=30)
                if msg == "__END__":
                    yield "data: __END__\n\n"
                    break
                safe = msg.replace("\r", "").replace("\n", "\\n")
                yield f"data: {safe}\n\n"
            except queue.Empty:
                yield ": keepalive\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/api/status/<job_id>")
def job_status(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404

    return jsonify({
        "status": job["status"],
        "started_at": job["started_at"],
        "finished_at": job["finished_at"],
        "result": job["result"],
        "error": job["error"],
    })


@app.route("/health")
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
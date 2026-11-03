import io
import logging
import os
import secrets
import sqlite3
import tempfile
import threading
import time
import uuid
from contextlib import closing
from pathlib import Path
from hmac import compare_digest

from flask import Flask, jsonify, render_template, request, send_file
from flask import redirect, session, url_for
from dotenv import load_dotenv

from export_excel import export_issues_to_excel
from pipeline import process_feedback


load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["SECRET_KEY"] = os.environ.get("TAKT_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("TAKT_COOKIE_SECURE", "false").lower() == "true"
)
logger = logging.getLogger(__name__)
jobs = {}
jobs_lock = threading.Lock()
login_attempts = {}
login_attempts_lock = threading.Lock()
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 15 * 60


def _csrf_token():
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.before_request
def require_login_and_csrf():
    if request.endpoint in {"login", "health_check", "static"}:
        return None

    if not os.environ.get("TAKT_APP_PASSWORD"):
        if request.path.startswith("/api/"):
            return jsonify(error="The app password is not configured on the server."), 503
        return "The app password is not configured on the server.", 503

    if not session.get("authenticated"):
        if request.path.startswith("/api/"):
            return jsonify(error="Please log in to continue."), 401
        return redirect(url_for("login"))

    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        expected_token = session.get("csrf_token", "")
        supplied_token = request.headers.get("X-CSRF-Token", "")
        if not expected_token or not compare_digest(expected_token, supplied_token):
            return jsonify(error="The session expired. Refresh the page and try again."), 400
    return None


def _login_rate_limited(remote_address):
    now = time.monotonic()
    with login_attempts_lock:
        attempts = [
            timestamp
            for timestamp in login_attempts.get(remote_address, [])
            if now - timestamp < LOGIN_WINDOW_SECONDS
        ]
        login_attempts[remote_address] = attempts
        return len(attempts) >= LOGIN_MAX_ATTEMPTS


def _record_failed_login(remote_address):
    now = time.monotonic()
    with login_attempts_lock:
        attempts = [
            timestamp
            for timestamp in login_attempts.get(remote_address, [])
            if now - timestamp < LOGIN_WINDOW_SECONDS
        ]
        attempts.append(now)
        login_attempts[remote_address] = attempts


@app.get("/healthz")
def health_check():
    return jsonify(status="ok")


@app.route("/login", methods=["GET", "POST"])
def login():
    configured_password = os.environ.get("TAKT_APP_PASSWORD")
    if not configured_password:
        return render_template(
            "login.html",
            error="מנהל האתר צריך להגדיר סיסמת גישה לפני השימוש.",
            csrf_token=_csrf_token(),
        ), 503

    if request.method == "GET":
        return render_template("login.html", error=None, csrf_token=_csrf_token())

    if _login_rate_limited(request.remote_addr or ""):
        return render_template(
            "login.html",
            error="נרשמו יותר מדי ניסיונות. יש להמתין 15 דקות ולנסות שוב.",
            csrf_token=_csrf_token(),
        ), 429

    supplied_token = request.form.get("csrf_token", "")
    expected_token = session.get("csrf_token", "")
    supplied_password = request.form.get("password", "")
    if (
        not expected_token
        or not compare_digest(expected_token, supplied_token)
        or not compare_digest(configured_password, supplied_password)
    ):
        _record_failed_login(request.remote_addr or "")
        return render_template(
            "login.html",
            error="הסיסמה שגויה. נסו שוב.",
            csrf_token=_csrf_token(),
        ), 401

    session.clear()
    session["authenticated"] = True
    session["csrf_token"] = secrets.token_urlsafe(32)
    return redirect(url_for("index"))


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def _feedback_from_uploads(uploaded_files):
    feedback = []
    with tempfile.TemporaryDirectory(prefix="takt-upload-") as temp_dir:
        for index, uploaded_file in enumerate(uploaded_files):
            original_name = Path(uploaded_file.filename or "").name
            suffix = Path(original_name).suffix.lower()
            if suffix not in {".db", ".sqlite", ".sqlite3"}:
                raise ValueError(
                    f"Unsupported file type for {original_name or 'upload'}. "
                    "Upload a .db, .sqlite, or .sqlite3 file."
                )

            temporary_path = Path(temp_dir) / f"database_{index}{suffix}"
            temporary_path.write_bytes(uploaded_file.read())
            database_uri = temporary_path.resolve().as_uri() + "?mode=ro"

            try:
                with closing(sqlite3.connect(database_uri, uri=True)) as connection:
                    rows = connection.execute(
                        """
                        SELECT Comments
                        FROM TrainingFeedback
                        WHERE Comments IS NOT NULL
                          AND TRIM(Comments) != '';
                        """
                    ).fetchall()
            except sqlite3.Error as error:
                raise ValueError(
                    f"Could not read {original_name}: {error}"
                ) from error

            feedback.extend(
                {"source_file": original_name, "comment": row[0]}
                for row in rows
            )
    return feedback


def _run_job(job_id, feedback):
    def update_stage(message):
        with jobs_lock:
            jobs[job_id]["stage"] = message

    try:
        issues = process_feedback(feedback, progress_callback=update_stage)
        workbook_buffer = io.BytesIO()
        export_issues_to_excel(issues, output_path=workbook_buffer)
        workbook_buffer.seek(0)
        with jobs_lock:
            jobs[job_id].update(
                status="completed",
                stage="הדוח מוכן להורדה",
                report=workbook_buffer.getvalue(),
            )
    except Exception as error:
        logger.exception("Feedback processing job %s failed", job_id)
        with jobs_lock:
            jobs[job_id].update(
                status="failed",
                stage="העיבוד נכשל",
                error=str(error),
            )


@app.get("/")
def index():
    return render_template("index.html", csrf_token=_csrf_token())


@app.post("/api/jobs")
def create_job():
    pasted_text = request.form.get("feedback", "")
    feedback = [
        line.strip()
        for line in pasted_text.splitlines()
        if line.strip()
    ]

    uploaded_files = [
        uploaded_file
        for uploaded_file in request.files.getlist("databases")
        if uploaded_file.filename
    ]
    try:
        feedback.extend(_feedback_from_uploads(uploaded_files))
    except ValueError as error:
        return jsonify(error=str(error)), 400

    if not feedback:
        return jsonify(
            error="הדבק/י משובים או בחר/י קובץ מסד נתונים כדי להתחיל."
        ), 400

    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {
            "status": "running",
            "stage": "המשימה מתחילה",
            "error": None,
            "report": None,
        }

    threading.Thread(
        target=_run_job,
        args=(job_id, feedback),
        daemon=True,
    ).start()
    return jsonify(job_id=job_id), 202


@app.get("/api/jobs/<job_id>")
def get_job(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            return jsonify(error="המשימה לא נמצאה או שפג תוקפה."), 404
        return jsonify(
            status=job["status"],
            stage=job["stage"],
            error=job["error"],
        )


@app.get("/api/jobs/<job_id>/report")
def download_report(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None or job["status"] != "completed" or job["report"] is None:
            return jsonify(error="הדוח עדיין אינו זמין."), 404
        report = job["report"]

    response = send_file(
        io.BytesIO(report),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="דוח_בעיות_טקט.xlsx",
    )

    def remove_job():
        with jobs_lock:
            jobs.pop(job_id, None)

    response.call_on_close(remove_job)
    return response


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify(error="הקובץ גדול מדי. הגודל המרבי לבקשה הוא 16MB."), 413


if __name__ == "__main__":
    app.run(
        host=os.environ.get("TAKT_HOST", "127.0.0.1"),
        port=int(os.environ.get("TAKT_PORT", "5000")),
        debug=False,
    )

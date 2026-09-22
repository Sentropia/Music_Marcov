"""Flask entry point for the Markov Music Generator web app."""

from __future__ import annotations

from io import BytesIO
import os

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge

from music_generator import (
    AudioSynthesisError,
    MAX_ORDER,
    MIN_ORDER,
    generate_mp3_bytes,
    load_model,
)


def create_app() -> Flask:
    """Create the HTTP application used by Gunicorn and local development."""
    application = Flask(__name__)
    # The API accepts a tiny JSON object, not uploaded audio or model files.
    application.config["MAX_CONTENT_LENGTH"] = 16 * 1024

    @application.errorhandler(RequestEntityTooLarge)
    def request_too_large(_: RequestEntityTooLarge):
        return jsonify(error="Request body is too large."), 413

    @application.get("/")
    def index():
        return render_template("index.html", min_order=MIN_ORDER, max_order=MAX_ORDER)

    @application.get("/healthz")
    def healthz():
        try:
            load_model()
        except Exception:
            application.logger.exception("Health check could not load the Markov model")
            return jsonify(status="unavailable"), 503
        return jsonify(status="ok")

    @application.post("/api/generate")
    def generate():
        if not request.is_json:
            return jsonify(error="Request body must be a JSON object."), 400

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Request body must be a JSON object."), 400

        try:
            audio_data = generate_mp3_bytes(payload.get("order"))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except AudioSynthesisError:
            application.logger.exception("MP3 rendering failed")
            return jsonify(error="Audio rendering is temporarily unavailable. Please try again."), 503
        except Exception:
            application.logger.exception("Music generation failed")
            return jsonify(error="Music generation failed. Please try again."), 500

        response = send_file(
            BytesIO(audio_data),
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="markov_music.mp3",
            max_age=0,
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    return application


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)

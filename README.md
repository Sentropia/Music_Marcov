# Markov Music Generator

A Flask web application that generates downloadable piano MIDI files with the bundled Markov model. The application keeps the model in memory and returns each MIDI file directly to the browser; it does not create a shared `generated_music.mid` file.

## Local development

This project targets Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app webapp run --debug
```

Open `http://127.0.0.1:5000`, select an order from 3 through 9, and download the generated MIDI file.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Render deployment

The repository includes `render.yaml`. Create a Render Blueprint from this repository, or create a Python Web Service with:

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn --bind 0.0.0.0:$PORT webapp:app`
- **Health check path:** `/healthz`

`markov_model.pkl` must remain present in the deployed repository because it is loaded by `music_generator.py`. No desktop application, MuseScore installation, persistent disk, or generated-file storage is required.

## API

- `GET /` — web interface.
- `GET /healthz` — loads/checks the bundled model and returns `{"status": "ok"}`; it returns HTTP 503 if the model cannot be loaded.
- `POST /api/generate` — accepts a JSON object such as `{"order": 5}` and returns an `audio/midi` attachment. Missing, malformed, or out-of-range orders receive HTTP 400.

The model artifact is a trusted local pickle. Do not accept model pickle uploads from users.

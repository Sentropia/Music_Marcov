# Markov Music Generator

A Flask web application that generates piano music from the bundled Markov model
and returns an MP3 that plays directly in modern browsers. The model is cached
in each server process; generated MIDI and MP3 data stay in memory per request.

## Local development

The supported local path uses Docker because FluidSynth and its SoundFont are
system-level audio dependencies:

```bash
docker build -t markov-music .
docker run --rm -p 10000:10000 -e PORT=10000 markov-music
```

Open `http://127.0.0.1:10000`, select an order from 3 through 9, generate music,
then play it on the page or download the MP3.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Render deployment

The repository includes `render.yaml`, which deploys the included Dockerfile as
a Render Blueprint. The Docker image installs the FluidSynth shared library and
Ubuntu's `fluid-soundfont-gm` package, then starts Gunicorn. No Render dashboard
package configuration, persistent disk, MuseScore, or desktop software is
required.

After deployment, verify `GET /healthz` returns `{"status":"ok"}` and generate
an MP3 from the browser. `markov_model.pkl` must remain present in the deployed
repository because `music_generator.py` loads it as a trusted local artifact.

## API

- `GET /` — web interface.
- `GET /healthz` — loads/checks the bundled model and returns `{"status": "ok"}`;
  it returns HTTP 503 if the model cannot be loaded.
- `POST /api/generate` — accepts `{"order": 3..9}` and returns a downloadable
  `audio/mpeg` attachment. The frontend uses the same in-memory response for its
  HTML5 player and MP3 download link. Invalid requests return HTTP 400; an
  unavailable audio renderer returns HTTP 503.

See `THIRD_PARTY_NOTICES.md` for the runtime SoundFont notice. Do not accept
model pickle uploads from users.

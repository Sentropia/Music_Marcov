FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        fluidsynth \
        fluid-soundfont-gm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV SOUNDFONT_PATH=/usr/share/sounds/sf2/FluidR3_GM.sf2

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT webapp:app"]


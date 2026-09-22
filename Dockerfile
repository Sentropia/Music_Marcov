FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SOUNDFONT_PATH=/usr/share/sounds/sf2/FluidR3_GM.sf2

RUN apt-get update \
    && apt-get install --no-install-recommends -y libfluidsynth3 fluid-soundfont-gm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./

CMD gunicorn --bind 0.0.0.0:${PORT:-10000} webapp:app

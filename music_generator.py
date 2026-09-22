"""Markov-model MIDI generation for the web application."""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import pickle
import random

import pretty_midi


PROJECT_DIR = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_DIR / "markov_model.pkl"

NUMBER_OF_STATES = 240
MIN_PITCH = 48
MAX_PITCH = 84
START_PITCH = 60
MIN_ORDER = 3
MAX_ORDER = 9
MIN_VELOCITY = 105
MAX_VELOCITY = 125
TEMPO_BPM = 100


@lru_cache(maxsize=1)
def load_model() -> dict:
    """Load the trusted, repository-bundled Markov model once per process."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Markov model not found: {MODEL_PATH}")

    with MODEL_PATH.open("rb") as model_file:
        model = pickle.load(model_file)

    if not isinstance(model, dict):
        raise TypeError("markov_model.pkl has an unexpected format.")
    return model


def validate_order(order: object) -> int:
    """Return a valid requested order or raise ValueError for invalid input."""
    if isinstance(order, bool):
        raise ValueError("order must be an integer between 3 and 9.")
    if isinstance(order, float) and not order.is_integer():
        raise ValueError("order must be an integer between 3 and 9.")
    try:
        parsed_order = int(order)
    except (TypeError, ValueError) as exc:
        raise ValueError("order must be an integer between 3 and 9.") from exc

    if parsed_order < MIN_ORDER or parsed_order > MAX_ORDER:
        raise ValueError(f"order must be between {MIN_ORDER} and {MAX_ORDER}.")
    return parsed_order


def available_orders(model: dict) -> list[int]:
    orders = []
    for key in model:
        try:
            orders.append(int(key))
        except (TypeError, ValueError):
            continue
    return sorted(set(orders))


def get_candidates(model: dict, history: list, order: int) -> Counter:
    if order <= 0 or len(history) < order:
        return Counter()
    table = model.get(order)
    if table is None:
        return Counter()
    return table.get(tuple(history[-order:]), Counter())


def get_backoff_candidates(model: dict, history: list, start_order: int) -> tuple[Counter, int]:
    orders = available_orders(model)
    if not orders:
        return Counter(), 0

    highest_order = min(start_order, max(orders), MAX_ORDER)
    for order in range(highest_order, MIN_ORDER - 1, -1):
        candidates = get_candidates(model, history, order)
        if candidates:
            return candidates, order

    # Preserve the original safety fallback when no order 3..9 context exists.
    order_one = model.get(1)
    if order_one:
        candidates = Counter()
        for transitions in order_one.values():
            candidates.update(transitions)
        if candidates:
            return candidates, 1
    return Counter(), 0


def choose_initial_state(model: dict, rng: random.Random):
    order_one = model.get(1)
    if not order_one:
        raise RuntimeError("Order-1 model is empty.")

    candidates = Counter()
    for transitions in order_one.values():
        candidates.update(transitions)
    if not candidates:
        raise RuntimeError("No initial states available.")

    return rng.choices(list(candidates), weights=list(candidates.values()), k=1)[0]


def choose_next_state(model: dict, history: list, current_pitch: float, generation_order: int, rng: random.Random):
    candidates, used_order = get_backoff_candidates(model, history, generation_order)
    if not candidates:
        raise RuntimeError("No Markov transition candidates found.")

    valid_states = []
    valid_weights = []
    for state, weight in candidates.items():
        try:
            interval = float(state[0])
        except (TypeError, ValueError, IndexError):
            continue
        if MIN_PITCH <= current_pitch + interval <= MAX_PITCH:
            valid_states.append(state)
            valid_weights.append(float(weight))

    if not valid_states:
        for state, weight in candidates.items():
            try:
                numeric_weight = float(weight)
            except (TypeError, ValueError):
                continue
            if numeric_weight > 0:
                valid_states.append(state)
                valid_weights.append(numeric_weight)
    if not valid_states:
        raise RuntimeError("No valid next states available.")

    return rng.choices(valid_states, weights=valid_weights, k=1)[0], used_order


def generate_states(model: dict, generation_order: int, rng: random.Random | None = None) -> tuple[list, Counter]:
    """Generate states using the original weighted Markov/backoff strategy."""
    rng = rng or random.Random()
    first_state = choose_initial_state(model, rng)
    states = [first_state]
    history = [first_state]
    current_pitch = START_PITCH
    order_usage = Counter()

    for _ in range(NUMBER_OF_STATES - 1):
        state, used_order = choose_next_state(model, history, current_pitch, generation_order, rng)
        states.append(state)
        order_usage[used_order] += 1
        current_pitch = max(MIN_PITCH, min(MAX_PITCH, current_pitch + float(state[0])))
        history.append(state)
        if len(history) > generation_order + 24:
            history.pop(0)
    return states, order_usage


def states_to_midi(states: list, tempo_bpm: float, rng: random.Random) -> pretty_midi.PrettyMIDI:
    midi = pretty_midi.PrettyMIDI(initial_tempo=float(tempo_bpm))
    piano_program = pretty_midi.instrument_name_to_program("Acoustic Grand Piano")
    instrument = pretty_midi.Instrument(program=piano_program)
    current_pitch = START_PITCH
    current_time = 0.0

    for state in states:
        try:
            interval, rhythm = float(state[0]), float(state[1])
        except (TypeError, ValueError, IndexError):
            continue

        current_pitch = int(round(max(MIN_PITCH, min(MAX_PITCH, current_pitch + interval))))
        gap = max(rhythm, 0.25)
        duration = min(max(gap * 0.90, 0.08), 2.5)
        instrument.notes.append(
            pretty_midi.Note(
                velocity=rng.randint(MIN_VELOCITY, MAX_VELOCITY),
                pitch=current_pitch,
                start=current_time,
                end=current_time + duration,
            )
        )
        current_time += gap

    midi.instruments.append(instrument)
    return midi


def generate_midi_bytes(order: object, seed: int | None = None) -> bytes:
    """Generate a downloadable MIDI file entirely in memory."""
    generation_order = validate_order(order)
    model = load_model()
    if not available_orders(model):
        raise RuntimeError("The Markov model contains no orders.")

    rng = random.Random(seed)
    states, _ = generate_states(model, generation_order, rng)
    midi = states_to_midi(states, TEMPO_BPM, rng)
    output = BytesIO()
    midi.write(output)
    return output.getvalue()

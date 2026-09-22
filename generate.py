from pathlib import Path
from collections import Counter
import pickle
import random
import subprocess
import sys

import pretty_midi


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path.home() / "Desktop" / "project"

MODEL_CACHE = PROJECT_DIR / "markov_model.pkl"
MIDI_PATH = PROJECT_DIR / "generated_music.mid"

MUSESCORE_COMMAND = (
    Path.home()
    / "Downloads"
    / "MuseScore-Studio-4.7.4.260706075-x86_64.AppImage"
)


# ============================================================
# GENERATION SETTINGS
# ============================================================

NUMBER_OF_STATES = 240

MIN_PITCH = 48
MAX_PITCH = 84

START_PITCH = 60

MIN_ORDER = 3
MAX_ORDER = 9

# ------------------------------------------------------------
# MIDI dynamics
#
# MIDI velocity:
# 1   = very quiet
# 127 = maximum
#
# We deliberately use a high range so the generated
# piano sounds louder and clearer in MuseScore.
# ------------------------------------------------------------

MIN_VELOCITY = 105
MAX_VELOCITY = 125

TEMPO_BPM = 100


# ============================================================
# LOAD MARKOV MODEL
# ============================================================

def load_model():

    if not MODEL_CACHE.exists():

        raise FileNotFoundError(
            f"\nMarkov model not found:\n"
            f"{MODEL_CACHE}\n\n"
            f"Expected file:\n"
            f"markov_model.pkl"
        )

    try:

        with open(
            MODEL_CACHE,
            "rb"
        ) as file:

            model = pickle.load(file)

    except Exception as exc:

        raise RuntimeError(
            f"Could not load Markov model:\n{exc}"
        )

    if not isinstance(
        model,
        dict
    ):

        raise TypeError(
            "markov_model.pkl has an unexpected format."
        )

    return model


# ============================================================
# AVAILABLE ORDERS
# ============================================================

def available_orders(model):

    orders = []

    for key in model.keys():

        try:

            value = int(key)

        except (
            TypeError,
            ValueError
        ):

            continue

        orders.append(value)

    return sorted(
        set(orders)
    )


# ============================================================
# GET CANDIDATES
# ============================================================

def get_candidates(
    model,
    history,
    order
):

    if order <= 0:
        return Counter()

    if len(history) < order:
        return Counter()

    table = model.get(
        order
    )

    if table is None:
        return Counter()

    context = tuple(
        history[-order:]
    )

    transitions = table.get(
        context
    )

    if not transitions:
        return Counter()

    return transitions


# ============================================================
# BACKOFF
# ============================================================

def get_backoff_candidates(
    model,
    history,
    start_order
):

    orders = available_orders(
        model
    )

    if not orders:
        return Counter(), 0

    highest_available = max(
        orders
    )

    highest_order = min(
        start_order,
        highest_available,
        MAX_ORDER
    )

    # --------------------------------------------------------
    # Main search:
    #
    # 9 -> 8 -> 7 -> ... -> 3
    #
    # We deliberately keep the main Backoff floor at 3.
    # --------------------------------------------------------

    for order in range(
        highest_order,
        MIN_ORDER - 1,
        -1
    ):

        candidates = get_candidates(
            model,
            history,
            order
        )

        if candidates:

            return (
                candidates,
                order
            )

    # --------------------------------------------------------
    # Safety fallback:
    #
    # If nothing exists from Order 3 down,
    # use Order 1 only to prevent generation failure.
    # --------------------------------------------------------

    order_one = model.get(
        1
    )

    if order_one:

        candidates = Counter()

        for transitions in (
            order_one.values()
        ):

            for state, count in (
                transitions.items()
            ):

                candidates[state] += count

        if candidates:

            return (
                candidates,
                1
            )

    return (
        Counter(),
        0
    )


# ============================================================
# INITIAL STATE
# ============================================================

def choose_initial_state(
    model
):

    order_one = model.get(
        1
    )

    if not order_one:

        raise RuntimeError(
            "Order-1 model is empty."
        )

    candidates = Counter()

    for transitions in (
        order_one.values()
    ):

        for state, count in (
            transitions.items()
        ):

            candidates[state] += count

    if not candidates:

        raise RuntimeError(
            "No initial states available."
        )

    states = list(
        candidates.keys()
    )

    weights = list(
        candidates.values()
    )

    return random.choices(
        states,
        weights=weights,
        k=1
    )[0]


# ============================================================
# NEXT STATE
# ============================================================

def choose_next_state(
    model,
    history,
    current_pitch,
    generation_order
):

    candidates, used_order = (
        get_backoff_candidates(
            model,
            history,
            generation_order
        )
    )

    if not candidates:

        raise RuntimeError(
            "No Markov transition candidates found."
        )

    valid_states = []
    valid_weights = []

    # --------------------------------------------------------
    # First pass:
    # respect pitch range
    # --------------------------------------------------------

    for state, weight in (
        candidates.items()
    ):

        try:

            interval = float(
                state[0]
            )

        except (
            TypeError,
            ValueError,
            IndexError
        ):

            continue

        next_pitch = (
            current_pitch
            + interval
        )

        if not (
            MIN_PITCH
            <= next_pitch
            <= MAX_PITCH
        ):

            continue

        valid_states.append(
            state
        )

        valid_weights.append(
            float(weight)
        )

    # --------------------------------------------------------
    # Second pass:
    # if pitch filtering removed everything,
    # use the original candidates.
    # --------------------------------------------------------

    if not valid_states:

        for state, weight in (
            candidates.items()
        ):

            try:
                weight = float(
                    weight
                )
            except (
                TypeError,
                ValueError
            ):
                continue

            if weight <= 0:
                continue

            valid_states.append(
                state
            )

            valid_weights.append(
                weight
            )

    if not valid_states:

        raise RuntimeError(
            "No valid next states available."
        )

    selected = random.choices(
        valid_states,
        weights=valid_weights,
        k=1
    )[0]

    return (
        selected,
        used_order
    )


# ============================================================
# GENERATE STATE SEQUENCE
# ============================================================

def generate_states(
    model,
    generation_order
):

    first_state = (
        choose_initial_state(
            model
        )
    )

    states = [
        first_state
    ]

    history = [
        first_state
    ]

    current_pitch = START_PITCH

    order_usage = Counter()

    for _ in range(
        NUMBER_OF_STATES - 1
    ):

        state, used_order = (
            choose_next_state(
                model,
                history,
                current_pitch,
                generation_order
            )
        )

        states.append(
            state
        )

        order_usage[
            used_order
        ] += 1

        interval = float(
            state[0]
        )

        current_pitch += interval

        current_pitch = max(
            MIN_PITCH,
            min(
                MAX_PITCH,
                current_pitch
            )
        )

        history.append(
            state
        )

        # ----------------------------------------------------
        # Keep history bounded.
        # ----------------------------------------------------

        max_history = (
            generation_order + 24
        )

        if len(history) > max_history:

            history.pop(0)

    return (
        states,
        order_usage
    )


# ============================================================
# STATE -> MIDI
# ============================================================

def states_to_midi(
    states,
    tempo_bpm
):

    # --------------------------------------------------------
    # Tempo
    # --------------------------------------------------------

    midi = pretty_midi.PrettyMIDI(
        initial_tempo=float(
            tempo_bpm
        )
    )

    # --------------------------------------------------------
    # Acoustic Grand Piano
    # --------------------------------------------------------

    piano_program = (
        pretty_midi
        .instrument_name_to_program(
            "Acoustic Grand Piano"
        )
    )

    instrument = pretty_midi.Instrument(
        program=piano_program
    )

    current_pitch = START_PITCH
    current_time = 0.0

    # --------------------------------------------------------
    # Create notes
    # --------------------------------------------------------

    for state in states:

        try:

            interval = float(
                state[0]
            )

            rhythm = float(
                state[1]
            )

        except (
            TypeError,
            ValueError,
            IndexError
        ):

            continue

        # ----------------------------------------------------
        # Pitch
        # ----------------------------------------------------

        current_pitch += interval

        current_pitch = int(
            round(
                max(
                    MIN_PITCH,
                    min(
                        MAX_PITCH,
                        current_pitch
                    )
                )
            )
        )

        # ----------------------------------------------------
        # Rhythm
        # ----------------------------------------------------

        gap = max(
            rhythm,
            0.25
        )

        # ----------------------------------------------------
        # Duration
        # ----------------------------------------------------

        duration = min(
            max(
                gap * 0.90,
                0.08
            ),
            2.5
        )

        # ----------------------------------------------------
        # LOUDER MIDI VELOCITY
        # ----------------------------------------------------

        velocity = random.randint(
            MIN_VELOCITY,
            MAX_VELOCITY
        )

        note = pretty_midi.Note(

            velocity=velocity,

            pitch=current_pitch,

            start=current_time,

            end=(
                current_time
                + duration
            )
        )

        instrument.notes.append(
            note
        )

        current_time += gap

    midi.instruments.append(
        instrument
    )

    return midi


# ============================================================
# VERIFY MIDI
# ============================================================

def verify_midi(
    expected_tempo
):

    try:

        check = pretty_midi.PrettyMIDI(
            str(MIDI_PATH)
        )

    except Exception as exc:

        raise RuntimeError(
            f"Could not reopen generated MIDI:\n{exc}"
        )

    _, tempi = (
        check.get_tempo_changes()
    )

    if len(tempi) == 0:

        raise RuntimeError(
            "Generated MIDI contains no tempo information."
        )

    actual_tempo = float(
        tempi[0]
    )

    # --------------------------------------------------------
    # Verify notes
    # --------------------------------------------------------

    total_notes = 0

    for instrument in (
        check.instruments
    ):

        total_notes += len(
            instrument.notes
        )

    if total_notes == 0:

        raise RuntimeError(
            "Generated MIDI contains no notes."
        )

    print()
    print("=" * 65)
    print("MIDI VERIFICATION")
    print("=" * 65)

    print(
        f"Expected BPM : "
        f"{expected_tempo:.2f}"
    )

    print(
        f"Actual BPM   : "
        f"{actual_tempo:.2f}"
    )

    print(
        f"Total notes  : "
        f"{total_notes}"
    )

    print(
        f"Velocity     : "
        f"{MIN_VELOCITY} - {MAX_VELOCITY}"
    )

    print("=" * 65)

    if abs(
        actual_tempo
        - expected_tempo
    ) > 0.01:

        raise RuntimeError(
            "MIDI tempo verification failed."
        )


# ============================================================
# OPEN MUSESCORE
# ============================================================

def open_in_musescore():

    if not MUSESCORE_COMMAND.exists():

        raise FileNotFoundError(
            f"MuseScore executable not found:\n"
            f"{MUSESCORE_COMMAND}"
        )

    try:

        # ----------------------------------------------------
        # ONLY open MuseScore.
        #
        # No xdotool.
        # No wmctrl.
        # No keyboard automation.
        # No remote-control notification.
        # ----------------------------------------------------

        process = subprocess.Popen(

            [
                str(MUSESCORE_COMMAND),
                str(MIDI_PATH)
            ],

            cwd=str(PROJECT_DIR),

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL,

            start_new_session=True
        )

        print(
            f"MuseScore started. PID = "
            f"{process.pid}"
        )

        return True

    except Exception as exc:

        raise RuntimeError(
            f"Could not launch MuseScore:\n{exc}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Interface:
    #
    # python generate.py
    #
    # OR
    #
    # python generate.py 7
    #
    # Default Order = 5
    # --------------------------------------------------------

    if len(sys.argv) > 2:

        print(
            "Usage:"
        )

        print(
            "python generate.py [order]"
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Default
    # --------------------------------------------------------

    generation_order = 5

    # --------------------------------------------------------
    # Optional Order
    # --------------------------------------------------------

    if len(sys.argv) == 2:

        try:

            generation_order = int(
                sys.argv[1]
            )

        except ValueError:

            raise ValueError(
                "Order must be an integer."
            )

    # --------------------------------------------------------
    # Keep Order inside 3..9
    # --------------------------------------------------------

    generation_order = max(
        MIN_ORDER,
        min(
            MAX_ORDER,
            generation_order
        )
    )

    print()
    print("=" * 65)
    print("MARKOV MUSIC GENERATOR")
    print("=" * 65)

    print(
        f"Requested Order : "
        f"{generation_order}"
    )

    print(
        f"State            : "
        f"(Interval, Rhythm)"
    )

    print(
        f"Tempo            : "
        f"{TEMPO_BPM} BPM"
    )

    print(
        f"Velocity         : "
        f"{MIN_VELOCITY}-{MAX_VELOCITY}"
    )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print()
    print(
        "Loading Markov model..."
    )

    model = load_model()

    orders = available_orders(
        model
    )

    if not orders:

        raise RuntimeError(
            "The Markov model contains no orders."
        )

    print(
        f"Available Orders: "
        f"{orders}"
    )

    # --------------------------------------------------------
    # Effective order
    # --------------------------------------------------------

    effective_order = min(
        generation_order,
        max(orders)
    )

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    print()
    print(
        "Generating music..."
    )

    states, order_usage = (
        generate_states(
            model,
            effective_order
        )
    )

    print(
        f"Generated states: "
        f"{len(states)}"
    )

    # --------------------------------------------------------
    # Order statistics
    # --------------------------------------------------------

    print()
    print(
        "Order usage:"
    )

    for order, count in sorted(
        order_usage.items(),
        reverse=True
    ):

        print(
            f"  Order {order}: "
            f"{count}"
        )

    # --------------------------------------------------------
    # MIDI
    # --------------------------------------------------------

    print()
    print(
        "Creating MIDI..."
    )

    midi = states_to_midi(
        states,
        TEMPO_BPM
    )

    midi.write(
        str(MIDI_PATH)
    )

    if not MIDI_PATH.exists():

        raise RuntimeError(
            "MIDI file was not created."
        )

    print(
        f"MIDI saved to:\n"
        f"{MIDI_PATH}"
    )

    # --------------------------------------------------------
    # Verify
    # --------------------------------------------------------

    verify_midi(
        TEMPO_BPM
    )

    # --------------------------------------------------------
    # Open MuseScore
    # --------------------------------------------------------

    print()
    print(
        "Opening MuseScore..."
    )

    open_in_musescore()

    print()
    print(
        "Generation finished successfully."
    )

    print("=" * 65)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\nGeneration cancelled."
        )

        sys.exit(1)

    except Exception as exc:

        print()
        print("=" * 65)
        print("ERROR")
        print("=" * 65)
        print(
            str(exc)
        )
        print("=" * 65)

        sys.exit(1)


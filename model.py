from pathlib import Path
from collections import Counter, defaultdict
import pickle

PROJECT_DIR = Path(__file__).resolve().parent
STATES_CACHE = PROJECT_DIR / "all_states.pkl"
MODEL_CACHE = PROJECT_DIR / "markov_model.pkl"

MAX_ORDER = 9
MIN_COUNT = 3


def load_sequences():
    if not STATES_CACHE.exists():
        raise FileNotFoundError(f"Dataset not found:\n{STATES_CACHE}\nRun: python model.py after build_dataset.py")
    with open(STATES_CACHE, "rb") as f:
        data = pickle.load(f)
    if not isinstance(data, list):
        raise TypeError("all_states.pkl must contain a list of sequences.")
    return data


def build_order(sequences, order):
    table = defaultdict(Counter)
    for sequence in sequences:
        if len(sequence) <= order:
            continue
        for i in range(order, len(sequence)):
            context = tuple(sequence[i - order:i])
            next_state = sequence[i]
            table[context][next_state] += 1

    filtered = {}
    for context, transitions in table.items():
        kept = Counter({state: count for state, count in transitions.items() if count >= MIN_COUNT})
        if kept:
            filtered[context] = kept
    return filtered


def main():
    sequences = load_sequences()
    model = {}

    print("=" * 65)
    print("BUILD MARKOV MODEL")
    print("=" * 65)
    print(f"Sequences : {len(sequences):,}")
    print(f"Orders    : 1..{MAX_ORDER}")
    print(f"MIN_COUNT : {MIN_COUNT}")

    for order in range(1, MAX_ORDER + 1):
        table = build_order(sequences, order)
        model[order] = table
        transitions = sum(len(counter) for counter in table.values())
        print(f"Order {order}: contexts={len(table):,}, transitions={transitions:,}")

    with open(MODEL_CACHE, "wb") as f:
        pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"\nSaved: {MODEL_CACHE}")
    print("=" * 65)


if __name__ == "__main__":
    main()

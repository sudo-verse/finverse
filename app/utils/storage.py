import json

def save_signal(data, filename="signals.json"):
    try:
        with open(filename, "r") as f:
            existing = json.load(f)
    except:
        existing = []

    existing.append(data)

    with open(filename, "w") as f:
        json.dump(existing, f, indent=4)
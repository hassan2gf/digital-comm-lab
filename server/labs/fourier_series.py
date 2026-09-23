import numpy as np

# ---------- 1. Settings ----------
DEFAULTS = {"shape": "square", "frequency": 500, "amplitude": 1.0, "count": 1}
POINTS_PER_PERIOD = 2000
PERIODS = 2
TOTAL_POWER = {"square": 1.0, "triangle": 1 / 3, "sawtooth": 1 / 3}   # divided by A squared

# ---------- 2. Harmonic amplitudes ----------
def harmonics(shape, amplitude, count):
    if shape == "square":
        orders = 2 * np.arange(1, count + 1) - 1                  # 1, 3, 5, ...
        values = 4 * amplitude / (np.pi * orders)                 # decay as 1/n
    elif shape == "triangle":
        index = np.arange(count)
        orders = 2 * index + 1
        values = 8 * amplitude / np.pi ** 2 * (-1) ** index / orders ** 2   # decay as 1/n^2
    else:
        orders = np.arange(1, count + 1)                          # all harmonics
        values = 2 * amplitude / np.pi * (-1) ** (orders + 1) / orders
    return orders, values

# ---------- 3. Ideal waveform used as reference ----------
def ideal_wave(shape, amplitude, angle):
    if shape == "square":
        return amplitude * np.sign(np.sin(angle))
    if shape == "triangle":
        return amplitude * 2 / np.pi * np.arcsin(np.sin(angle))
    return amplitude * (2 * ((angle / (2 * np.pi) + 0.5) % 1) - 1)

# ---------- 4. Entry point ----------
def compute(settings):
    frequency = settings["frequency"]
    amplitude = settings["amplitude"]
    count = int(settings["count"])
    shape = settings["shape"]

    time = np.arange(PERIODS * POINTS_PER_PERIOD) / (frequency * POINTS_PER_PERIOD)
    angle = 2 * np.pi * frequency * time

    orders, values = harmonics(shape, amplitude, count)
    partial_sum = np.sin(np.outer(angle, orders)) @ values      # all harmonics at once
    reference = ideal_wave(shape, amplitude, angle)

    error = np.sqrt(np.mean((partial_sum - reference) ** 2))
    partial_power = np.sum(values ** 2) / 2
    full_power = TOTAL_POWER[shape] * amplitude ** 2

    return {
        "time": np.round(time * 1000, 5).tolist(),
        "sum": np.round(partial_sum, 4).tolist(),
        "ideal": np.round(reference, 4).tolist(),
        "harmonic_frequency": (orders * frequency).tolist(),
        "harmonic_amplitude": np.round(np.abs(values), 5).tolist(),
        "measurements": {
            "count": count,
            "highest": int(orders[-1] * frequency),
            "error": round(float(error), 4),
            "overshoot": round(float((np.max(partial_sum) / amplitude - 1) * 100), 2),
            "power": round(float(100 * partial_power / full_power), 2),
        },
    }
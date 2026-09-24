import numpy as np
from labs import lab2_coding as coding

# ---------- 1. Default settings ----------
DEFAULTS = {
    "code": "nrz_polar",
    "amplitude": 1.0,
    "bit_rate": 1000,
    "samples_per_bit": 20,
    "block_bits": 128,          # bits per measured block
    "averaging": True,
    "reset": False,
    "scale": "db",
    "running": True,
    "show_theory": True,
}
POINTS = 401                    # frequency grid from 0 to 4 Rb
THEORY_BLOCKS = 400             # blocks used once to build the theoretical curve

_state = {"sum": None, "count": 0, "frozen": None}
_theory = {"code": None, "curve": None, "lines": None}


# ---------- 2. Frequency grid and transform matrix ----------
def grid(samples_per_bit, length):
    frequency = np.linspace(0, 4, POINTS)
    angle = 2 * np.pi * frequency / samples_per_bit
    times = np.arange(length * samples_per_bit)
    return frequency, np.exp(-1j * np.outer(angle, times))


def block_power(settings, matrix, length):
    """Power spectrum of one random block, in volts squared."""
    bits = list(np.random.randint(0, 2, length))
    first, second = coding.encode(bits, settings["code"], settings["amplitude"])
    signal = coding.waveform(first, second, settings["samples_per_bit"])
    return np.abs(matrix @ signal) ** 2 / (length * settings["samples_per_bit"] ** 2)


# ---------- 3. Theoretical curve: average of many blocks ----------
def theory(settings, matrix, length):
    key = (settings["code"], settings["amplitude"])
    if _theory["code"] == key:
        return _theory["curve"]
    total = np.zeros(POINTS)
    for _ in range(THEORY_BLOCKS):
        total += block_power(settings, matrix, length)
    _theory["code"] = key
    _theory["curve"] = total / THEORY_BLOCKS
    return _theory["curve"]


# ---------- 4. Separate spectral lines from the continuous part ----------
def split_lines(power):
    spacing = POINTS / 4.0                       # points per Rb
    width = max(2, int(spacing / 12))
    positions = [int(round(k * spacing)) for k in range(5)]
    mask = np.ones(POINTS, dtype=bool)
    for position in positions:
        mask[max(0, position - width):min(POINTS, position + width + 1)] = False

    lines = []
    background = np.mean(power[mask]) if mask.any() else 0.0
    for index, position in enumerate(positions):
        low = max(0, position - width)
        high = min(POINTS, position + width + 1)
        strength = float(np.sum(power[low:high]) - background * (high - low))
        if strength > 8 * max(background, 1e-12):
            lines.append((float(index), strength))
    return mask, lines


# ---------- 5. Measurements on the continuous part ----------
# ---------- 5. Measurements on the continuous part ----------
def measure(frequency, power, mask):
    values = power.copy()
    values[~mask] = 0.0
    peak = np.max(values) or 1.0

    # smooth the curve before looking for the first null
    window = 9
    kernel = np.ones(window) / window
    smooth = np.convolve(values, kernel, mode="same")

    first_null = None
    start = int(POINTS / 4 * 0.3)                # ignore the very low frequencies
    for index in range(start, POINTS - 1):
        if smooth[index] < 0.03 * peak and smooth[index] <= smooth[index + 1]:
            first_null = float(frequency[index])
            break

    total = np.sum(power)
    running = np.cumsum(power)
    band = float(frequency[np.argmax(running >= 0.9 * total)]) if total > 0 else 0.0
    return {
        "first_null": round(first_null, 2) if first_null else None,
        "bandwidth90": round(band, 2),
        "power": round(float(np.mean(power) * POINTS), 4),
    }


# ---------- 6. Entry point ----------
def compute(settings):
    length = settings["block_bits"]
    frequency, matrix = grid(settings["samples_per_bit"], length)

    if settings["reset"] or _state["sum"] is None or len(_state["sum"]) != POINTS:
        _state["sum"] = np.zeros(POINTS)
        _state["count"] = 0

    if settings["running"] or _state["count"] == 0:
        power = block_power(settings, matrix, length)
        if settings["averaging"]:
            _state["sum"] += power
            _state["count"] += 1
            measured = _state["sum"] / _state["count"]
        else:
            _state["sum"] = power.copy()
            _state["count"] = 1
            measured = power
        _state["frozen"] = measured
    else:
        measured = _state["frozen"]

    reference = theory(settings, matrix, length) if settings["show_theory"] else None

    mask, lines = split_lines(measured)
    info = measure(frequency, measured, mask)
    info["blocks"] = _state["count"]
    info["bit_rate"] = settings["bit_rate"]

    scale = np.max(measured[mask]) or 1.0        # normalise on the continuous part
    floor = -50.0 if settings["scale"] == "db" else 0.0

    def convert(values, ceiling):
        normalized = values / scale
        if settings["scale"] == "db":
            return np.minimum(10 * np.log10(np.maximum(normalized, 1e-5)), ceiling)
        return np.minimum(normalized, ceiling)

    return {
        "frequency": np.round(frequency, 3).tolist(),
        "measured": np.round(convert(measured, 12), 3).tolist(),
        "theory": None if reference is None else np.round(convert(reference, 12), 3).tolist(),
        "lines": [[position, round(float(convert(np.array([value]), 25)[0]), 2)]
                  for position, value in lines],
        "floor": floor,
        "measurements": info,
    }
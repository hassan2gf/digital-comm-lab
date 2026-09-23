import numpy as np

# ---------- 1. Default settings ----------
DEFAULTS = {
    "sample_rate": 20000,     # rendering resolution, not the TP sampling rate
    "duration": 0.02,         # displayed duration in seconds
    "dc": 0.0,                # DC component
    "window": "none",         # none, hann, hamming
    "components": [
        {"on": True, "amplitude": 1.0, "frequency": 1000, "phase": 0, "shape": "sin"},
    ],
}
MAX_FREQUENCY = 10000         # spectrum display limit

# ---------- 2. Build the time-domain signal ----------
def build_signal(settings):
    rate = settings["sample_rate"]
    time = np.arange(0, settings["duration"], 1 / rate)
    components = []
    for item in settings["components"]:
        if not item["on"]:
            components.append(None)
            continue
        phase = np.deg2rad(item["phase"])
        angle = 2 * np.pi * item["frequency"] * time + phase
        wave = item["amplitude"] * (np.sin(angle) if item["shape"] == "sin" else np.cos(angle))
        components.append(wave)
    active = [c for c in components if c is not None]
    total = settings["dc"] + (sum(active) if active else np.zeros_like(time))
    return time, components, total

# ---------- 3. Spectrum ----------
def spectrum(signal, rate, window):
    size = len(signal)
    if window == "hann":
        weights = np.hanning(size)
    elif window == "hamming":
        weights = np.hamming(size)
    else:
        weights = np.ones(size)
    gain = size * np.mean(weights)                  # compensate the window energy loss
    transform = np.fft.rfft(signal * weights)
    amplitude = 2 * np.abs(transform) / gain
    amplitude[0] = np.abs(transform[0]) / gain      # DC has no mirror image
    frequency = np.fft.rfftfreq(size, 1 / rate)
    return frequency, amplitude

# ---------- 4. Entry point called by the server ----------
def compute(settings):
    rate = settings["sample_rate"]
    time, components, total = build_signal(settings)
    frequency, amplitude = spectrum(total, rate, settings["window"])
    keep = frequency <= MAX_FREQUENCY

    return {
        "time": np.round(time * 1000, 4).tolist(),        # milliseconds
        "signal": np.round(total, 4).tolist(),
        "components": [None if c is None else np.round(c, 4).tolist() for c in components],
        "frequency": np.round(frequency[keep], 2).tolist(),
        "amplitude": np.round(amplitude[keep], 5).tolist(),
        "measurements": {
            "resolution": round(rate / len(time), 2),
            "mean": round(float(np.mean(total)), 4),
            "rms": round(float(np.sqrt(np.mean(total ** 2))), 4),
            "peak": round(float(np.max(np.abs(total))), 4),
        },
    }
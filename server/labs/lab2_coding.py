import numpy as np

# ---------- 1. Default settings ----------
DEFAULTS = {
    "code": "nrz_polar",
    "amplitude": 1.0,
    "bit_rate": 1000,           # bits per second
    "samples_per_bit": 20,
    "visible_bits": 16,
    "source": "random",         # random or manual
    "sequence": "1011001011100101",
    "running": True,
    "offset": 0,                # scrolling position inside one bit
    "bits": [],                 # bits currently on screen, sent back by the client
    "step": 4,                  # samples advanced per frame
    "spectrum_bits": 128,       # block length used for the spectrum
    "averaging": True,
    "reset_average": False,
    "scale": "db",              # db or linear
}
SPECTRUM_POINTS = 401           # frequency grid from 0 to 4 Rb

_average = {"sum": None, "count": 0}     # kept between calls


# ---------- 2. Bit source ----------
def next_bit(settings, index):
    if settings["source"] == "manual":
        text = "".join(c for c in settings["sequence"] if c in "01") or "0"
        return 1 if text[index % len(text)] == "1" else 0
    return int(np.random.randint(0, 2))


# ---------- 3. Line coders: bits -> levels, two half-bits each ----------
def encode(bits, code, amplitude):
    """Returns two levels per bit (first half, second half)."""
    first, second = [], []
    polarity = 1                                  # for AMI and HDB3
    previous = 0                                  # for NRZI
    zero_run = 0                                  # for HDB3
    since_pulse = 0                               # for HDB3 B rule
    for bit in bits:
        if code == "nrz_unipolar":
            level = amplitude if bit else 0.0
            first.append(level); second.append(level)
        elif code == "nrz_polar":
            level = amplitude if bit else -amplitude
            first.append(level); second.append(level)
        elif code == "nrzi":
            if bit:
                previous = 1 - previous
            level = amplitude if previous else -amplitude
            first.append(level); second.append(level)
        elif code == "rz":
            level = amplitude if bit else 0.0
            first.append(level); second.append(0.0)
        elif code == "manchester":
            high = amplitude if bit else -amplitude
            first.append(high); second.append(-high)
        elif code == "ami":
            if bit:
                level = amplitude * polarity
                polarity = -polarity
            else:
                level = 0.0
            first.append(level); second.append(level)
        else:                                     # hdb3
            if bit:
                level = amplitude * polarity
                polarity = -polarity
                zero_run = 0
                since_pulse += 1
                first.append(level); second.append(level)
            else:
                zero_run += 1
                if zero_run == 4:
                    # replace the fourth zero by a violation V
                    if since_pulse % 2 == 0:
                        # even number of pulses since last substitution: use B00V
                        level_b = amplitude * polarity
                        first[-3] = level_b; second[-3] = level_b   # B on the first zero
                        polarity = -polarity
                    level_v = amplitude * (-polarity) * -1          # V keeps last polarity
                    level_v = amplitude * polarity * -1
                    first.append(level_v); second.append(level_v)
                    zero_run = 0
                    since_pulse = 0
                else:
                    first.append(0.0); second.append(0.0)
    return np.array(first), np.array(second)


def waveform(bits, settings):
    """Builds the sampled waveform from the half-bit levels."""
    spb = settings["samples_per_bit"]
    first, second = encode(bits, settings["code"], settings["amplitude"])
    half = spb // 2
    shape = np.empty(len(bits) * spb)
    for index in range(len(bits)):
        start = index * spb
        shape[start:start + half] = first[index]
        shape[start + half:start + spb] = second[index]
    return shape


# ---------- 4. Spectrum of the current code ----------
def spectrum(settings):
    length = settings["spectrum_bits"]
    bits = [int(np.random.randint(0, 2)) for _ in range(length)] \
        if settings["source"] == "random" else \
        [next_bit(settings, i) for i in range(length)]

    spb = settings["samples_per_bit"]
    signal = waveform(bits, settings)
    signal = signal - np.mean(signal) * 0          # keep the DC component visible

    # frequency grid from 0 to 4 Rb
    frequency = np.linspace(0, 4, SPECTRUM_POINTS)
    step = 2 * np.pi * frequency / spb             # angle per sample
    times = np.arange(len(signal))
    matrix = np.exp(-1j * np.outer(step, times))
    power = np.abs(matrix @ signal) ** 2 / (length * spb ** 2)

    if settings["reset_average"] or _average["sum"] is None \
            or len(_average["sum"]) != SPECTRUM_POINTS:
        _average["sum"] = np.zeros(SPECTRUM_POINTS)
        _average["count"] = 0
    if settings["averaging"]:
        _average["sum"] += power
        _average["count"] += 1
        power = _average["sum"] / _average["count"]
    else:
        _average["sum"] = power.copy()
        _average["count"] = 1

    peak = np.max(power) or 1.0
    normalized = power / peak
    if settings["scale"] == "db":
        values = 10 * np.log10(np.maximum(normalized, 1e-6))
    else:
        values = normalized
    return frequency, values, _average["count"]


# ---------- 5. Measurements ----------
def measure(shape, bits, settings):
    spb = settings["samples_per_bit"]
    changes = np.nonzero(np.diff(np.sign(shape - np.mean(shape))))[0]
    longest = 0
    if len(shape):
        transitions = np.nonzero(np.diff(shape))[0]
        if len(transitions):
            gaps = np.diff(np.concatenate(([0], transitions, [len(shape) - 1])))
            longest = int(np.max(gaps)) / spb
        else:
            longest = len(shape) / spb
    return {
        "dc": round(float(np.mean(shape)), 4),
        "power": round(float(np.mean(shape ** 2)), 4),
        "longest_flat": round(longest, 2),
        "ones": int(sum(bits)),
    }


# ---------- 6. Entry point ----------
def compute(settings):
    spb = settings["samples_per_bit"]
    visible = settings["visible_bits"]

    bits = [int(b) for b in settings["bits"]]
    offset = int(settings["offset"])
    index = int(settings.get("index", 0))

    if len(bits) != visible + 1:                   # first call or settings changed
        bits = [next_bit(settings, i) for i in range(visible + 1)]
        index = visible + 1
        offset = 0
    elif settings["running"]:
        offset += settings["step"]
        if offset >= spb:
            offset -= spb
            bits.pop(0)
            bits.append(next_bit(settings, index))
            index += 1

    shape = waveform(bits, settings)[offset:offset + visible * spb]
    frequency, values, count = spectrum(settings)
    info = measure(shape, bits[:visible], settings)
    info["averages"] = count
    info["bit_rate"] = settings["bit_rate"]

    return {
        "y": np.round(shape, 4).tolist(),
        "bits": bits,
        "offset": offset,
        "index": index,
        "samples_per_bit": spb,
        "frequency": np.round(frequency, 3).tolist(),
        "spectrum": np.round(values, 3).tolist(),
        "measurements": info,
    }
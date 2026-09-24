import numpy as np

# ---------- 1. Default settings ----------
DEFAULTS = {
    "code": "ami",
    "amplitude": 1.0,
    "bit_rate": 1000,
    "samples_per_bit": 20,
    "visible_bits": 16,
    "source": "manual",
    "sequence": "1011001011100101",
    "running": True,
    "step": 4,
    "invert": False,
    "show_clock": False,
    "inject_error": False,
    "bits": [],
    "offset": 0,
    "index": 0,
}


# ---------- 2. Bit source ----------
def next_bit(settings, index):
    if settings["source"] == "manual":
        text = "".join(c for c in settings["sequence"] if c in "01") or "0"
        return 1 if text[index % len(text)] == "1" else 0
    return int(np.random.randint(0, 2))


# ---------- 3. Encoders: one level per half bit ----------
def encode(bits, code, amplitude):
    first, second = [], []
    polarity = 1             # AMI and HDB3 alternate the pulse sign
    last = 0                 # NRZI remembers the previous level
    zeros = 0                # HDB3 counts consecutive zeros
    pulses = 0               # HDB3 counts pulses since the last substitution
    level = amplitude        # current level for the differential codes
    previous_bit = None      # Miller needs the previous bit

    for bit in bits:
        if code == "nrz_unipolar":
            value = amplitude if bit else 0.0
            first.append(value); second.append(value)
        elif code == "nrz_polar":
            value = amplitude if bit else -amplitude
            first.append(value); second.append(value)
        elif code == "nrzi":
            if bit:
                last = 1 - last
            value = amplitude if last else -amplitude
            first.append(value); second.append(value)
        elif code == "rz":
            first.append(amplitude if bit else 0.0)
            second.append(0.0)
        elif code == "manchester":
            high = amplitude if bit else -amplitude
            first.append(high); second.append(-high)
        elif code == "manchester_diff":
            if bit == 0:
                level = -level                    # a zero starts with a transition
            first.append(level); second.append(-level)
            level = -level                        # mid-bit transition, always
        elif code == "miller":
            if bit == 1:
                first.append(level); second.append(-level)
                level = -level                    # transition in the middle
            else:
                if previous_bit == 0:
                    level = -level                # transition between two zeros
                first.append(level); second.append(level)
            previous_bit = bit
        elif code == "ami":
            if bit:
                value = amplitude * polarity
                polarity = -polarity
            else:
                value = 0.0
            first.append(value); second.append(value)
        else:                                     # hdb3
            if bit:
                value = amplitude * polarity
                polarity = -polarity
                pulses += 1
                zeros = 0
                first.append(value); second.append(value)
            else:
                zeros += 1
                if zeros == 4:
                    if pulses % 2 == 0:           # even number of pulses: use B00V
                        b_level = amplitude * polarity
                        first[-3] = b_level; second[-3] = b_level
                        polarity = -polarity
                    v_level = amplitude * -polarity   # V breaks the alternation
                    first.append(v_level); second.append(v_level)
                    zeros = 0
                    pulses = 0
                else:
                    first.append(0.0); second.append(0.0)
    return np.array(first, dtype=float), np.array(second, dtype=float)


# ---------- 4. Decoders: levels back to bits ----------
def decode(first, second, code, amplitude):
    threshold = amplitude / 2
    bits = []
    last = 0                 # NRZI
    previous_end = None      # end level of the previous bit

    for a, b in zip(first, second):
        if code in ("nrz_unipolar", "rz"):
            bits.append(1 if a > threshold else 0)
        elif code == "nrz_polar":
            bits.append(1 if a > 0 else 0)
        elif code == "nrzi":
            level = 1 if a > 0 else 0
            bits.append(1 if level != last else 0)
            last = level
        elif code == "manchester":
            bits.append(1 if a > b else 0)
        elif code == "manchester_diff":
            # a zero shows a transition at the start of the bit
            if previous_end is None:
                bits.append(1)
            else:
                bits.append(0 if abs(a - previous_end) > threshold else 1)
        elif code == "miller":
            # a one always shows a transition in the middle of the bit
            bits.append(1 if abs(a - b) > threshold else 0)
        else:                                     # ami and hdb3
            bits.append(1 if abs(a) > threshold else 0)
        previous_end = b
    return bits


# ---------- 5. Build the sampled waveforms ----------
def waveform(first, second, samples_per_bit):
    half = samples_per_bit // 2
    shape = np.empty(len(first) * samples_per_bit)
    for index in range(len(first)):
        start = index * samples_per_bit
        shape[start:start + half] = first[index]
        shape[start + half:start + samples_per_bit] = second[index]
    return shape


def message_shape(bits, samples_per_bit):
    """The original binary message, drawn as a 0/1 waveform."""
    return np.repeat(np.array(bits, dtype=float), samples_per_bit)


def clock_shape(count, samples_per_bit):
    """One clock period per bit: high then low."""
    half = samples_per_bit // 2
    single = np.concatenate([np.ones(half), np.zeros(samples_per_bit - half)])
    return np.tile(single, count)


# ---------- 6. Measurements ----------
def measure(first, second, bits, amplitude):
    levels = np.concatenate([first, second])

    changes = 0
    flat, longest = 0.0, 0.0
    previous = None
    for a, b in zip(first, second):
        for value in (a, b):
            if previous is not None and abs(value - previous) > 1e-9:
                changes += 1
                longest = max(longest, flat)
                flat = 0.0
            flat += 0.5
            previous = value
    longest = max(longest, flat)

    return {
        "levels": int(len(np.unique(np.round(levels, 6)))),
        "dc": round(float(np.mean(levels)), 4),
        "transitions": round(changes / max(len(bits), 1), 2),
        "longest_flat": round(longest, 1),
        "ones": int(sum(bits)),
        "total": len(bits),
    }


# ---------- 7. Entry point ----------
def compute(settings):
    spb = settings["samples_per_bit"]
    visible = settings["visible_bits"]

    bits = [int(b) for b in settings["bits"]]
    offset = int(settings["offset"])
    index = int(settings.get("index", 0))

    if len(bits) != visible + 1:                  # first call or settings changed
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

    amplitude = settings["amplitude"]
    first, second = encode(bits, settings["code"], amplitude)

    # optional single error: one pulse is flipped
    error_position = -1
    if settings["inject_error"] and len(first) > 4:
        error_position = len(first) // 2
        first[error_position] = -first[error_position]
        second[error_position] = -second[error_position]

    # optional wire inversion
    if settings["invert"]:
        first, second = -first, -second

    decoded = decode(first, second, settings["code"], amplitude)

    window = slice(offset, offset + visible * spb)
    code_wave = waveform(first, second, spb)[window]
    message = message_shape(bits, spb)[window]
    clock = clock_shape(len(bits), spb)[window].tolist() if settings["show_clock"] else None

    info = measure(first, second, bits, amplitude)
    info["bit_rate"] = settings["bit_rate"]
    info["decoded_ok"] = decoded[:visible] == bits[:visible]

    return {
        "message": np.round(message, 3).tolist(),
        "code": np.round(code_wave, 4).tolist(),
        "clock": clock,
        "bits": bits,
        "decoded": decoded,
        "offset": offset,
        "index": index,
        "samples_per_bit": spb,
        "error_position": error_position,
        "measurements": info,
    }
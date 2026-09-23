import numpy as np

# ---------- 1. الإعدادات ----------
DEFAUT = {"forme": "carre", "f0": 500, "A": 1.0, "N": 1}
POINTS_PAR_PERIODE = 2000     # دقة الرسم: 2000 نقطة في كل دورة
PERIODES = 2                  # نعرض دورتين
PUISSANCE = {"carre": 1.0, "triangle": 1 / 3, "dent": 1 / 3}   # القدرة النظرية ÷ A²

# ---------- 2. التوافقيات حسب شكل الإشارة ----------
def harmoniques(forme, A, N):
    if forme == "carre":
        n = 2 * np.arange(1, N + 1) - 1                     # 1, 3, 5, ...
        b = 4 * A / (np.pi * n)
    elif forme == "triangle":
        k = np.arange(N)
        n = 2 * k + 1                                       # 1, 3, 5, ...
        b = 8 * A / np.pi ** 2 * (-1) ** k / n ** 2
    else:
        n = np.arange(1, N + 1)                             # 1, 2, 3, ...
        b = 2 * A / np.pi * (-1) ** (n + 1) / n
    return n, b

# ---------- 3. الإشارة المثالية ----------
def ideal(forme, A, phase):
    if forme == "carre":
        return A * np.sign(np.sin(phase))
    if forme == "triangle":
        return A * 2 / np.pi * np.arcsin(np.sin(phase))
    return A * (2 * ((phase / (2 * np.pi) + 0.5) % 1) - 1)

# ---------- 4. الحساب ----------
def calculer(p):
    f0, A, N, forme = p["f0"], p["A"], int(p["N"]), p["forme"]
    t = np.arange(PERIODES * POINTS_PAR_PERIODE) / (f0 * POINTS_PAR_PERIODE)
    phase = 2 * np.pi * f0 * t

    n, b = harmoniques(forme, A, N)
    somme = np.sin(np.outer(phase, n)) @ b
    ref = ideal(forme, A, phase)

    erreur = np.sqrt(np.mean((somme - ref) ** 2))
    p_partielle = np.sum(b ** 2) / 2
    p_totale = PUISSANCE[forme] * A ** 2

    return {
        "t": np.round(t * 1000, 5).tolist(),
        "somme": np.round(somme, 4).tolist(),
        "ideal": np.round(ref, 4).tolist(),
        "f_harm": (n * f0).tolist(),
        "A_harm": np.round(np.abs(b), 5).tolist(),
        "mesures": {
            "N": N,
            "f_max": int(n[-1] * f0),
            "erreur": round(float(erreur), 4),
            "depassement": round(float((np.max(somme) / A - 1) * 100), 2),
            "puissance": round(float(100 * p_partielle / p_totale), 2),
        },
    }
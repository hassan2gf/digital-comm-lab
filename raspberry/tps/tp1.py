import numpy as np
from scipy import signal

# ---------- 1. الإعدادات الافتراضية ----------
DEFAUT = {
    "fs_affichage": 20000,   # تردد العينات المستعمل فقط للرسم (ليس عينات TP)
    "duree": 0.02,           # مدة الإشارة المعروضة بالثواني
    "dc": 0.0,               # المركبة المستمرة
    "fenetre": "aucune",     # نوع النافذة: aucune, hann, hamming
    # كل مركبة: تشغيل، سعة، تردد، طور بالدرجات، نوع
    # --- المرحلة ج ---
    "ech_actif": False,      # هل نعرض مرحلة أخذ العينات
    "fs": 8000,              # تردد أخذ العينات
    "antirepli": False,      # مرشح مضاد للتداخل
    "fc_anti": 3400,         # تردد قطعه
    "bloqueur": True,        # عرض العينة والحفظ (درج)
    "reconstruire": True,    # حساب الإشارة المسترجعة
    "fc_recons": 3400,       # تردد قطع مرشح الاسترجاع
    "composantes": [
        {"on": True,  "A": 1.0, "f": 1000, "phi": 0, "type": "sin"},
        {"on": False, "A": 0.5, "f": 2000, "phi": 0, "type": "sin"},
        {"on": False, "A": 0.3, "f": 3000, "phi": 0, "type": "sin"},
        {"on": False, "A": 0.2, "f": 4000, "phi": 0, "type": "sin"},
    ],
}

# ---------- 2. بناء الإشارة في الزمن ----------
def construire(p):
    fs = p["fs_affichage"]
    t = np.arange(0, p["duree"], 1 / fs)
    composantes = []
    for c in p["composantes"]:
        if not c["on"]:
            composantes.append(None)
            continue
        phi = np.deg2rad(c["phi"])
        angle = 2 * np.pi * c["f"] * t + phi
        y = c["A"] * (np.sin(angle) if c["type"] == "sin" else np.cos(angle))
        composantes.append(y)
    total = p["dc"] + sum(c for c in composantes if c is not None)
    if not isinstance(total, np.ndarray):
        total = np.full_like(t, float(p["dc"]))
    return t, composantes, total

# ---------- 3. حساب الطيف ----------
def spectre(y, fs, fenetre):
    N = len(y)
    if fenetre == "hann":
        w = np.hanning(N)
    elif fenetre == "hamming":
        w = np.hamming(N)
    else:
        w = np.ones(N)
    correction = N * np.mean(w)          # تعويض الطاقة التي تأخذها النافذة
    Y = np.fft.rfft(y * w)
    amplitudes = 2 * np.abs(Y) / correction
    amplitudes[0] = np.abs(Y[0]) / correction   # التردد 0 لا يُضاعف
    f = np.fft.rfftfreq(N, 1 / fs)
    return f, amplitudes
# ---------- 5. مرشح تمرير منخفض ----------
def passe_bas(y, fs, fc, ordre=8):
    """مرشح Butterworth يمرّر ما تحت fc ويوقف ما فوقها."""
    fc = min(fc, 0.49 * fs)                  # لا يمكن أن يتجاوز نصف تردد العينات
    sos = signal.butter(ordre, fc, btype="low", fs=fs, output="sos")
    return signal.sosfiltfilt(sos, y)

# ---------- 6. أخذ العينات والاسترجاع ----------
def echantillonner(t, y, p):
    fs_aff = p["fs_affichage"]
    fs = p["fs"]

    # 6-أ: المرشح المضاد للتداخل قبل أخذ العينات
    avant = passe_bas(y, fs_aff, p["fc_anti"]) if p["antirepli"] else y

    # 6-ب: أخذ عينة كل fs_aff/fs نقطة
    pas = max(1, int(round(fs_aff / fs)))
    indices = np.arange(0, len(t), pas)
    t_ech = t[indices]
    y_ech = avant[indices]

    # 6-ج: العينة والحفظ (كل عينة تبقى ثابتة حتى العينة التالية)
    escalier = np.repeat(y_ech, pas)[: len(t)]
    if len(escalier) < len(t):
        escalier = np.pad(escalier, (0, len(t) - len(escalier)), mode="edge")

    # 6-د: الاسترجاع بمرشح تمرير منخفض
    recons = passe_bas(escalier, fs_aff, min(p["fc_recons"], fs / 2)) if p["reconstruire"] else None

    # 6-هـ: قياس الخطأ بين الأصلية والمسترجعة
    erreur = None
    if recons is not None:
        e = y - recons
        marge = int(0.05 * len(t))           # نهمل الحواف حيث يتشوه المرشح
        e_utile = e[marge: len(e) - marge]
        erreur = {
            "max": round(float(np.max(np.abs(e_utile))), 4),
            "efficace": round(float(np.sqrt(np.mean(e_utile ** 2))), 4),
        }
    return t_ech, y_ech, escalier, recons, erreur

# ---------- 4. الدالة التي يناديها الخادم ----------
def calculer(p):
    fs = p["fs_affichage"]
    t, composantes, total = construire(p)
    f, A = spectre(total, fs, p["fenetre"])
    limite = f <= 10000                  # نعرض حتى 10 kHz فقط
    return {
        "t": np.round(t * 1000, 4).tolist(),          # الزمن بالميلي ثانية
        "y": np.round(total, 4).tolist(),
        "composantes": [
            None if c is None else np.round(c, 4).tolist() for c in composantes
        ],
        "f": np.round(f[limite], 2).tolist(),
        "A": np.round(A[limite], 5).tolist(),
        "mesures": {
            "df": round(fs / len(t), 2),              # دقة التحليل
            "moyenne": round(float(np.mean(total)), 4),
            "efficace": round(float(np.sqrt(np.mean(total ** 2))), 4),
            "crete": round(float(np.max(np.abs(total))), 4),
        },
    }
# ---------- 7. الدالة التي يناديها الخادم ----------
def calculer(p):
    fs_aff = p["fs_affichage"]
    t, composantes, total = construire(p)
    f, A = spectre(total, fs_aff, p["fenetre"])
    limite = f <= 10000

    sortie = {
        "t": np.round(t * 1000, 4).tolist(),
        "y": np.round(total, 4).tolist(),
        "composantes": [None if c is None else np.round(c, 4).tolist() for c in composantes],
        "f": np.round(f[limite], 2).tolist(),
        "A": np.round(A[limite], 5).tolist(),
        "mesures": {
            "df": round(fs_aff / len(t), 2),
            "moyenne": round(float(np.mean(total)), 4),
            "efficace": round(float(np.sqrt(np.mean(total ** 2))), 4),
            "crete": round(float(np.max(np.abs(total))), 4),
        },
    }

    if not p["ech_actif"]:
        return sortie

    # --- المرحلة ج ---
    t_ech, y_ech, escalier, recons, erreur = echantillonner(t, total, p)
    f_ech, A_ech = spectre(escalier, fs_aff, p["fenetre"])

    sortie["ech"] = {
        "t_ech": np.round(t_ech * 1000, 4).tolist(),
        "y_ech": np.round(y_ech, 4).tolist(),
        "escalier": np.round(escalier, 4).tolist() if p["bloqueur"] else None,
        "recons": None if recons is None else np.round(recons, 4).tolist(),
        "f": np.round(f_ech[limite], 2).tolist(),
        "A": np.round(A_ech[limite], 5).tolist(),
        "erreur": erreur,
        "fs": p["fs"],
        "nyquist": p["fs"] / 2,
        "n_ech": len(t_ech),
    }
    return sortie

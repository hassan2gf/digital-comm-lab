import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

COULEURS = ["#5cc8ff", "#ff9a8a", "#c9a6ff", "#7cf29a", "#ffd166", "#f78fb3", "#8ce0d8", "#b0a8ff"]
MAX_COMPOSANTES = 8
class PanneauEchantillonnage(QtWidgets.QWidget):
    """المرحلة ج: أخذ العينات، العينة والحفظ، الاسترجاع."""
    change = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        # ---------- الشاشة 1: الزمن ----------
        self.ecran_t = pg.PlotWidget()
        self.ecran_t.setBackground("#0b0e10")
        self.ecran_t.showGrid(x=True, y=True, alpha=0.3)
        self.ecran_t.setLabel("bottom", "Temps (ms)")
        self.ecran_t.setLabel("left", "Amplitude (V)")
        self.ecran_t.addLegend()
        self.c_origine = self.ecran_t.plot(pen=pg.mkPen("#4a5560", width=1), name="Originale")
        self.c_escalier = self.ecran_t.plot(pen=pg.mkPen("#ff9a8a", width=1), name="Bloqueur")
        self.c_recons = self.ecran_t.plot(pen=pg.mkPen("#7cf29a", width=2), name="Reconstruite")
        self.points = self.ecran_t.plot(pen=None, symbol="o", symbolSize=6,
                                        symbolBrush="#f5b84a", name="Échantillons")

        # ---------- الشاشة 2: الطيف ----------
        self.ecran_f = pg.PlotWidget()
        self.ecran_f.setBackground("#0b0e10")
        self.ecran_f.showGrid(x=True, y=True, alpha=0.3)
        self.ecran_f.setLabel("bottom", "Fréquence (Hz)")
        self.ecran_f.setLabel("left", "Amplitude (V)")
        self.ecran_f.addLegend()
        self.c_spectre = self.ecran_f.plot(pen=pg.mkPen("#5cc8ff", width=2), name="Signal échantillonné")
        self.ligne_fs = pg.InfiniteLine(angle=90, pen=pg.mkPen("#f5b84a", style=QtCore.Qt.DashLine),
                                        label="fs", labelOpts={"color": "#f5b84a"})
        self.ligne_ny = pg.InfiniteLine(angle=90, pen=pg.mkPen("#ff6b5e", style=QtCore.Qt.DashLine),
                                        label="fs/2", labelOpts={"color": "#ff6b5e"})
        self.ecran_f.addItem(self.ligne_fs)
        self.ecran_f.addItem(self.ligne_ny)

        # ---------- الإعدادات ----------
        self.actif = QtWidgets.QCheckBox("Activer l'échantillonnage")
        self.fs = QtWidgets.QSpinBox()
        self.fs.setRange(500, 20000); self.fs.setSingleStep(500)
        self.fs.setValue(8000); self.fs.setSuffix(" Hz")
        self.antirepli = QtWidgets.QCheckBox("Filtre anti-repliement")
        self.fc_anti = QtWidgets.QSpinBox()
        self.fc_anti.setRange(100, 9000); self.fc_anti.setValue(3400); self.fc_anti.setSuffix(" Hz")
        self.bloqueur = QtWidgets.QCheckBox("Bloqueur (escalier)")
        self.bloqueur.setChecked(True)
        self.reconstruire = QtWidgets.QCheckBox("Reconstruction")
        self.reconstruire.setChecked(True)
        self.fc_recons = QtWidgets.QSpinBox()
        self.fc_recons.setRange(100, 9000); self.fc_recons.setValue(3400); self.fc_recons.setSuffix(" Hz")

        form = QtWidgets.QFormLayout()
        form.addRow(self.actif)
        form.addRow("fs :", self.fs)
        form.addRow(self.antirepli)
        form.addRow("fc (anti-repliement) :", self.fc_anti)
        form.addRow(self.bloqueur)
        form.addRow(self.reconstruire)
        form.addRow("fc (reconstruction) :", self.fc_recons)

        for w in (self.actif, self.antirepli, self.bloqueur, self.reconstruire):
            w.stateChanged.connect(self.change.emit)
        for w in (self.fs, self.fc_anti, self.fc_recons):
            w.valueChanged.connect(self.change.emit)

        # ---------- القياسات ----------
        self.mesures = QtWidgets.QLabel("—")
        self.mesures.setStyleSheet("font-family: Consolas; color: #9aa3ad;")

        ecrans = QtWidgets.QVBoxLayout()
        ecrans.addWidget(self.ecran_t)
        ecrans.addWidget(self.ecran_f)
        ecrans.addWidget(self.mesures)

        colonne = QtWidgets.QVBoxLayout()
        colonne.addLayout(form)
        colonne.addStretch()

        principal = QtWidgets.QHBoxLayout(self)
        principal.addLayout(ecrans, 3)
        principal.addLayout(colonne, 1)

    # ---------- الإعدادات المرسلة ----------
    def valeurs(self):
        return {
            "ech_actif": self.actif.isChecked(),
            "fs": self.fs.value(),
            "antirepli": self.antirepli.isChecked(),
            "fc_anti": self.fc_anti.value(),
            "bloqueur": self.bloqueur.isChecked(),
            "reconstruire": self.reconstruire.isChecked(),
            "fc_recons": self.fc_recons.value(),
        }

    # ---------- الرسم ----------
    def afficher(self, r):
        if "ech" not in r:
            for c in (self.c_origine, self.c_escalier, self.c_recons, self.points, self.c_spectre):
                c.setData([], [])
            self.mesures.setText("Échantillonnage désactivé")
            return

        e = r["ech"]
        t = np.array(r["t"])
        self.c_origine.setData(t, np.array(r["y"]))
        self.points.setData(np.array(e["t_ech"]), np.array(e["y_ech"]))
        self.c_escalier.setData(np.array(e["escalier"]) if e["escalier"] else [],
                                np.array(e["escalier"]) is not None and t or [])
        if e["escalier"]:
            self.c_escalier.setData(t, np.array(e["escalier"]))
        else:
            self.c_escalier.setData([], [])
        if e["recons"]:
            self.c_recons.setData(t, np.array(e["recons"]))
        else:
            self.c_recons.setData([], [])

        self.c_spectre.setData(np.array(e["f"]), np.array(e["A"]))
        self.ligne_fs.setPos(e["fs"])
        self.ligne_ny.setPos(e["nyquist"])

        texte = "fs = %s Hz   |   fs/2 = %s Hz   |   %s échantillons" % (
            e["fs"], e["nyquist"], e["n_ech"])
        if e["erreur"]:
            texte += "   |   Erreur max = %s V   |   Erreur efficace = %s V" % (
                e["erreur"]["max"], e["erreur"]["efficace"])
        self.mesures.setText(texte)

class BlocComposante(QtWidgets.QGroupBox):
    """صندوق إعدادات مركبة واحدة."""
    change = QtCore.pyqtSignal()
    supprimer = QtCore.pyqtSignal(object)      # يحمل الصندوق نفسه

    def __init__(self, defaut):
        super().__init__()
        self.on = QtWidgets.QCheckBox("Activer")
        self.on.setChecked(defaut["on"])
        self.type = QtWidgets.QComboBox()
        self.type.addItems(["sin", "cos"])
        self.A = QtWidgets.QDoubleSpinBox()
        self.A.setRange(0, 5); self.A.setSingleStep(0.1); self.A.setValue(defaut["A"])
        self.f = QtWidgets.QSpinBox()
        self.f.setRange(1, 9000); self.f.setValue(defaut["f"]); self.f.setSuffix(" Hz")
        self.phi = QtWidgets.QSpinBox()
        self.phi.setRange(-180, 180); self.phi.setValue(defaut["phi"]); self.phi.setSuffix(" °")
        self.bouton_suppr = QtWidgets.QPushButton("Supprimer")

        grille = QtWidgets.QFormLayout(self)
        grille.addRow(self.on)
        grille.addRow("Type :", self.type)
        grille.addRow("A :", self.A)
        grille.addRow("f :", self.f)
        grille.addRow("φ :", self.phi)
        grille.addRow(self.bouton_suppr)

        for w in (self.A, self.f, self.phi):
            w.valueChanged.connect(self.change.emit)
        self.type.currentTextChanged.connect(self.change.emit)
        self.on.stateChanged.connect(self.change.emit)
        self.bouton_suppr.clicked.connect(lambda: self.supprimer.emit(self))

    def valeurs(self):
        return {"on": self.on.isChecked(), "type": self.type.currentText(),
                "A": self.A.value(), "f": self.f.value(), "phi": self.phi.value()}

class PanneauFourier(QtWidgets.QWidget):
    """تبويب متسلسلة فورييه: بناء إشارة من توافقياتها."""
    demande = QtCore.pyqtSignal(str, dict)
    FORMES = [("Carrée", "carre"), ("Triangulaire", "triangle"), ("Dent de scie", "dent")]

    def __init__(self):
        super().__init__()

        # ---------- شاشة الزمن ----------
        self.ecran_t = pg.PlotWidget()
        self.ecran_t.setBackground("#0b0e10")
        self.ecran_t.showGrid(x=True, y=True, alpha=0.3)
        self.ecran_t.setLabel("bottom", "Temps (ms)")
        self.ecran_t.setLabel("left", "Amplitude (V)")
        self.ecran_t.addLegend()
        self.c_ideal = self.ecran_t.plot(
            pen=pg.mkPen("#6f7a84", width=2, style=QtCore.Qt.DashLine), name="Signal idéal")
        self.c_somme = self.ecran_t.plot(
            pen=pg.mkPen("#f5b84a", width=2), name="Somme des harmoniques")

        # ---------- شاشة الطيف (أعمدة) ----------
        self.ecran_f = pg.PlotWidget()
        self.ecran_f.setBackground("#0b0e10")
        self.ecran_f.showGrid(x=True, y=True, alpha=0.3)
        self.ecran_f.setLabel("bottom", "Fréquence (Hz)")
        self.ecran_f.setLabel("left", "Amplitude (V)")
        self.barres = pg.BarGraphItem(x=[], height=[], width=1, brush="#5cc8ff")
        self.ecran_f.addItem(self.barres)

        # ---------- الإعدادات ----------
        self.forme = QtWidgets.QComboBox()
        for texte, cle in self.FORMES:
            self.forme.addItem(texte, cle)
        self.f0 = QtWidgets.QSpinBox()
        self.f0.setRange(50, 2000); self.f0.setValue(500); self.f0.setSuffix(" Hz")
        self.A = QtWidgets.QDoubleSpinBox()
        self.A.setRange(0.1, 5); self.A.setSingleStep(0.1); self.A.setValue(1.0)
        self.N = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.N.setRange(1, 100); self.N.setValue(1)
        self.texte_N = QtWidgets.QLabel("N = 1 harmonique")
        self.voir_ideal = QtWidgets.QCheckBox("Afficher le signal idéal")
        self.voir_ideal.setChecked(True)

        self.forme.currentIndexChanged.connect(self.envoyer)
        self.f0.valueChanged.connect(self.envoyer)
        self.A.valueChanged.connect(self.envoyer)
        self.N.valueChanged.connect(self.envoyer)
        self.voir_ideal.stateChanged.connect(
            lambda: self.c_ideal.setVisible(self.voir_ideal.isChecked()))

        form = QtWidgets.QFormLayout()
        form.addRow("Forme :", self.forme)
        form.addRow("f0 :", self.f0)
        form.addRow("A :", self.A)
        form.addRow(self.texte_N)
        form.addRow(self.N)
        form.addRow(self.voir_ideal)

        # ---------- القياسات ----------
        self.mesures = QtWidgets.QLabel("—")
        self.mesures.setStyleSheet("font-family: Consolas; color: #9aa3ad;")

        ecrans = QtWidgets.QVBoxLayout()
        ecrans.addWidget(self.ecran_t, 3)
        ecrans.addWidget(self.ecran_f, 2)
        ecrans.addWidget(self.mesures)
        colonne = QtWidgets.QVBoxLayout()
        colonne.addLayout(form)
        colonne.addStretch()
        principal = QtWidgets.QHBoxLayout(self)
        principal.addLayout(ecrans, 3)
        principal.addLayout(colonne, 1)

    def envoyer(self):
        n = self.N.value()
        self.texte_N.setText("N = %d harmonique%s" % (n, "s" if n > 1 else ""))
        params = {"forme": self.forme.currentData(), "f0": self.f0.value(),
                  "A": self.A.value(), "N": n}
        self.demande.emit("fourier", params)

    def afficher(self, r):
        t = np.array(r["t"])
        self.c_somme.setData(t, np.array(r["somme"]))
        self.c_ideal.setData(t, np.array(r["ideal"]))
        self.barres.setOpts(x=np.array(r["f_harm"]), height=np.array(r["A_harm"]),
                            width=0.4 * self.f0.value())
        m = r["mesures"]
        self.mesures.setText(
            "N = %s   |   Dernière harmonique = %s Hz   |   Erreur efficace = %s V   |   "
            "Dépassement = %s %%   |   Puissance restituée = %s %%"
            % (m["N"], m["f_max"], m["erreur"], m["depassement"], m["puissance"]))
class TP1(QtWidgets.QWidget):
    demande = QtCore.pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()
        self.blocs = []
        self.dernier = None                    # آخر نتيجة وصلت

        # ---------- الشاشة 1: مركبة واحدة ----------
        self.choix = QtWidgets.QComboBox()
        self.choix.currentIndexChanged.connect(self.dessiner_composante)
        self.ecran_c = self._nouvel_ecran("Temps (ms)", "Amplitude (V)")
        self.courbe_c = self.ecran_c.plot(pen=pg.mkPen(COULEURS[0], width=2))

        entete = QtWidgets.QHBoxLayout()
        entete.addWidget(QtWidgets.QLabel("Composante affichée :"))
        entete.addWidget(self.choix)
        entete.addStretch()

        # ---------- الشاشة 2: المجموع ----------
        self.ecran_s = self._nouvel_ecran("Temps (ms)", "Amplitude (V)")
        self.courbe_s = self.ecran_s.plot(pen=pg.mkPen("#f5b84a", width=2))

        # ---------- الشاشة 3: الطيف ----------
        self.ecran_f = self._nouvel_ecran("Fréquence (Hz)", "Amplitude (V)")
        self.courbe_f = self.ecran_f.plot(pen=pg.mkPen("#5cc8ff", width=2))

        # ---------- عمود المركبات ----------
        self.conteneur = QtWidgets.QWidget()
        self.liste = QtWidgets.QVBoxLayout(self.conteneur)
        self.liste.addStretch()
        defilement = QtWidgets.QScrollArea()
        defilement.setWidget(self.conteneur)
        defilement.setWidgetResizable(True)
        defilement.setMinimumWidth(240)

        self.bouton_ajout = QtWidgets.QPushButton("+ Ajouter une composante")
        self.bouton_ajout.clicked.connect(lambda: self.ajouter())

        # ---------- إعدادات عامة ----------
        self.dc = QtWidgets.QDoubleSpinBox()
        self.dc.setRange(-5, 5); self.dc.setSingleStep(0.1)
        self.dc.valueChanged.connect(self.envoyer)
        self.fenetre = QtWidgets.QComboBox()
        self.fenetre.addItems(["aucune", "hann", "hamming"])
        self.fenetre.currentTextChanged.connect(self.envoyer)
        generaux = QtWidgets.QFormLayout()
        generaux.addRow("Composante continue :", self.dc)
        generaux.addRow("Fenêtre :", self.fenetre)

        # ---------- القياسات ----------
        self.mesures = QtWidgets.QLabel("—")
        self.mesures.setStyleSheet("font-family: Consolas; color: #9aa3ad;")

        # ---------- الترتيب ----------
        ecrans = QtWidgets.QVBoxLayout()
        ecrans.addLayout(entete)
        ecrans.addWidget(self.ecran_c)
        ecrans.addWidget(QtWidgets.QLabel("Somme des composantes"))
        ecrans.addWidget(self.ecran_s)
        ecrans.addWidget(QtWidgets.QLabel("Spectre de la somme"))
        ecrans.addWidget(self.ecran_f)
        ecrans.addWidget(self.mesures)

        colonne = QtWidgets.QVBoxLayout()
        colonne.addWidget(defilement, 1)
        colonne.addWidget(self.bouton_ajout)
        colonne.addLayout(generaux)

        page_signaux = QtWidgets.QWidget()
        mise_en_page = QtWidgets.QHBoxLayout(page_signaux)
        mise_en_page.addLayout(ecrans, 3)
        mise_en_page.addLayout(colonne, 1)

        self.panneau_ech = PanneauEchantillonnage()
        self.panneau_ech.change.connect(self.envoyer)

        self.etapes = QtWidgets.QTabWidget()
        self.etapes.addTab(page_signaux, "A/B — Signaux et spectre")
        self.panneau_fourier = PanneauFourier()
        self.panneau_fourier.demande.connect(self.demande.emit)
        self.etapes.addTab(self.panneau_ech, "C — Échantillonnage")
        self.etapes.addTab(self.panneau_fourier, "Série de Fourier")
        principal = QtWidgets.QVBoxLayout(self)
        principal.addWidget(self.etapes)

        # مركبتان في البداية
        self.ajouter({"on": True, "A": 1.0, "f": 1000, "phi": 0}, envoi=False)
        self.ajouter({"on": False, "A": 0.5, "f": 2000, "phi": 0}, envoi=False)

    # ---------- أدوات داخلية ----------
    def _nouvel_ecran(self, x, y):
        e = pg.PlotWidget()
        e.setBackground("#0b0e10")
        e.showGrid(x=True, y=True, alpha=0.3)
        e.setLabel("bottom", x)
        e.setLabel("left", y)
        return e

    def ajouter(self, defaut=None, envoi=True):
        if len(self.blocs) >= MAX_COMPOSANTES:
            return
        if defaut is None:
            defaut = {"on": True, "A": 0.5, "f": 1000 * (len(self.blocs) + 1), "phi": 0}
        bloc = BlocComposante(defaut)
        bloc.change.connect(self.envoyer)
        bloc.supprimer.connect(self.retirer)
        self.blocs.append(bloc)
        self.liste.insertWidget(len(self.blocs) - 1, bloc)
        self.renumeroter()
        if envoi:
            self.envoyer()

    def retirer(self, bloc):
        if len(self.blocs) <= 1:
            return
        self.blocs.remove(bloc)
        bloc.setParent(None)
        self.renumeroter()
        self.envoyer()

    def renumeroter(self):
        for i, b in enumerate(self.blocs):
            b.setTitle("Composante %d" % (i + 1))
        self.bouton_ajout.setEnabled(len(self.blocs) < MAX_COMPOSANTES)
        ancien = self.choix.currentIndex()
        self.choix.blockSignals(True)
        self.choix.clear()
        self.choix.addItems(["Composante %d" % (i + 1) for i in range(len(self.blocs))])
        self.choix.setCurrentIndex(min(max(ancien, 0), len(self.blocs) - 1))
        self.choix.blockSignals(False)
        self.dessiner_composante()

    # ---------- الإرسال والاستقبال ----------
    def envoyer(self):
        params = {
            "dc": self.dc.value(),
            "fenetre": self.fenetre.currentText(),
            "composantes": [b.valeurs() for b in self.blocs],
        }
        params.update(self.panneau_ech.valeurs())
        self.demande.emit("tp1", params)

    def afficher(self, r):
        if r.get("tp") == "fourier":
            self.panneau_fourier.afficher(r)
            return
        self.dernier = r
        t = np.array(r["t"])
        self.courbe_s.setData(t, np.array(r["y"]))
        self.courbe_f.setData(np.array(r["f"]), np.array(r["A"]))
        m = r["mesures"]
        self.mesures.setText(
            "Δf = %s Hz   |   Moyenne = %s V   |   Efficace = %s V   |   Crête = %s V"
            % (m["df"], m["moyenne"], m["efficace"], m["crete"])
        )
        self.dessiner_composante()
        self.panneau_ech.afficher(r)

    def dessiner_composante(self):
        i = self.choix.currentIndex()
        if self.dernier is None or i < 0 or i >= len(self.dernier["composantes"]):
            self.courbe_c.setData([], [])
            return
        c = self.dernier["composantes"][i]
        self.courbe_c.setPen(pg.mkPen(COULEURS[i % len(COULEURS)], width=2))
        if c is None:
            self.courbe_c.setData([], [])      # المركبة مطفأة
        else:
            self.courbe_c.setData(np.array(self.dernier["t"]), np.array(c))
import sys
from PyQt5 import QtWidgets
from reseau import Reseau
from tps.tp1_gui import TP1

IP_RASPBERRY = "192.168.1.20"

class Fenetre(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Labo ComNum")
        self.resize(1280, 800)

        # ---------- 1. التبويبات (عمل تطبيقي لكل تبويب) ----------
        self.onglets = QtWidgets.QTabWidget()
        self.tp1 = TP1()
        self.onglets.addTab(self.tp1, "TP1 — Signaux et CAN")
        self.setCentralWidget(self.onglets)

        # ---------- 2. شريط الحالة ----------
        self.etat = QtWidgets.QLabel("Déconnecté")
        self.statusBar().addPermanentWidget(self.etat)

        # ---------- 3. ربط الواجهة بالشبكة ----------
        self.reseau = Reseau(IP_RASPBERRY)
        self.reseau.etat.connect(self.etat.setText)
        self.reseau.resultat.connect(self.tp1.afficher)
        self.tp1.demande.connect(self.reseau.envoyer)
        self.reseau.etat.connect(self.quand_etat)

    def quand_etat(self, texte):
        if texte == "Connecté":
            self.tp1.envoyer()   # نطلب أول حساب فور الاتصال

app = QtWidgets.QApplication(sys.argv)
fenetre = Fenetre()
fenetre.show()
sys.exit(app.exec_())
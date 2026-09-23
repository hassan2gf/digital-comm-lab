import json
from PyQt5 import QtCore, QtNetwork

class Reseau(QtCore.QObject):
    """يدير الاتصال مع الراسبيري: يرسل الطلبات ويستقبل النتائج."""

    resultat = QtCore.pyqtSignal(dict)   # إشارة تُطلق عند وصول نتيجة
    etat = QtCore.pyqtSignal(str)        # إشارة تُطلق عند تغيّر حالة الاتصال

    def __init__(self, ip, port=5000):
        super().__init__()
        self.ip, self.port = ip, port
        self.tampon = b""
        self.socket = QtNetwork.QTcpSocket(self)
        self.socket.connected.connect(lambda: self.etat.emit("Connecté"))
        self.socket.disconnected.connect(lambda: self.etat.emit("Déconnecté"))
        self.socket.readyRead.connect(self._lire)
        self.minuteur = QtCore.QTimer(self)
        self.minuteur.timeout.connect(self._verifier)
        self.minuteur.start(2000)
        self._verifier()

    def _verifier(self):
        if self.socket.state() == QtNetwork.QAbstractSocket.UnconnectedState:
            self.etat.emit("Connexion...")
            self.socket.connectToHost(self.ip, self.port)

    def envoyer(self, tp, params):
        if self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState:
            msg = {"tp": tp, "params": params}
            self.socket.write((json.dumps(msg) + "\n").encode())

    def _lire(self):
        self.tampon += bytes(self.socket.readAll())
        while b"\n" in self.tampon:
            ligne, self.tampon = self.tampon.split(b"\n", 1)
            self.resultat.emit(json.loads(ligne))
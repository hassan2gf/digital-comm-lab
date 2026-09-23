import json
from PyQt5 import QtCore, QtNetwork

class Network(QtCore.QObject):
    """Keeps a TCP link with the computation server."""

    result = QtCore.pyqtSignal(dict)
    status = QtCore.pyqtSignal(str)

    def __init__(self, host, port=5000, retry_ms=2000):
        super().__init__()
        self.host = host
        self.port = port
        self.buffer = b""
        self.socket = QtNetwork.QTcpSocket(self)
        self.socket.connected.connect(lambda: self.status.emit("Connected"))
        self.socket.disconnected.connect(lambda: self.status.emit("Disconnected"))
        self.socket.readyRead.connect(self._read)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._retry)
        self.timer.start(retry_ms)
        self._retry()

    def _retry(self):
        if self.socket.state() == QtNetwork.QAbstractSocket.UnconnectedState:
            self.status.emit("Connecting...")
            self.socket.connectToHost(self.host, self.port)

    def send(self, lab, settings):
        if self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState:
            message = {"lab": lab, "settings": settings}
            self.socket.write((json.dumps(message) + "\n").encode())

    def _read(self):
        self.buffer += bytes(self.socket.readAll())
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            self.result.emit(json.loads(line))
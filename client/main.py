import sys
from PyQt5 import QtWidgets
from network import Network
from panels.lab1_panel import Lab1

SERVER_HOST = "192.168.1.20"     # use "127.0.0.1" when running on the Pi itself


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Communications Lab")
        self.resize(1280, 800)

        self.lab1 = Lab1()
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self.lab1, "Lab 1 - Signals")
        self.setCentralWidget(self.tabs)

        self.status_label = QtWidgets.QLabel("Disconnected")
        self.statusBar().addPermanentWidget(self.status_label)

        self.network = Network(SERVER_HOST)
        self.network.status.connect(self.status_label.setText)
        self.network.status.connect(self.on_status)
        self.network.result.connect(self.lab1.display)
        self.lab1.request.connect(self.network.send)

    def on_status(self, text):
        if text == "Connected":
            self.lab1.start()


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
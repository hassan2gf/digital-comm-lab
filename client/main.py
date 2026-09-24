import sys
import os
import theme
import subprocess
from PyQt5 import QtWidgets, QtGui, QtCore
from network import Network
from home_page import HomePage
from panels.lab1_panel import Lab1
from panels.lab2_panel import Lab2


SERVER_HOST = "127.0.0.1"          # "127.0.0.1" on the Pi itself
BASE = os.path.dirname(os.path.abspath(__file__)) + os.sep


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Communications Lab")

        # ---------- 1. Pages ----------
        self.home = HomePage(BASE)
        self.lab1 = Lab1()
        self.lab2 = Lab2()
        self.pages = QtWidgets.QStackedWidget()
        self.pages.addWidget(self.home)          # index 0
        self.pages.addWidget(self.wrap(self.lab1, "Lab 1 - Signals and Spectrum"))
        self.pages.addWidget(self.wrap(self.lab2, "Lab 2 - Line Coding"))
        self.setCentralWidget(self.pages)
        self.home.chosen.connect(self.open_lab)

        # ---------- 2. Status bar ----------
        self.status_label = QtWidgets.QLabel("Disconnected")
        self.statusBar().addPermanentWidget(self.status_label)

        # ---------- 3. Network ----------
        # ---------- 3. Network ----------
        self.network = Network(SERVER_HOST)
        self.network.status.connect(self.status_label.setText)
        self.network.status.connect(self.on_status)
        self.network.result.connect(self.route)
        self.lab1.request.connect(self.network.send)
        self.lab2.request.connect(self.network.send)

        # ---------- 4. Shortcuts ----------

        # ---------- 4. Shortcuts ----------
        self.add_shortcut("Escape", self.go_home)
        self.add_shortcut("Ctrl+Q", self.close)
        self.add_shortcut("Ctrl+Shift+Q", self.power_off)
    def route(self, result):
        if result.get("lab") == "lab2":
            self.lab2.display(result)
        else:
            self.lab1.display(result)

    def add_shortcut(self, keys, action):
        shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(keys), self)
        shortcut.activated.connect(action)

    def wrap(self, panel, title):
        """Adds a header with a back button above a lab panel."""
        back = QtWidgets.QPushButton("< Back to menu")
        back.setFixedHeight(34)
        back.clicked.connect(self.go_home)
        label = QtWidgets.QLabel(title)
        label.setStyleSheet("font-size: 16px; font-weight: 600;")

        header = QtWidgets.QHBoxLayout()
        header.addWidget(back)
        header.addSpacing(16)
        header.addWidget(label)
        header.addStretch()

        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.addLayout(header)
        layout.addWidget(panel)
        return page

    def open_lab(self, key):
        if key == "lab1":
            self.lab2.stop()
            self.pages.setCurrentIndex(1)
            self.lab1.start()
        elif key == "lab2":
            self.pages.setCurrentIndex(2)
            self.lab2.start()

    def go_home(self):
        self.lab2.stop()
        self.pages.setCurrentIndex(0)

    def on_status(self, text):
        if text == "Connected" and self.pages.currentIndex() == 1:
            self.lab1.start()

    def power_off(self):
        answer = QtWidgets.QMessageBox.question(
            self, "Shutdown", "Turn off the device?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if answer == QtWidgets.QMessageBox.Yes:
            subprocess.run(["sudo", "shutdown", "-h", "now"])


app = QtWidgets.QApplication(sys.argv)
app.setStyle("Fusion")
app.setStyleSheet(theme.STYLE)
window = MainWindow()
window.showFullScreen()
sys.exit(app.exec_())

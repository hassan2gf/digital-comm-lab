from PyQt5 import QtWidgets, QtCore, QtGui

# ---------- 1. Texts to customize ----------
TITLE = "Digital Communications Laboratory"
SUBTITLE = "Faculty of Technology - Department of Electronics"
LOGO_FILE = "assets/logo.png"

# ---------- 2. Lab list: (key, title, description, ready) ----------
LABS = [
    ("lab1", "Lab 1 - Signals and Spectrum",
     "Periodic signals, spectrum and Fourier series", True),
    ("lab2", "Lab 2 - Line Coding",
     "NRZ, RZ, Manchester, AMI, HDB3 and power spectral density", True),
    ("lab3", "Lab 3 - Pulse Shaping",
     "Raised cosine filter, intersymbol interference and eye diagram", False),
    ("lab4", "Lab 4 - Digital Modulation",
     "ASK, PSK, FSK, QAM, constellation and bit error rate", False),
]


class LabCard(QtWidgets.QFrame):
    """One clickable card for a lab."""
    chosen = QtCore.pyqtSignal(str)

    def __init__(self, key, title, description, ready):
        super().__init__()
        self.key = key
        self.ready = ready
        self.setFixedSize(430, 130)
        self.setCursor(QtCore.Qt.PointingHandCursor if ready else QtCore.Qt.ForbiddenCursor)

        border = "#5a4a2a" if ready else "#2c323a"
        background = "#1f2329" if ready else "#16191d"
        text_color = "#e6e8eb" if ready else "#59626b"
        self.setStyleSheet(
            "QFrame { background: %s; border: 1px solid %s; border-radius: 12px; }"
            "QLabel { border: none; color: %s; }" % (background, border, text_color))

        name = QtWidgets.QLabel(title)
        name.setStyleSheet("font-size: 19px; font-weight: 600; border: none;")
        details = QtWidgets.QLabel(description)
        details.setWordWrap(True)
        details.setStyleSheet("font-size: 13px; color: #9aa3ad; border: none;")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.addWidget(name)
        layout.addWidget(details)
        if not ready:
            soon = QtWidgets.QLabel("Coming soon")
            soon.setStyleSheet("font-size: 12px; color: #f5b84a; border: none;")
            layout.addWidget(soon)
        layout.addStretch()

    def mousePressEvent(self, event):
        if self.ready:
            self.chosen.emit(self.key)


class HomePage(QtWidgets.QWidget):
    """Welcome screen with the logo and the list of labs."""
    chosen = QtCore.pyqtSignal(str)

    def __init__(self, base_path=""):
        super().__init__()
        self.setStyleSheet("background: #12161a;")

        logo = QtWidgets.QLabel()
        logo.setAlignment(QtCore.Qt.AlignCenter)
        picture = QtGui.QPixmap(base_path + LOGO_FILE)
        if not picture.isNull():
            logo.setPixmap(picture.scaledToHeight(130, QtCore.Qt.SmoothTransformation))

        title = QtWidgets.QLabel(TITLE)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: 600; color: #e6e8eb;")

        subtitle = QtWidgets.QLabel(SUBTITLE)
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #9aa3ad;")

        # cards on a two column grid
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(22)
        for index, (key, name, description, ready) in enumerate(LABS):
            card = LabCard(key, name, description, ready)
            card.chosen.connect(self.chosen.emit)
            grid.addWidget(card, index // 2, index % 2)

        holder = QtWidgets.QHBoxLayout()
        holder.addStretch()
        holder.addLayout(grid)
        holder.addStretch()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(logo)
        layout.addSpacing(18)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(40)
        layout.addLayout(holder)
        layout.addStretch()
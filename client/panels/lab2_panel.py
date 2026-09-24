import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import theme
from widgets import Section, Dial, LitButton, Cell

pg.setConfigOptions(antialias=False)

CODES = [
    ("NRZ unipolar", "nrz_unipolar"),
    ("NRZ polar", "nrz_polar"),
    ("NRZI", "nrzi"),
    ("RZ", "rz"),
    ("Manchester", "manchester"),
    ("Manchester differential", "manchester_diff"),
    ("Miller", "miller"),
    ("AMI", "ami"),
    ("HDB3", "hdb3"),
]


class ScreenBox(QtWidgets.QFrame):
    """A framed screen with a small header, like an instrument channel."""
    def __init__(self, title, colour, right_text=""):
        super().__init__()
        self.setObjectName("screen")
        self.title = QtWidgets.QLabel(title)
        self.title.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 12px; color: %s;" % colour)
        self.info = QtWidgets.QLabel(right_text)
        self.info.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 12px; color: %s;" % theme.MUTED)

        head = QtWidgets.QHBoxLayout()
        head.setContentsMargins(12, 5, 12, 5)
        head.addWidget(self.title)
        head.addStretch()
        head.addWidget(self.info)

        self.plot = pg.PlotWidget()
        self.plot.setStyleSheet("border: none;")

        box = QtWidgets.QVBoxLayout(self)
        box.setContentsMargins(1, 1, 1, 1)
        box.setSpacing(0)
        box.addLayout(head)
        box.addWidget(self.plot)
        


class Lab2(QtWidgets.QWidget):
    """Line coding: original message, coded signal, decoded message."""
    request = QtCore.pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()
        self.state = {"bits": [], "offset": 0, "index": 0}
        self.running = False

        # ---------- 1. Screens ----------
        self.message_box = ScreenBox("CH1 · Binary message", theme.BLUE, "16 bits")
        theme.style_plot(self.message_box.plot, "", "")
        self.message_box.plot.setYRange(-0.3, 1.6)
        self.message_box.plot.setMouseEnabled(x=False, y=False)
        self.message_box.plot.hideAxis("left")
        self.message_curve = self.message_box.plot.plot(pen=pg.mkPen(theme.BLUE, width=2))
        self.bit_texts = []

        self.code_box = ScreenBox("CH2 · Line code", theme.GREEN, "1 bit/div")
        theme.style_plot(self.code_box.plot, "Time (bits)", "Amplitude (V)")
        self.code_box.plot.setYRange(-2.1, 1.8)
        self.code_curve = self.code_box.plot.plot(pen=pg.mkPen(theme.GREEN, width=2))
        self.clock_curve = self.code_box.plot.plot(
            pen=pg.mkPen("#5b6672", width=1, style=QtCore.Qt.DashLine))
        self.error_marker = pg.InfiniteLine(
            angle=90, pen=pg.mkPen(theme.RED, width=2, style=QtCore.Qt.DashLine))
        self.error_marker.setVisible(False)
        self.code_box.plot.addItem(self.error_marker)

        # ---------- 2. Decoded strip ----------
        self.decoded_box = QtWidgets.QFrame()
        self.decoded_text = QtWidgets.QLabel("-")
        self.decoded_text.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 15px; letter-spacing: 3px;"
            "background: transparent;")
        self.decoded_status = QtWidgets.QLabel("")
        caption = QtWidgets.QLabel("DECODED")
        caption.setStyleSheet(
            "font-size: 11px; color: %s; background: transparent;" % theme.MUTED)
        caption.setFixedWidth(110)
        strip = QtWidgets.QHBoxLayout(self.decoded_box)
        strip.setContentsMargins(14, 9, 14, 9)
        strip.addWidget(caption)
        strip.addWidget(self.decoded_text)
        strip.addStretch()
        strip.addWidget(self.decoded_status)
        self.set_decoded_style(True)

        # ---------- 3. Measurement cells ----------
        self.cells = {
            "levels": Cell("Levels"),
            "dc": Cell("DC"),
            "transitions": Cell("Trans / bit"),
            "longest_flat": Cell("Longest flat"),
            "ones": Cell("Ones"),
        }
        cells_row = QtWidgets.QHBoxLayout()
        cells_row.setSpacing(9)
        for cell in self.cells.values():
            cells_row.addWidget(cell)

        # ---------- 4. Instrument panel ----------
        self.source = QtWidgets.QComboBox()
        self.source.addItems(["Random sequence", "Manual sequence"])
        self.source.setCurrentIndex(1)
        self.source.currentIndexChanged.connect(self.source_changed)
        self.sequence = QtWidgets.QLineEdit("1011001011100101")
        self.sequence.setStyleSheet("font-family: Consolas, monospace; letter-spacing: 1px;")
        self.sequence.editingFinished.connect(self.reset_bits)

        self.code = QtWidgets.QComboBox()
        for label_text, key in CODES:
            self.code.addItem(label_text, key)
        self.code.setCurrentIndex(7)                      # AMI
        self.code.currentIndexChanged.connect(self.reset_bits)

        self.amplitude = Dial("Amplitude", 1, 15, 10, ["0.1", "0.5", "1.0", "1.5"],
                              "V", divider=10.0)
        self.bit_rate = Dial("Bit rate", 1, 100, 10, ["0.1k", "1k", "5k", "10k"],
                             "kbit/s", divider=10.0)
        self.speed = Dial("Scroll speed", 1, 20, 4, ["1", "5", "10", "20"])

        self.invert = LitButton("Invert wires")
        self.show_clock = LitButton("Show bit clock")
        self.show_decoded = LitButton("Show decoded message")
        self.show_decoded.setChecked(True)
        self.show_decoded.toggled.connect(self.decoded_box.setVisible)
        self.inject_error = LitButton("Inject one bit error")

        self.run_button = QtWidgets.QPushButton("RUN")
        self.run_button.setObjectName("primary")
        self.run_button.setMinimumHeight(44)
        self.stop_button = QtWidgets.QPushButton("STOP")
        self.stop_button.setMinimumHeight(44)
        self.run_button.clicked.connect(lambda: self.set_running(True))
        self.stop_button.clicked.connect(lambda: self.set_running(False))

        panel = QtWidgets.QWidget()
        panel.setObjectName("panel")
        panel.setFixedWidth(326)
        column = QtWidgets.QVBoxLayout(panel)
        column.setContentsMargins(18, 16, 18, 16)
        column.setSpacing(10)
        column.addWidget(Section("Source"))
        column.addWidget(self.source)
        column.addWidget(self.sequence)
        column.addWidget(Section("Encoder"))
        column.addWidget(self.code)
        column.addWidget(Section("Vertical"))
        column.addWidget(self.amplitude)
        column.addWidget(Section("Horizontal"))
        column.addWidget(self.bit_rate)
        column.addWidget(self.speed)
        column.addWidget(Section("Experiments"))
        for button in (self.invert, self.show_clock, self.show_decoded, self.inject_error):
            column.addWidget(button)
        column.addStretch()
        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.stop_button)
        column.addLayout(buttons)

        # ---------- 5. Page layout ----------
        left = QtWidgets.QVBoxLayout()
        left.setContentsMargins(16, 14, 14, 14)
        left.setSpacing(11)
        left.addWidget(self.message_box, 2)
        left.addWidget(self.code_box, 3)
        left.addWidget(self.decoded_box)
        left.addLayout(cells_row)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(left, 1)
        layout.addWidget(panel)

        # ---------- 6. Frame timer ----------
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.send)
        self.waiting = False
        self.set_running(False)
    # ---------- helpers ----------
    def set_decoded_style(self, good):
        colour = "#2f5a3c" if good else "#6b3a33"
        background = "#12261a" if good else "#2a1614"
        self.decoded_box.setStyleSheet(
            "QFrame { background: %s; border: 1px solid %s; border-radius: 8px; }"
            % (background, colour))

    def set_running(self, active):
        self.running = active
        self.run_button.setObjectName("primary" if active else "")
        self.stop_button.setObjectName("" if active else "primary")
        for button in (self.run_button, self.stop_button):
            button.style().unpolish(button)
            button.style().polish(button)

    def reset_bits(self):
        self.state["bits"] = []

    def source_changed(self, index):
        self.sequence.setEnabled(index == 1)
        self.reset_bits()

    # ---------- control ----------
    def start(self):
        self.state = {"bits": [], "offset": 0, "index": 0}
        self.running = False
        self.waiting = False
        self.timer.start(40)
        self.send()

    def stop(self):
        self.timer.stop()

    # ---------- exchange ----------
    def send(self):
        if self.waiting:
            return
        settings = {
            "code": self.code.currentData(),
            "amplitude": self.amplitude.number(),
            "bit_rate": int(self.bit_rate.number() * 1000),
            "source": "manual" if self.source.currentIndex() == 1 else "random",
            "sequence": self.sequence.text(),
            "running": self.running,
            "step": int(self.speed.number()),
            "invert": self.invert.isChecked(),
            "show_clock": self.show_clock.isChecked(),
            "inject_error": self.inject_error.isChecked(),
            "bits": self.state["bits"],
            "offset": self.state["offset"],
            "index": self.state["index"],
        }
        self.waiting = True
        self.request.emit("lab2", settings)

    def display(self, result):
        self.waiting = False
        self.state = {"bits": result["bits"], "offset": result["offset"],
                      "index": result["index"]}

        spb = result["samples_per_bit"]
        message = np.array(result["message"])
        self.message_curve.setData(np.arange(len(message)) / spb, message)
        self.draw_bits(result["bits"], result["offset"], spb)

        code = np.array(result["code"])
        self.code_curve.setData(np.arange(len(code)) / spb, code)
        self.code_box.title.setText(
            "CH2 · %s%s" % (self.code.currentText(),
                            " · wires inverted" if self.invert.isChecked() else ""))
        self.code_box.info.setText("%.1f V/div · 1 bit/div" % self.amplitude.number())

        if result["clock"]:
            clock = np.array(result["clock"]) * 0.3 - 1.95
            self.clock_curve.setData(np.arange(len(clock)) / spb, clock)
        else:
            self.clock_curve.setData([], [])

        position = result["error_position"]
        self.error_marker.setVisible(position >= 0)
        if position >= 0:
            self.error_marker.setPos(position - result["offset"] / spb + 0.5)

        decoded = "".join(str(b) for b in result["decoded"][:16])
        self.decoded_text.setText(decoded)
        good = result["measurements"]["decoded_ok"]
        self.set_decoded_style(good)
        if good:
            self.decoded_status.setText("✓ identical to the original message")
            self.decoded_status.setStyleSheet(
                "color: %s; font-weight: 600; background: transparent;" % theme.GREEN)
        else:
            self.decoded_status.setText("✗ different from the original message")
            self.decoded_status.setStyleSheet(
                "color: %s; font-weight: 600; background: transparent;" % theme.RED)

        info = result["measurements"]
        self.cells["levels"].set(info["levels"])
        self.cells["dc"].set("%.2f V" % info["dc"],
                             theme.GREEN if abs(info["dc"]) < 0.02 else theme.ACCENT)
        self.cells["transitions"].set("%.2f" % info["transitions"])
        self.cells["longest_flat"].set("%.1f bits" % info["longest_flat"])
        self.cells["ones"].set("%d / %d" % (info["ones"], info["total"]))

    def draw_bits(self, bits, offset, spb):
        while len(self.bit_texts) < len(bits):
            item = pg.TextItem(color=theme.DIM, anchor=(0.5, 0.5))
            self.message_box.plot.addItem(item)
            self.bit_texts.append(item)
        for index, item in enumerate(self.bit_texts):
            if index < len(bits):
                position = index + 0.5 - offset / spb
                item.setText(str(bits[index]))
                item.setPos(position, 1.4)
                item.setVisible(0 <= position <= 16)
            else:
                item.setVisible(False)
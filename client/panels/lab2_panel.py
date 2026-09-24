import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import theme

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


class Readout(QtWidgets.QFrame):
    """One small measurement box."""
    def __init__(self, title):
        super().__init__()
        self.setObjectName("card")
        self.value = QtWidgets.QLabel("-")
        self.value.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 16px; color: %s;" % theme.TEXT)
        name = QtWidgets.QLabel(title)
        name.setStyleSheet("font-size: 11px; color: %s;" % theme.MUTED)
        box = QtWidgets.QVBoxLayout(self)
        box.setContentsMargins(11, 8, 11, 8)
        box.setSpacing(2)
        box.addWidget(name)
        box.addWidget(self.value)

    def set(self, text, colour=None):
        self.value.setText(str(text))
        self.value.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 16px; color: %s;"
            % (colour or theme.TEXT))


class Lab2(QtWidgets.QWidget):
    """Line coding: original message, coded signal, decoded message."""
    request = QtCore.pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()
        self.state = {"bits": [], "offset": 0, "index": 0}
        self.running = True

        # ---------- 1. Message screen ----------
        self.message_plot = theme.style_plot(pg.PlotWidget(), "", "Message")
        self.message_plot.setYRange(-0.3, 1.6)
        self.message_plot.setMouseEnabled(x=False, y=False)
        self.message_plot.hideAxis("left")
        self.message_curve = self.message_plot.plot(pen=pg.mkPen(theme.BLUE, width=2))
        self.bit_texts = []

        # ---------- 2. Code screen ----------
        self.code_plot = theme.style_plot(pg.PlotWidget(), "Time (bits)", "Amplitude (V)")
        self.code_plot.setYRange(-1.8, 1.8)
        self.code_curve = self.code_plot.plot(pen=pg.mkPen(theme.GREEN, width=2))
        self.clock_curve = self.code_plot.plot(
            pen=pg.mkPen(theme.MUTED, width=1, style=QtCore.Qt.DashLine))
        self.error_marker = pg.InfiniteLine(
            angle=90, pen=pg.mkPen(theme.RED, width=2, style=QtCore.Qt.DashLine))
        self.error_marker.setVisible(False)
        self.code_plot.addItem(self.error_marker)

        # ---------- 3. Decoded strip ----------
        self.decoded_box = QtWidgets.QFrame()
        self.decoded_box.setObjectName("card")
        self.decoded_text = QtWidgets.QLabel("-")
        self.decoded_text.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 15px; letter-spacing: 3px;")
        self.decoded_status = QtWidgets.QLabel("")
        strip = QtWidgets.QHBoxLayout(self.decoded_box)
        strip.setContentsMargins(14, 9, 14, 9)
        label = QtWidgets.QLabel("Decoded message")
        label.setStyleSheet("color: %s;" % theme.MUTED)
        label.setFixedWidth(130)
        strip.addWidget(label)
        strip.addWidget(self.decoded_text)
        strip.addStretch()
        strip.addWidget(self.decoded_status)

        # ---------- 4. Measurements ----------
        self.boxes = {
            "levels": Readout("Levels"),
            "dc": Readout("DC component"),
            "transitions": Readout("Transitions / bit"),
            "longest_flat": Readout("Longest flat"),
            "ones": Readout("Ones in window"),
        }
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(10)
        for box in self.boxes.values():
            row.addWidget(box)

        # ---------- 5. Settings ----------
        self.code = QtWidgets.QComboBox()
        for label_text, key in CODES:
            self.code.addItem(label_text, key)
        self.code.setCurrentIndex(7)                   # AMI
        self.code.currentIndexChanged.connect(self.reset_bits)

        self.amplitude = QtWidgets.QDoubleSpinBox()
        self.amplitude.setRange(0.1, 1.5)
        self.amplitude.setSingleStep(0.1)
        self.amplitude.setValue(1.0)
        self.amplitude.setSuffix(" V")

        self.bit_rate = QtWidgets.QSpinBox()
        self.bit_rate.setRange(100, 10000)
        self.bit_rate.setSingleStep(100)
        self.bit_rate.setValue(1000)
        self.bit_rate.setSuffix(" bit/s")

        self.source = QtWidgets.QComboBox()
        self.source.addItems(["random", "manual"])
        self.source.setCurrentIndex(1)
        self.source.currentTextChanged.connect(self.source_changed)
        self.sequence = QtWidgets.QLineEdit("1011001011100101")
        self.sequence.editingFinished.connect(self.reset_bits)

        self.speed = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.speed.setRange(1, 20)
        self.speed.setValue(4)
        self.speed_label = QtWidgets.QLabel("Scroll speed: 4")
        self.speed.valueChanged.connect(
            lambda v: self.speed_label.setText("Scroll speed: %d" % v))

        self.invert = QtWidgets.QCheckBox("Invert wires (swap polarity)")
        self.show_clock = QtWidgets.QCheckBox("Show bit clock")
        self.show_decoded = QtWidgets.QCheckBox("Show decoded message")
        self.show_decoded.setChecked(True)
        self.show_decoded.stateChanged.connect(
            lambda: self.decoded_box.setVisible(self.show_decoded.isChecked()))
        self.inject_error = QtWidgets.QCheckBox("Inject one bit error")

        self.run_button = QtWidgets.QPushButton("Stop")
        self.run_button.setObjectName("primary")
        self.run_button.clicked.connect(self.toggle_run)

        form = QtWidgets.QFormLayout()
        form.addRow("Line code:", self.code)
        form.addRow("Amplitude:", self.amplitude)
        form.addRow("Bit rate:", self.bit_rate)
        form.addRow("Source:", self.source)
        form.addRow("Sequence:", self.sequence)
        form.addRow(self.speed_label)
        form.addRow(self.speed)

        experiments = QtWidgets.QGroupBox("Experiments")
        tests = QtWidgets.QVBoxLayout(experiments)
        tests.setSpacing(9)
        for widget in (self.invert, self.show_clock, self.show_decoded, self.inject_error):
            tests.addWidget(widget)

        side = QtWidgets.QVBoxLayout()
        side.addLayout(form)
        side.addWidget(experiments)
        side.addStretch()
        side.addWidget(self.run_button)

        screens = QtWidgets.QVBoxLayout()
        screens.setSpacing(10)
        screens.addWidget(self.message_plot, 2)
        screens.addWidget(self.code_plot, 3)
        screens.addWidget(self.decoded_box)
        screens.addLayout(row)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(screens, 3)
        panel = QtWidgets.QWidget()
        panel.setFixedWidth(290)
        panel.setLayout(side)
        layout.addWidget(panel)

        # ---------- 6. Frame timer ----------
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.send)
        self.waiting = False

    # ---------- control ----------
    def start(self):
        self.state = {"bits": [], "offset": 0, "index": 0}
        self.waiting = False
        self.timer.start(40)
        self.send()

    def stop(self):
        self.timer.stop()

    def toggle_run(self):
        self.running = not self.running
        self.run_button.setText("Stop" if self.running else "Run")

    def reset_bits(self):
        self.state["bits"] = []

    def source_changed(self, text):
        self.sequence.setEnabled(text == "manual")
        self.reset_bits()

    # ---------- exchange ----------
    def send(self):
        if self.waiting:
            return
        settings = {
            "code": self.code.currentData(),
            "amplitude": self.amplitude.value(),
            "bit_rate": self.bit_rate.value(),
            "source": self.source.currentText(),
            "sequence": self.sequence.text(),
            "running": self.running,
            "step": self.speed.value(),
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
        x = np.arange(len(message)) / spb
        self.message_curve.setData(x, message)
        self.draw_bits(result["bits"], result["offset"], spb)

        code = np.array(result["code"])
        self.code_curve.setData(np.arange(len(code)) / spb, code)

        if result["clock"]:
            clock = np.array(result["clock"]) * 0.35 - 1.6
            self.clock_curve.setData(np.arange(len(clock)) / spb, clock)
        else:
            self.clock_curve.setData([], [])

        position = result["error_position"]
        self.error_marker.setVisible(position >= 0)
        if position >= 0:
            self.error_marker.setPos(position - result["offset"] / spb + 0.5)

        decoded = "".join(str(b) for b in result["decoded"][:16])
        self.decoded_text.setText(decoded)
        if result["measurements"]["decoded_ok"]:
            self.decoded_status.setText("Identical to the original message")
            self.decoded_status.setStyleSheet("color: %s; font-weight: 600;" % theme.GREEN)
        else:
            self.decoded_status.setText("Different from the original message")
            self.decoded_status.setStyleSheet("color: %s; font-weight: 600;" % theme.RED)

        info = result["measurements"]
        self.boxes["levels"].set(info["levels"])
        self.boxes["dc"].set("%.2f V" % info["dc"],
                             theme.GREEN if abs(info["dc"]) < 0.02 else theme.ACCENT)
        self.boxes["transitions"].set("%.2f" % info["transitions"])
        self.boxes["longest_flat"].set("%.1f bits" % info["longest_flat"])
        self.boxes["ones"].set("%d / %d" % (info["ones"], info["total"]))

    def draw_bits(self, bits, offset, spb):
        """Writes the bits above the message waveform."""
        while len(self.bit_texts) < len(bits):
            item = pg.TextItem(color=theme.MUTED, anchor=(0.5, 0.5))
            self.message_plot.addItem(item)
            self.bit_texts.append(item)
        for index, item in enumerate(self.bit_texts):
            if index < len(bits):
                position = index + 0.5 - offset / spb
                item.setText(str(bits[index]))
                item.setPos(position, 1.4)
                item.setVisible(0 <= position <= 16)
            else:
                item.setVisible(False)
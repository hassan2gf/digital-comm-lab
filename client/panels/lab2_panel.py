import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

CODES = [
    ("NRZ unipolar", "nrz_unipolar"),
    ("NRZ polar", "nrz_polar"),
    ("NRZI", "nrzi"),
    ("RZ", "rz"),
    ("Manchester", "manchester"),
    ("AMI", "ami"),
    ("HDB3", "hdb3"),
]


def new_plot(x_label, y_label):
    plot = pg.PlotWidget()
    plot.setBackground("#0b0e10")
    plot.showGrid(x=True, y=True, alpha=0.3)
    plot.setLabel("bottom", x_label)
    plot.setLabel("left", y_label)
    return plot


class Lab2(QtWidgets.QWidget):
    """Line coding: scrolling waveform and power spectrum."""
    request = QtCore.pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()
        self.state = {"bits": [], "offset": 0, "index": 0}
        self.running = True
        self.reset_average = False

        # ---------- 1. Waveform screen ----------
        self.wave_plot = new_plot("Time (bits)", "Amplitude (V)")
        self.wave_plot.setYRange(-2.2, 2.2)
        self.wave_curve = self.wave_plot.plot(pen=pg.mkPen("#7cf29a", width=2))
        self.bit_labels = []                        # text items above the waveform

        # ---------- 2. Spectrum screen ----------
        self.spectrum_plot = new_plot("Frequency (f / Rb)", "Power (dB)")
        self.spectrum_curve = self.spectrum_plot.plot(pen=pg.mkPen("#5cc8ff", width=2))

        # ---------- 3. Settings ----------
        self.code = QtWidgets.QComboBox()
        for label, key in CODES:
            self.code.addItem(label, key)
        self.code.currentIndexChanged.connect(self.code_changed)

        self.amplitude = QtWidgets.QDoubleSpinBox()
        self.amplitude.setRange(0.1, 2.0)
        self.amplitude.setSingleStep(0.1)
        self.amplitude.setValue(1.0)
        self.amplitude.valueChanged.connect(self.restart_average)

        self.bit_rate = QtWidgets.QSpinBox()
        self.bit_rate.setRange(100, 10000)
        self.bit_rate.setSingleStep(100)
        self.bit_rate.setValue(1000)
        self.bit_rate.setSuffix(" bit/s")

        self.speed = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.speed.setRange(1, 20)
        self.speed.setValue(4)
        self.speed_label = QtWidgets.QLabel("Scroll speed: 4")
        self.speed.valueChanged.connect(
            lambda v: self.speed_label.setText("Scroll speed: %d" % v))

        self.source = QtWidgets.QComboBox()
        self.source.addItems(["random", "manual"])
        self.source.currentTextChanged.connect(self.source_changed)
        self.sequence = QtWidgets.QLineEdit("1011001011100101")
        self.sequence.setEnabled(False)
        self.sequence.editingFinished.connect(self.restart_average)

        self.averaging = QtWidgets.QCheckBox("Spectrum averaging")
        self.averaging.setChecked(True)
        self.scale = QtWidgets.QComboBox()
        self.scale.addItems(["db", "linear"])
        self.scale.currentTextChanged.connect(self.scale_changed)

        self.run_button = QtWidgets.QPushButton("Stop")
        self.run_button.clicked.connect(self.toggle_run)
        self.reset_button = QtWidgets.QPushButton("Reset spectrum")
        self.reset_button.clicked.connect(self.restart_average)

        form = QtWidgets.QFormLayout()
        form.addRow("Code:", self.code)
        form.addRow("Amplitude:", self.amplitude)
        form.addRow("Bit rate:", self.bit_rate)
        form.addRow(self.speed_label)
        form.addRow(self.speed)
        form.addRow("Source:", self.source)
        form.addRow("Sequence:", self.sequence)
        form.addRow(self.averaging)
        form.addRow("Scale:", self.scale)
        form.addRow(self.run_button)
        form.addRow(self.reset_button)

        # ---------- 4. Readout ----------
        self.readout = QtWidgets.QLabel("-")
        self.readout.setStyleSheet("font-family: Consolas; color: #9aa3ad;")

        plots = QtWidgets.QVBoxLayout()
        plots.addWidget(self.wave_plot, 1)
        plots.addWidget(self.spectrum_plot, 1)
        plots.addWidget(self.readout)
        side = QtWidgets.QVBoxLayout()
        side.addLayout(form)
        side.addStretch()
        layout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(plots, 3)
        layout.addLayout(side, 1)

        # ---------- 5. Frame timer ----------
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.send)
        self.waiting = False                        # avoid piling up requests

    # ---------- control ----------
    def start(self):
        self.state = {"bits": [], "offset": 0, "index": 0}
        self.waiting = False
        self.timer.start(40)                        # 25 frames per second
        self.send()

    def stop(self):
        self.timer.stop()

    def toggle_run(self):
        self.running = not self.running
        self.run_button.setText("Stop" if self.running else "Run")

    def code_changed(self):
        self.state["bits"] = []                     # rebuild from scratch
        self.restart_average()

    def source_changed(self, text):
        self.sequence.setEnabled(text == "manual")
        self.state["bits"] = []
        self.restart_average()

    def scale_changed(self, text):
        self.spectrum_plot.setLabel("left", "Power (dB)" if text == "db" else "Power (linear)")
        self.restart_average()

    def restart_average(self):
        self.reset_average = True

    # ---------- exchange ----------
    def send(self):
        if self.waiting:                            # previous answer not received yet
            return
        settings = {
            "code": self.code.currentData(),
            "amplitude": self.amplitude.value(),
            "bit_rate": self.bit_rate.value(),
            "source": self.source.currentText(),
            "sequence": self.sequence.text(),
            "running": self.running,
            "step": self.speed.value(),
            "averaging": self.averaging.isChecked(),
            "reset_average": self.reset_average,
            "scale": self.scale.currentText(),
            "bits": self.state["bits"],
            "offset": self.state["offset"],
            "index": self.state["index"],
        }
        self.reset_average = False
        self.waiting = True
        self.request.emit("lab2", settings)

    def display(self, result):
        self.waiting = False
        self.state = {"bits": result["bits"], "offset": result["offset"],
                      "index": result["index"]}

        samples = result["samples_per_bit"]
        y = np.array(result["y"])
        x = np.arange(len(y)) / samples
        self.wave_curve.setData(x, y)
        self.draw_bit_labels(result["bits"], result["offset"], samples)

        self.spectrum_curve.setData(np.array(result["frequency"]),
                                    np.array(result["spectrum"]))
        info = result["measurements"]
        self.readout.setText(
            "Rb = %s bit/s   |   DC = %s V   |   Power = %s W   |   "
            "Longest flat = %s bits   |   Averages = %s"
            % (info["bit_rate"], info["dc"], info["power"],
               info["longest_flat"], info["averages"]))

    def draw_bit_labels(self, bits, offset, samples):
        """Writes each bit above the waveform, moving with it."""
        needed = len(bits)
        while len(self.bit_labels) < needed:
            item = pg.TextItem(color="#7f8a94", anchor=(0.5, 0.5))
            self.wave_plot.addItem(item)
            self.bit_labels.append(item)
        for index, item in enumerate(self.bit_labels):
            if index < needed:
                position = index + 0.5 - offset / samples
                item.setText(str(bits[index]))
                item.setPos(position, 1.9)
                item.setVisible(0 <= position <= 16)
            else:
                item.setVisible(False)
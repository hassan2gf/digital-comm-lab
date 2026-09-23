import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

COLORS = ["#5cc8ff", "#ff9a8a", "#c9a6ff", "#7cf29a", "#ffd166", "#f78fb3", "#8ce0d8", "#b0a8ff"]
MAX_COMPONENTS = 8


def new_plot(x_label, y_label):
    """Creates a dark oscilloscope-like plot area."""
    plot = pg.PlotWidget()
    plot.setBackground("#0b0e10")
    plot.showGrid(x=True, y=True, alpha=0.3)
    plot.setLabel("bottom", x_label)
    plot.setLabel("left", y_label)
    return plot


class ComponentBox(QtWidgets.QGroupBox):
    """Settings of a single sine or cosine component."""
    changed = QtCore.pyqtSignal()
    removed = QtCore.pyqtSignal(object)

    def __init__(self, values):
        super().__init__()
        self.enabled = QtWidgets.QCheckBox("Enabled")
        self.enabled.setChecked(values["on"])
        self.shape = QtWidgets.QComboBox()
        self.shape.addItems(["sin", "cos"])
        self.amplitude = QtWidgets.QDoubleSpinBox()
        self.amplitude.setRange(0, 5)
        self.amplitude.setSingleStep(0.1)
        self.amplitude.setValue(values["amplitude"])
        self.frequency = QtWidgets.QSpinBox()
        self.frequency.setRange(1, 9000)
        self.frequency.setValue(values["frequency"])
        self.frequency.setSuffix(" Hz")
        self.phase = QtWidgets.QSpinBox()
        self.phase.setRange(-180, 180)
        self.phase.setValue(values["phase"])
        self.phase.setSuffix(" deg")
        self.delete_button = QtWidgets.QPushButton("Remove")

        form = QtWidgets.QFormLayout(self)
        form.addRow(self.enabled)
        form.addRow("Shape:", self.shape)
        form.addRow("Amplitude:", self.amplitude)
        form.addRow("Frequency:", self.frequency)
        form.addRow("Phase:", self.phase)
        form.addRow(self.delete_button)

        for widget in (self.amplitude, self.frequency, self.phase):
            widget.valueChanged.connect(self.changed.emit)
        self.shape.currentTextChanged.connect(self.changed.emit)
        self.enabled.stateChanged.connect(self.changed.emit)
        self.delete_button.clicked.connect(lambda: self.removed.emit(self))

    def values(self):
        return {
            "on": self.enabled.isChecked(),
            "shape": self.shape.currentText(),
            "amplitude": self.amplitude.value(),
            "frequency": self.frequency.value(),
            "phase": self.phase.value(),
        }


class SignalsPage(QtWidgets.QWidget):
    """Single components, their sum, and the spectrum of the sum."""
    request = QtCore.pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()
        self.boxes = []
        self.last_result = None

        self.selector = QtWidgets.QComboBox()
        self.selector.currentIndexChanged.connect(self.draw_selected)
        self.component_plot = new_plot("Time (ms)", "Amplitude (V)")
        self.component_curve = self.component_plot.plot(pen=pg.mkPen(COLORS[0], width=2))

        header = QtWidgets.QHBoxLayout()
        header.addWidget(QtWidgets.QLabel("Displayed component:"))
        header.addWidget(self.selector)
        header.addStretch()

        self.sum_plot = new_plot("Time (ms)", "Amplitude (V)")
        self.sum_curve = self.sum_plot.plot(pen=pg.mkPen("#f5b84a", width=2))

        self.spectrum_plot = new_plot("Frequency (Hz)", "Amplitude (V)")
        self.spectrum_curve = self.spectrum_plot.plot(pen=pg.mkPen("#5cc8ff", width=2))

        # component column with its own scroll bar
        holder = QtWidgets.QWidget()
        self.column = QtWidgets.QVBoxLayout(holder)
        self.column.addStretch()
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(holder)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(240)

        self.add_button = QtWidgets.QPushButton("+ Add component")
        self.add_button.clicked.connect(lambda: self.add_component())

        self.dc = QtWidgets.QDoubleSpinBox()
        self.dc.setRange(-5, 5)
        self.dc.setSingleStep(0.1)
        self.dc.valueChanged.connect(self.send)
        self.window = QtWidgets.QComboBox()
        self.window.addItems(["none", "hann", "hamming"])
        self.window.currentTextChanged.connect(self.send)

        options = QtWidgets.QFormLayout()
        options.addRow("DC component:", self.dc)
        options.addRow("Window:", self.window)

        self.readout = QtWidgets.QLabel("-")
        self.readout.setStyleSheet("font-family: Consolas; color: #9aa3ad;")

        plots = QtWidgets.QVBoxLayout()
        plots.addLayout(header)
        plots.addWidget(self.component_plot)
        plots.addWidget(QtWidgets.QLabel("Sum of components"))
        plots.addWidget(self.sum_plot)
        plots.addWidget(QtWidgets.QLabel("Spectrum of the sum"))
        plots.addWidget(self.spectrum_plot)
        plots.addWidget(self.readout)

        side = QtWidgets.QVBoxLayout()
        side.addWidget(scroll, 1)
        side.addWidget(self.add_button)
        side.addLayout(options)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(plots, 3)
        layout.addLayout(side, 1)

        self.add_component({"on": True, "amplitude": 1.0, "frequency": 1000, "phase": 0}, notify=False)
        self.add_component({"on": False, "amplitude": 0.5, "frequency": 2000, "phase": 0}, notify=False)

    def add_component(self, values=None, notify=True):
        if len(self.boxes) >= MAX_COMPONENTS:
            return
        if values is None:
            values = {"on": True, "amplitude": 0.5,
                      "frequency": 1000 * (len(self.boxes) + 1), "phase": 0}
        box = ComponentBox(values)
        box.changed.connect(self.send)
        box.removed.connect(self.remove_component)
        self.boxes.append(box)
        self.column.insertWidget(len(self.boxes) - 1, box)
        self.refresh_titles()
        if notify:
            self.send()

    def remove_component(self, box):
        if len(self.boxes) <= 1:
            return
        self.boxes.remove(box)
        box.setParent(None)
        self.refresh_titles()
        self.send()

    def refresh_titles(self):
        for index, box in enumerate(self.boxes):
            box.setTitle("Component %d" % (index + 1))
        self.add_button.setEnabled(len(self.boxes) < MAX_COMPONENTS)
        previous = self.selector.currentIndex()
        self.selector.blockSignals(True)          # avoid useless requests while rebuilding
        self.selector.clear()
        self.selector.addItems(["Component %d" % (i + 1) for i in range(len(self.boxes))])
        self.selector.setCurrentIndex(min(max(previous, 0), len(self.boxes) - 1))
        self.selector.blockSignals(False)
        self.draw_selected()

    def send(self):
        settings = {
            "dc": self.dc.value(),
            "window": self.window.currentText(),
            "components": [box.values() for box in self.boxes],
        }
        self.request.emit("lab1", settings)

    def display(self, result):
        self.last_result = result
        time = np.array(result["time"])
        self.sum_curve.setData(time, np.array(result["signal"]))
        self.spectrum_curve.setData(np.array(result["frequency"]), np.array(result["amplitude"]))
        info = result["measurements"]
        self.readout.setText(
            "Resolution = %s Hz   |   Mean = %s V   |   RMS = %s V   |   Peak = %s V"
            % (info["resolution"], info["mean"], info["rms"], info["peak"]))
        self.draw_selected()

    def draw_selected(self):
        index = self.selector.currentIndex()
        if self.last_result is None or index < 0 or index >= len(self.last_result["components"]):
            self.component_curve.setData([], [])
            return
        component = self.last_result["components"][index]
        self.component_curve.setPen(pg.mkPen(COLORS[index % len(COLORS)], width=2))
        if component is None:
            self.component_curve.setData([], [])
        else:
            self.component_curve.setData(np.array(self.last_result["time"]), np.array(component))


class FourierPage(QtWidgets.QWidget):
    """Builds a periodic waveform from its harmonics."""
    request = QtCore.pyqtSignal(str, dict)
    SHAPES = [("Square", "square"), ("Triangle", "triangle"), ("Sawtooth", "sawtooth")]

    def __init__(self):
        super().__init__()
        self.time_plot = new_plot("Time (ms)", "Amplitude (V)")
        self.time_plot.addLegend()
        self.ideal_curve = self.time_plot.plot(
            pen=pg.mkPen("#6f7a84", width=2, style=QtCore.Qt.DashLine), name="Ideal waveform")
        self.sum_curve = self.time_plot.plot(
            pen=pg.mkPen("#f5b84a", width=2), name="Sum of harmonics")

        self.spectrum_plot = new_plot("Frequency (Hz)", "Amplitude (V)")
        self.bars = pg.BarGraphItem(x=[], height=[], width=1, brush="#5cc8ff")
        self.spectrum_plot.addItem(self.bars)

        self.shape = QtWidgets.QComboBox()
        for label, key in self.SHAPES:
            self.shape.addItem(label, key)
        self.frequency = QtWidgets.QSpinBox()
        self.frequency.setRange(50, 2000)
        self.frequency.setValue(500)
        self.frequency.setSuffix(" Hz")
        self.amplitude = QtWidgets.QDoubleSpinBox()
        self.amplitude.setRange(0.1, 5)
        self.amplitude.setSingleStep(0.1)
        self.amplitude.setValue(1.0)
        self.count = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.count.setRange(1, 100)
        self.count.setValue(1)
        self.count_label = QtWidgets.QLabel("Harmonics: 1")
        self.show_ideal = QtWidgets.QCheckBox("Show ideal waveform")
        self.show_ideal.setChecked(True)

        self.shape.currentIndexChanged.connect(self.send)
        self.frequency.valueChanged.connect(self.send)
        self.amplitude.valueChanged.connect(self.send)
        self.count.valueChanged.connect(self.send)
        self.show_ideal.stateChanged.connect(
            lambda: self.ideal_curve.setVisible(self.show_ideal.isChecked()))

        form = QtWidgets.QFormLayout()
        form.addRow("Waveform:", self.shape)
        form.addRow("Frequency:", self.frequency)
        form.addRow("Amplitude:", self.amplitude)
        form.addRow(self.count_label)
        form.addRow(self.count)
        form.addRow(self.show_ideal)

        self.readout = QtWidgets.QLabel("-")
        self.readout.setStyleSheet("font-family: Consolas; color: #9aa3ad;")

        plots = QtWidgets.QVBoxLayout()
        plots.addWidget(self.time_plot, 3)
        plots.addWidget(self.spectrum_plot, 2)
        plots.addWidget(self.readout)
        side = QtWidgets.QVBoxLayout()
        side.addLayout(form)
        side.addStretch()
        layout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(plots, 3)
        layout.addLayout(side, 1)

    def send(self):
        count = self.count.value()
        self.count_label.setText("Harmonics: %d" % count)
        settings = {"shape": self.shape.currentData(), "frequency": self.frequency.value(),
                    "amplitude": self.amplitude.value(), "count": count}
        self.request.emit("fourier", settings)

    def display(self, result):
        time = np.array(result["time"])
        self.sum_curve.setData(time, np.array(result["sum"]))
        self.ideal_curve.setData(time, np.array(result["ideal"]))
        self.bars.setOpts(x=np.array(result["harmonic_frequency"]),
                          height=np.array(result["harmonic_amplitude"]),
                          width=0.4 * self.frequency.value())
        info = result["measurements"]
        self.readout.setText(
            "Harmonics = %s   |   Highest = %s Hz   |   RMS error = %s V   |   "
            "Overshoot = %s %%   |   Power recovered = %s %%"
            % (info["count"], info["highest"], info["error"], info["overshoot"], info["power"]))


class Lab1(QtWidgets.QWidget):
    """Lab 1 with its internal steps."""
    request = QtCore.pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()
        self.signals_page = SignalsPage()
        self.fourier_page = FourierPage()
        self.signals_page.request.connect(self.request.emit)
        self.fourier_page.request.connect(self.request.emit)

        self.steps = QtWidgets.QTabWidget()
        self.steps.addTab(self.signals_page, "Signals and spectrum")
        self.steps.addTab(self.fourier_page, "Fourier series")
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.steps)

    def start(self):
        """Asks for a first computation on both pages."""
        self.signals_page.send()
        self.fourier_page.send()

    def display(self, result):
        if result.get("lab") == "fourier":
            self.fourier_page.display(result)
        else:
            self.signals_page.display(result)
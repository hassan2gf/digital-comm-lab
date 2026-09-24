import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import theme
from widgets import Section, Dial, LitButton, Cell
from panels.lab2_panel import CODES, ScreenBox

pg.setConfigOptions(antialias=False)


class Lab3(QtWidgets.QWidget):
    """Power spectral density of line codes."""
    request = QtCore.pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()
        self.running = False
        self.reset_pending = True
        self.waiting = False

        # ---------- 1. Spectrum screen ----------
        self.screen = ScreenBox("PSD · measured vs theory", theme.BLUE, "dB · f / Rb")
        theme.style_plot(self.screen.plot, "Frequency (f / Rb)", "PSD (dB)")
        self.plot = self.screen.plot
        self.plot.addLegend(offset=(-12, 12))
        self.theory_curve = self.plot.plot(
            pen=pg.mkPen(theme.RED, width=2), name="Theory")
        self.measured_curve = self.plot.plot(
            pen=pg.mkPen(theme.BLUE, width=1.4), name="Measured")
        self.line_bars = pg.BarGraphItem(x=[], height=[], width=0.05, brush=theme.ACCENT)
        self.plot.addItem(self.line_bars)

        # ---------- 2. Measurement cells ----------
        self.cells = {
            "first_null": Cell("First null"),
            "bandwidth90": Cell("B 90%"),
            "power": Cell("Total power"),
            "blocks": Cell("Averaged blocks"),
        }
        cells_row = QtWidgets.QHBoxLayout()
        cells_row.setSpacing(9)
        for cell in self.cells.values():
            cells_row.addWidget(cell)

        # ---------- 3. Instrument panel ----------
        self.code = QtWidgets.QComboBox()
        for label_text, key in CODES:
            self.code.addItem(label_text, key)
        self.code.setCurrentIndex(1)                    # NRZ polar
        self.code.currentIndexChanged.connect(self.restart)

        self.amplitude = Dial("Amplitude", 1, 15, 10, ["0.1", "0.5", "1.0", "1.5"],
                              "V", divider=10.0)
        self.amplitude.changed.connect(self.restart)
        self.block = Dial("Block length", 32, 512, 128, ["32", "128", "256", "512"], "bits")
        self.block.changed.connect(self.restart)

        self.averaging = LitButton("Averaging")
        self.averaging.setChecked(True)
        self.averaging.toggled.connect(self.restart)
        self.show_theory = LitButton("Show theory")
        self.show_theory.setChecked(True)
        self.log_scale = LitButton("dB scale")
        self.log_scale.setChecked(True)
        self.log_scale.toggled.connect(self.scale_changed)

        self.reset_button = QtWidgets.QPushButton("Reset average")
        self.reset_button.clicked.connect(self.restart)
        self.zoom_button = QtWidgets.QPushButton("Zoom 1:1")
        self.zoom_button.clicked.connect(self.reset_zoom)

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
        column.addWidget(Section("Encoder"))
        column.addWidget(self.code)
        column.addWidget(self.amplitude)
        column.addWidget(Section("Measurement"))
        column.addWidget(self.block)
        column.addWidget(self.averaging)
        column.addWidget(self.reset_button)
        column.addWidget(Section("Display"))
        column.addWidget(self.show_theory)
        column.addWidget(self.log_scale)
        column.addWidget(self.zoom_button)
        column.addStretch()
        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.stop_button)
        column.addLayout(buttons)

        # ---------- 4. Page layout ----------
        left = QtWidgets.QVBoxLayout()
        left.setContentsMargins(16, 14, 14, 14)
        left.setSpacing(11)
        left.addWidget(self.screen, 1)
        left.addLayout(cells_row)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(left, 1)
        layout.addWidget(panel)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.send)
        self.set_running(False)
        self.reset_zoom()

    # ---------- helpers ----------
    def set_running(self, active):
        self.running = active
        self.run_button.setObjectName("primary" if active else "")
        self.stop_button.setObjectName("" if active else "primary")
        for button in (self.run_button, self.stop_button):
            button.style().unpolish(button)
            button.style().polish(button)

    def restart(self):
        self.reset_pending = True

    def scale_changed(self, active):
        self.plot.setLabel("left", "PSD (dB)" if active else "PSD (linear)")
        self.screen.info.setText(("dB" if active else "linear") + " · f / Rb")
        self.reset_zoom()
        self.restart()

    def reset_zoom(self):
        self.plot.setXRange(0, 4, padding=0)
        if self.log_scale.isChecked():
            self.plot.setYRange(-50, 14, padding=0)
        else:
            self.plot.setYRange(0, 1.6, padding=0)

    # ---------- control ----------
    def start(self):
        self.waiting = False
        self.reset_pending = True
        self.timer.start(120)          # 8 updates per second is enough for a spectrum
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
            "block_bits": int(self.block.number()),
            "averaging": self.averaging.isChecked(),
            "reset": self.reset_pending,
            "scale": "db" if self.log_scale.isChecked() else "linear",
            "running": self.running,
            "show_theory": self.show_theory.isChecked(),
        }
        self.reset_pending = False
        self.waiting = True
        self.request.emit("lab3", settings)

    def display(self, result):
        self.waiting = False
        frequency = np.array(result["frequency"])
        self.measured_curve.setData(frequency, np.array(result["measured"]))

        if result["theory"] and self.show_theory.isChecked():
            self.theory_curve.setData(frequency, np.array(result["theory"]))
        else:
            self.theory_curve.setData([], [])

        lines = result["lines"]
        floor = result["floor"]
        if lines:
            positions = [item[0] for item in lines]
            heights = [item[1] - floor for item in lines]
            self.line_bars.setOpts(x=positions, height=heights, y0=floor, width=0.05)
            self.line_bars.setVisible(True)
        else:
            self.line_bars.setVisible(False)

        info = result["measurements"]
        self.cells["first_null"].set(
            "%.2f Rb" % info["first_null"] if info["first_null"] else "-")
        self.cells["bandwidth90"].set("%.2f Rb" % info["bandwidth90"])
        self.cells["power"].set("%.2f" % info["power"])
        self.cells["blocks"].set(info["blocks"],
                                 theme.GREEN if info["blocks"] > 30 else theme.ACCENT)
        self.screen.title.setText("PSD · %s" % self.code.currentText())
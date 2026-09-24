from PyQt5 import QtWidgets, QtCore
import theme


class Section(QtWidgets.QWidget):
    """An engraved section title followed by a line."""
    def __init__(self, title):
        super().__init__()
        label = QtWidgets.QLabel(title.upper())
        label.setObjectName("section")
        rule = QtWidgets.QFrame()
        rule.setObjectName("rule")
        rule.setFrameShape(QtWidgets.QFrame.HLine)
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 8, 0, 0)
        row.setSpacing(10)
        row.addWidget(label)
        row.addWidget(rule, 1)


class Dial(QtWidgets.QWidget):
    """A labelled slider with its value and a small scale underneath."""
    changed = QtCore.pyqtSignal()

    def __init__(self, title, minimum, maximum, value, ticks, unit="", divider=1.0):
        super().__init__()
        self.divider = divider
        self.unit = unit

        self.title = QtWidgets.QLabel(title)
        self.title.setStyleSheet("color: %s;" % theme.MUTED)
        self.value = QtWidgets.QLabel("")
        self.value.setStyleSheet(
            "font-family: Consolas, monospace; color: %s;" % theme.ACCENT)

        head = QtWidgets.QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.addWidget(self.title)
        head.addStretch()
        head.addWidget(self.value)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(minimum, maximum)
        self.slider.setValue(value)
        self.slider.valueChanged.connect(self.refresh)

        scale = QtWidgets.QHBoxLayout()
        scale.setContentsMargins(0, 0, 0, 0)
        for index, tick in enumerate(ticks):
            mark = QtWidgets.QLabel(tick)
            mark.setStyleSheet(
                "font-family: Consolas, monospace; font-size: 10px; color: %s;" % theme.DIM)
            scale.addWidget(mark)
            if index < len(ticks) - 1:
                scale.addStretch()

        box = QtWidgets.QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(3)
        box.addLayout(head)
        box.addWidget(self.slider)
        box.addLayout(scale)
        self.refresh()

    def refresh(self):
        self.value.setText(self.text())
        self.changed.emit()

    def text(self):
        number = self.slider.value() / self.divider
        return ("%.1f %s" % (number, self.unit)).strip() if self.divider != 1 \
            else ("%d %s" % (number, self.unit)).strip()

    def number(self):
        return self.slider.value() / self.divider


class LitButton(QtWidgets.QPushButton):
    """A toggle button with a small LED that glows when active."""
    def __init__(self, text):
        super().__init__("  " + text)
        self.setCheckable(True)
        self.setMinimumHeight(38)
        self.setStyleSheet(
            "QPushButton { text-align: left; padding-left: 32px;"
            " background: #171b21; border: 1px solid %s; border-radius: 7px;"
            " color: %s; }"
            "QPushButton:checked { background: %s; border: 1px solid %s;"
            " color: %s; font-weight: 500; }"
            % (theme.BORDER, theme.MUTED, theme.ACCENT_DARK, theme.ACCENT, theme.ACCENT))

    def paintEvent(self, event):
        super().paintEvent(event)
        from PyQt5 import QtGui
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        if self.isChecked():
            glow = QtGui.QColor(theme.ACCENT)
            glow.setAlpha(70)
            painter.setBrush(glow)
            painter.drawEllipse(QtCore.QPointF(18, self.height() / 2), 9, 9)
        painter.setBrush(QtGui.QColor(theme.ACCENT if self.isChecked() else "#3a424c"))
        painter.drawEllipse(QtCore.QPointF(18, self.height() / 2), 4.5, 4.5)
        painter.end()


class Cell(QtWidgets.QFrame):
    """A measurement box: small caption above, value below."""
    def __init__(self, caption):
        super().__init__()
        self.setObjectName("cell")
        self.caption = QtWidgets.QLabel(caption.upper())
        self.caption.setStyleSheet("font-size: 11px; color: %s;" % theme.MUTED)
        self.value = QtWidgets.QLabel("-")
        self.value.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 16px; color: %s;" % theme.TEXT)
        box = QtWidgets.QVBoxLayout(self)
        box.setContentsMargins(12, 8, 12, 8)
        box.setSpacing(2)
        box.addWidget(self.caption)
        box.addWidget(self.value)

    def set(self, text, colour=None):
        self.value.setText(str(text))
        self.value.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 16px; color: %s;"
            % (colour or theme.TEXT))
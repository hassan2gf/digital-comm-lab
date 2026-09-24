# ---------- 1. Colour palette ----------
BACKGROUND = "#1e232a"      # window background
PANEL_TOP = "#2a313a"       # instrument panel, top of the gradient
PANEL_BOTTOM = "#232932"    # instrument panel, bottom
SCREEN = "#0b0e10"          # oscilloscope screens
BORDER = "#39424d"
EDGE = "#3d4650"            # light edge of the panel
TEXT = "#e6e8eb"
MUTED = "#9aa3ad"
DIM = "#6f7a84"
ACCENT = "#f5b84a"          # amber
ACCENT_DARK = "#33280f"     # background of a lit button
GREEN = "#7cf29a"           # coded signal
BLUE = "#5cc8ff"            # binary message
RED = "#ff6b5e"
FIELD = "#12161b"           # inputs and measurement cells

# ---------- 2. Global stylesheet ----------
STYLE = """
QWidget {
    background: %(background)s;
    color: %(text)s;
    font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif;
    font-size: 13px;
}
QLabel { background: transparent; }

QWidget#panel {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 %(panel_top)s, stop:1 %(panel_bottom)s);
    border-left: 1px solid %(edge)s;
}
QLabel#section {
    color: %(dim)s;
    font-size: 11px;
    letter-spacing: 2px;
}
QFrame#rule { background: %(edge)s; max-height: 1px; }

QPushButton {
    background: #171b21;
    border: 1px solid %(border)s;
    border-radius: 7px;
    padding: 8px 14px;
    color: %(text)s;
}
QPushButton:hover { background: #1f242c; }
QPushButton:pressed { background: #0f1215; }
QPushButton:checked {
    background: %(accent_dark)s;
    border: 1px solid %(accent)s;
    color: %(accent)s;
}
QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #f5c65f, stop:1 #e0a231);
    border: 1px solid %(accent)s;
    color: #1b1f24;
    font-weight: 600;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #ffd27a, stop:1 #eeb143);
}

QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
    background: %(field)s;
    border: 1px solid %(border)s;
    border-radius: 6px;
    padding: 5px 9px;
    min-height: 22px;
    color: %(text)s;
}
QComboBox::drop-down { border: none; width: 18px; }
QComboBox QAbstractItemView {
    background: %(field)s;
    border: 1px solid %(border)s;
    selection-background-color: %(accent_dark)s;
    color: %(text)s;
}

QCheckBox, QRadioButton { spacing: 8px; background: transparent; }
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px; height: 16px;
    border: 1px solid #5a6570;
    background: #0f1215;
}
QCheckBox::indicator { border-radius: 4px; }
QRadioButton::indicator { border-radius: 9px; }
QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border: 1px solid %(accent)s;
}
QCheckBox::indicator:checked {
    background: %(accent)s; border: 1px solid %(accent)s;
}

QSlider::groove:horizontal {
    height: 6px; border-radius: 3px; background: #141820;
}
QSlider::sub-page:horizontal {
    height: 6px; border-radius: 3px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #8a6a25, stop:1 %(accent)s);
}
QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #5a646f, stop:1 #2b323b);
    border: 1px solid #6c7783;
    width: 16px; height: 16px; margin: -6px 0; border-radius: 8px;
}

QTabWidget::pane { border: 1px solid %(border)s; border-radius: 8px; }
QTabBar::tab {
    background: transparent; color: %(muted)s;
    padding: 8px 18px; border-bottom: 2px solid transparent;
}
QTabBar::tab:selected {
    color: %(accent)s; font-weight: 600;
    border-bottom: 2px solid %(accent)s;
}
QScrollArea { border: none; }
QStatusBar { background: #171b21; color: %(muted)s; }

QFrame#cell {
    background: %(field)s;
    border: 1px solid #2c323a;
    border-radius: 7px;
}
QFrame#screen {
    background: %(screen)s;
    border: 1px solid #2c323a;
    border-radius: 8px;
}
""" % {"background": BACKGROUND, "panel_top": PANEL_TOP, "panel_bottom": PANEL_BOTTOM,
       "screen": SCREEN, "border": BORDER, "edge": EDGE, "text": TEXT,
       "muted": MUTED, "dim": DIM, "accent": ACCENT, "accent_dark": ACCENT_DARK,
       "field": FIELD}


# ---------- 3. Dark look for pyqtgraph screens ----------
def style_plot(plot, x_label, y_label):
    plot.setBackground(SCREEN)
    plot.showGrid(x=True, y=True, alpha=0.22)
    plot.setLabel("bottom", x_label, color=DIM, size="9pt")
    plot.setLabel("left", y_label, color=DIM, size="9pt")
    for side in ("bottom", "left"):
        plot.getAxis(side).setPen("#2c323a")
        plot.getAxis(side).setTextPen(DIM)
    return plot
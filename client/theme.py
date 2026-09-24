# ---------- 1. Colour palette ----------
BACKGROUND = "#1e232a"      # window background
PANEL = "#242a32"           # side panels
SCREEN = "#0b0e10"          # oscilloscope screens (unchanged)
BORDER = "#343c46"
TEXT = "#e6e8eb"
MUTED = "#9aa3ad"
ACCENT = "#f5b84a"          # amber, for the main action
GREEN = "#7cf29a"           # encoded signal
BLUE = "#5cc8ff"            # binary message
RED = "#ff6b5e"             # errors

# ---------- 2. Global stylesheet ----------
STYLE = """
QWidget {
    background: %(background)s;
    color: %(text)s;
    font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif;
    font-size: 13px;
}
QLabel { background: transparent; }
QPushButton {
    background: #13161a;
    border: 1px solid #353c45;
    border-radius: 7px;
    padding: 7px 14px;
    color: %(text)s;
}
QPushButton:hover { background: #1c2128; }
QPushButton:pressed { background: #0f1215; }
QPushButton#primary {
    background: %(accent)s;
    color: #1b1f24;
    border: none;
    font-weight: 600;
}
QPushButton#primary:hover { background: #ffc862; }
QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
    background: #13161a;
    border: 1px solid #353c45;
    border-radius: 6px;
    padding: 5px 8px;
    min-height: 22px;
    color: %(text)s;
}
QComboBox::drop-down { border: none; width: 18px; }
QComboBox QAbstractItemView {
    background: #13161a;
    border: 1px solid #353c45;
    selection-background-color: #2a2418;
    color: %(text)s;
}
QCheckBox, QRadioButton { spacing: 8px; background: transparent; }
QGroupBox {
    border: 1px solid %(border)s;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: %(muted)s;
}
QSlider::groove:horizontal {
    height: 4px; background: #353c45; border-radius: 2px;
}
QSlider::handle:horizontal {
    background: %(accent)s; width: 14px; height: 14px;
    margin: -6px 0; border-radius: 7px;
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
QStatusBar { background: #0f1215; color: %(muted)s; }
QFrame#card {
    background: %(panel)s;
    border: 1px solid %(border)s;
    border-radius: 8px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #5a6570;
    background: #0f1215;
}
QCheckBox::indicator { border-radius: 4px; }
QRadioButton::indicator { border-radius: 9px; }
QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border: 1px solid %(accent)s;
}
QCheckBox::indicator:checked {
    background: %(accent)s;
    border: 1px solid %(accent)s;
    image: none;
}
QRadioButton::indicator:checked {
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                                stop:0 %(accent)s, stop:0.45 %(accent)s,
                                stop:0.5 #0f1215, stop:1 #0f1215);
    border: 1px solid %(accent)s;
}
""" % {"background": BACKGROUND, "panel": PANEL, "border": BORDER,
       "text": TEXT, "muted": MUTED, "accent": ACCENT}


# ---------- 3. Helper for oscilloscope screens ----------
def style_plot(plot, x_label, y_label):
    """Applies the dark look to a pyqtgraph widget."""
    plot.setBackground(SCREEN)
    plot.showGrid(x=True, y=True, alpha=0.25)
    plot.setLabel("bottom", x_label, color=MUTED, size="10pt")
    plot.setLabel("left", y_label, color=MUTED, size="10pt")
    plot.getAxis("bottom").setPen(BORDER)
    plot.getAxis("left").setPen(BORDER)
    plot.getAxis("bottom").setTextPen(MUTED)
    plot.getAxis("left").setTextPen(MUTED)
    return plot
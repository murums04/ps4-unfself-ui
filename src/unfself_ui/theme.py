STYLE = """
QWidget { background: #0c121c; color: #e9eef5; font-family: 'Segoe UI', 'Helvetica Neue', 'Noto Sans', sans-serif; font-size: 10pt; }
QMainWindow { background: #0c121c; }
QLabel { background: transparent; }
QLabel#Brand { color: #57ddc5; font-size: 10pt; font-weight: 600; }
QLabel#Title { font-size: 23pt; font-weight: 700; }
QLabel#AboutTitle { font-size: 17pt; font-weight: 700; }
QLabel#Subtitle, QLabel#Hint { color: #98a9bd; }
QLabel#SectionTitle { font-weight: 600; font-size: 11pt; }
QLabel#DropTitle { font-size: 13pt; font-weight: 600; }
QLabel#DropIcon { color: #57ddc5; font-size: 28pt; }
QFrame#DropArea { background: #111e2b; border: 1px dashed #3d6677; border-radius: 12px; }
QFrame#DropArea[dragging="true"] { background: #193b40; border: 2px solid #57ddc5; }
QFrame#OutputPanel { background: #121d2a; border: 1px solid #243244; border-radius: 10px; }
QPushButton { background: #192638; border: 1px solid #314258; border-radius: 7px; padding: 8px 14px; font-weight: 600; }
QPushButton:hover { background: #23364c; border-color: #69859b; }
QPushButton:pressed { background: #0c1825; }
QPushButton:focus, QLineEdit:focus, QTableWidget:focus { border: 2px solid #57ddc5; }
QPushButton:disabled { background: #131d2a; color: #5f7186; border-color: #243244; }
QPushButton#Primary { background: #57ddc5; color: #09231f; border-color: #57ddc5; padding: 10px 22px; }
QPushButton#Primary:hover { background: #83ead8; }
QPushButton#Primary:disabled { background: #203e40; color: #70918d; border-color: #203e40; }
QPushButton#Quiet { background: transparent; border: 1px solid transparent; color: #b2c1d2; }
QPushButton#Quiet:hover { background: #1b2a3c; }
QPushButton#IconButton { padding: 7px; }
QPushButton#SupportLink { background: transparent; border: 1px solid transparent; padding: 4px; }
QPushButton#SupportLink:hover { background: #1b2a3c; }
QPushButton#SupportLink:focus { border: 2px solid #57ddc5; }
QLineEdit { background: #0d1622; border: 1px solid #35485f; border-radius: 6px; padding: 9px 10px; selection-background-color: #237e79; }
QLineEdit:disabled { color: #77899c; }
QTableWidget { background: #101a27; alternate-background-color: #131f2e; border: 1px solid #243244; border-radius: 8px; gridline-color: transparent; selection-background-color: #244c59; }
QTableWidget::item { padding: 8px; border: 0; }
QTableWidget::item:selected { background: #244c59; color: #ffffff; }
QHeaderView::section { background: #152235; color: #a7bbce; border: 0; padding: 10px 8px; font-weight: 600; }
QTableCornerButton::section { background: #152235; border: 0; }
QProgressBar { background: #1a2a3c; border: 0; border-radius: 3px; min-height: 5px; max-height: 5px; }
QProgressBar::chunk { background: #57ddc5; border-radius: 3px; }
QPlainTextEdit { background: #0b1420; color: #adc0d4; border: 1px solid #2b3c50; border-radius: 6px; padding: 8px; font-family: Consolas, Menlo, monospace; font-size: 9pt; }
QToolTip { background: #203247; color: #e9eef5; border: 1px solid #4b647e; padding: 5px; }
QScrollBar:vertical { background: #101a27; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #3a5068; min-height: 24px; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSplitter::handle { background: #243244; height: 3px; }
"""


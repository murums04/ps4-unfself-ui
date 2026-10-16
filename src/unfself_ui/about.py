from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from . import __version__
from .assets import asset_path
from .native_theme import install_native_theme
from .theme import STYLE
from .updates import UpdateChecker


def text_label(text, name="", wrap=False):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setObjectName(name)
    label.setWordWrap(wrap)
    return label


class AboutDialog(QDialog):
    def __init__(self, updates=None, parent=None):
        super().__init__(parent)
        install_native_theme()
        self.updates = updates if updates is not None else UpdateChecker(self)
        self.setWindowTitle("About PS4 Unfself UI")
        icon = QIcon(str(asset_path("icon.svg")))
        self.setWindowIcon(icon)
        self.setStyleSheet(STYLE)
        self.setMinimumWidth(540)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(18)

        header = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(icon.pixmap(64, 64))
        header.addWidget(logo)
        identity = QVBoxLayout()
        identity.setSpacing(2)
        identity.addWidget(text_label("murums", "Brand"))
        identity.addWidget(text_label("PS4 Unfself UI", "AboutTitle"))
        identity.addWidget(text_label(f"Version {__version__}", "Hint"))
        header.addLayout(identity, 1)
        self.owner_link = self.github_button("murums on GitHub", "https://github.com/murums04")
        self.upstream_link = self.github_button("Original ps4_unfself by SocraticBliss",
                                                "https://github.com/SocraticBliss/ps4_unfself")
        header.addWidget(self.owner_link, 0, Qt.AlignmentFlag.AlignTop)
        header.addWidget(self.upstream_link, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)
        layout.addWidget(text_label("Restore ELF files from already fake-signed, unencrypted PS4 SELF files.", wrap=True))

        updates_panel = QFrame()
        updates_panel.setObjectName("OutputPanel")
        updates_layout = QVBoxLayout(updates_panel)
        updates_layout.setContentsMargins(16, 14, 16, 14)
        updates_layout.setSpacing(9)
        updates_layout.addWidget(text_label("Updates", "SectionTitle"))
        self.update_status = text_label("", wrap=True)
        updates_layout.addWidget(self.update_status)
        actions = QHBoxLayout()
        self.check_button = QPushButton("Check now")
        self.check_button.clicked.connect(self.updates.check)
        self.download_button = QPushButton("Download portable")
        self.download_button.setObjectName("Primary")
        self.download_button.clicked.connect(self.open_download)
        self.release_button = QPushButton("View release")
        self.release_button.clicked.connect(self.open_release)
        actions.addWidget(self.check_button)
        actions.addWidget(self.download_button)
        actions.addWidget(self.release_button)
        actions.addStretch()
        updates_layout.addLayout(actions)
        updates_layout.addWidget(text_label("Checks GitHub on launch. Downloads open in your browser.\n"
                                           "Extract portable updates to a new folder; installers are on the release page.", "Hint", True))
        layout.addWidget(updates_panel)

        credits = QVBoxLayout()
        credits.setSpacing(7)
        credits.addWidget(text_label("Credits & license", "SectionTitle"))
        credits.addWidget(text_label("Based on ps4_unfself by SocraticBliss.\nOriginal research: Znullptr, flatz and zecoxao.", wrap=True))
        credits.addWidget(text_label("GPL-3.0 · Python · Qt for Python\nLicense notices are included with the application.", "Hint", True))
        layout.addLayout(credits)
        footer = QHBoxLayout()
        footer.addWidget(text_label("File conversion stays on your computer.", "Hint"), 1)
        close = QPushButton("Close")
        close.setDefault(True)
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        layout.addLayout(footer)
        self.updates.changed.connect(self.refresh_updates)
        self.refresh_updates()

    def github_button(self, title, url):
        button = QPushButton()
        button.setObjectName("IconButton")
        button.setIcon(QIcon(str(asset_path("github.svg"))))
        button.setIconSize(QSize(24, 24))
        button.setFixedSize(40, 40)
        button.setToolTip(title)
        button.setAccessibleName(title)
        button.clicked.connect(lambda: self.open_url(url))
        return button

    def refresh_updates(self):
        self.update_status.setText(self.updates.message)
        self.check_button.setEnabled(not self.updates.busy)
        release = self.updates.release
        self.download_button.setVisible(bool(release and release.download_url))
        self.release_button.setVisible(release is not None)

    def open_url(self, url):
        if not QDesktopServices.openUrl(QUrl(url)):
            self.update_status.setText("Could not open your browser. Please visit github.com manually.")

    def open_download(self):
        if self.updates.release and self.updates.release.download_url:
            self.open_url(self.updates.release.download_url)

    def open_release(self):
        if self.updates.release:
            self.open_url(self.updates.release.release_url)

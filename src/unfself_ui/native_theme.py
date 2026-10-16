import sys

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication, QWidget


class WindowsTitleBarTheme(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        import ctypes
        from ctypes import wintypes

        self.ctypes = ctypes
        self.set_attribute = ctypes.WinDLL("dwmapi").DwmSetWindowAttribute
        self.set_attribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
        self.set_attribute.restype = ctypes.c_long

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Show and isinstance(watched, QWidget) and watched.isWindow():
            # DWM colors use COLORREF (BGR). Unsupported attributes keep the OS default.
            for attribute, value in ((20, 1), (34, 0x00443224), (35, 0x001C120C), (36, 0x00F5EEE9)):
                color = self.ctypes.c_uint32(value)
                self.set_attribute(int(watched.winId()), attribute,
                                   self.ctypes.byref(color), self.ctypes.sizeof(color))
        return False


def install_native_theme():
    application = QApplication.instance()
    if sys.platform != "win32" or application.platformName() != "windows":
        return
    if not hasattr(application, "_native_title_theme"):
        application._native_title_theme = WindowsTitleBarTheme(application)
        application.installEventFilter(application._native_title_theme)

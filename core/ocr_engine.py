import os
from PIL import ImageGrab
import pytesseract
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QPen, QCursor
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal

from config import config_manager


class SnippingOverlay(QWidget):
    snip_image_completed = pyqtSignal(object)  # PIL Image objesi döner

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: black;")
        self.setWindowOpacity(0.35)
        self.setCursor(Qt.CrossCursor)

        self.start_pos = None
        self.end_pos = None
        self.is_drawing = False

    def start_selection(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            self.setGeometry(geo)
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.is_drawing = True
            self.update()
        elif event.button() == Qt.RightButton:
            self.close()

    def mouseMoveEvent(self, event):
        if self.is_drawing and self.start_pos:
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_drawing:
            self.is_drawing = False
            self.end_pos = event.pos()
            self.hide()
            self.close()

            if self.start_pos and self.end_pos:
                rect = QRect(self.start_pos, self.end_pos).normalized()
                if rect.width() > 8 and rect.height() > 8:
                    x = rect.x()
                    y = rect.y()
                    w = rect.width()
                    h = rect.height()

                    try:
                        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                        self.snip_image_completed.emit(img)
                    except Exception as e:
                        print(f"[OCR] Görsel yakalama hatası: {e}")

    def paintEvent(self, event):
        if self.is_drawing and self.start_pos and self.end_pos:
            painter = QPainter(self)
            rect = QRect(self.start_pos, self.end_pos).normalized()

            pen = QPen(QColor(0, 210, 255), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(QColor(0, 210, 255, 50))
            painter.drawRect(rect)

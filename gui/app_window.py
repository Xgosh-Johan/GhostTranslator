import sys
import os
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QLineEdit, QPushButton, QTabWidget, QScrollArea, QFrame,
    QComboBox, QCheckBox, QRadioButton, QDialog,
    QMessageBox, QFileDialog, QSizePolicy, QGraphicsDropShadowEffect,
    QApplication
)
from PyQt5.QtGui import QFont, QCursor, QKeySequence, QIcon, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer

from config import config_manager, BASE_DIR
from database import db
from core.tts_engine import tts_engine
from core.ai_engine import ai_engine
from core.hotkey_listener import hotkey_listener


# ==========================================
# GÜVENLİ VE DONMAYAN TUŞ / FARE KAYDEDİCİ
# ==========================================
class HotkeyCaptureDialog(QDialog):
    def __init__(self, action_name, parent=None):
        super().__init__(parent)
        self.captured_hotkey = None
        self.setWindowTitle("Kısayol Tuşu veya Fare Butonu Ata")
        self.setFixedSize(480, 180)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #0d0d11;
                border: 2px solid #10b981;
                border-radius: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel("🎯 Bir Tuşa veya Fare Yan Tuşuna Basın", self)
        title.setStyleSheet("color: #10b981; font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(f"'{action_name}' için klavyeden bir tuşa (örn: F8, F9, Alt+W)\nveya farenin yan tuşlarına (Mouse 4/5) basın.", self)
        desc.setStyleSheet("color: #d4d4d8; font-size: 13px; line-height: 1.4;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        cancel_lbl = QLabel("İptal etmek için ESC tuşuna basın", self)
        cancel_lbl.setStyleSheet("color: #71717a; font-size: 12px;")
        cancel_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(cancel_lbl)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return

        if key == Qt.Key_Escape:
            self.reject()
            return

        parts = []
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            parts.append("ctrl")
        if modifiers & Qt.AltModifier:
            parts.append("alt")
        if modifiers & Qt.ShiftModifier:
            parts.append("shift")
        if modifiers & Qt.MetaModifier:
            parts.append("windows")

        if Qt.Key_F1 <= key <= Qt.Key_F12:
            f_num = key - Qt.Key_F1 + 1
            parts.append(f"f{f_num}")
        else:
            key_seq = QKeySequence(key).toString().lower()
            if key_seq and key_seq not in parts:
                parts.append(key_seq)

        self.captured_hotkey = "+".join(parts) if parts else "f8"
        self.accept()

    def mousePressEvent(self, event):
        btn = event.button()
        if btn == Qt.XButton1:
            self.captured_hotkey = "xbutton1"
            self.accept()
        elif btn == Qt.XButton2:
            self.captured_hotkey = "xbutton2"
            self.accept()
        elif btn == Qt.MiddleButton:
            self.captured_hotkey = "middle"
            self.accept()
        else:
            super().mousePressEvent(event)


class HotkeyRecorderButton(QPushButton):
    hotkey_changed = pyqtSignal(str)

    def __init__(self, action_key, label_text, default_val, parent=None):
        super().__init__(parent)
        self.action_key = action_key
        self.label_text = label_text
        self.current_hotkey = config_manager.get("hotkeys", action_key, default_val)
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self._update_display()
        self.clicked.connect(self._open_capture_dialog)

    def _format_name(self, hk):
        hk = hk.lower().strip() if hk else ""
        if hk in ["xbutton1", "mouse_xbutton1"]:
            return "🖱️ Fare Yan Tuş 1 (Mouse 4)  -  [ Değiştir ]"
        elif hk in ["xbutton2", "mouse_xbutton2"]:
            return "🖱️ Fare Yan Tuş 2 (Mouse 5)  -  [ Değiştir ]"
        elif hk in ["middle", "mouse_middle"]:
            return "🖱️ Fare Orta Tuş (Tekerlek)  -  [ Değiştir ]"
        elif hk:
            return f"⌨️  {hk.upper()}   -  [ Değiştir ]"
        return "⚠️ Tuş Atanmadı (Tıkla ve Belirle)"

    def _update_display(self):
        txt = self._format_name(self.current_hotkey)
        self.setText(txt)
        self.setStyleSheet("""
            QPushButton {
                background-color: #141417;
                color: #ffffff;
                border: 1.5px solid #27272a;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                padding: 0 16px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #1f1f24;
                border-color: #10b981;
                color: #34d399;
            }
        """)

    def _open_capture_dialog(self):
        dlg = HotkeyCaptureDialog(self.label_text, self)
        if dlg.exec_() == QDialog.Accepted and dlg.captured_hotkey:
            self.current_hotkey = dlg.captured_hotkey
            self._update_display()
            self.hotkey_changed.emit(self.current_hotkey)


# ==========================================
# BÜYÜTÜLMÜŞ DETAY PENCERESİ (MODAL DIALOG)
# ==========================================
# ==========================================
# BÜYÜTÜLMÜŞ DETAY PENCERESİ (MODAL DIALOG)
# ==========================================
class CardDetailDialog(QDialog):
    def __init__(self, record, parent=None):
        super().__init__(parent)
        self.record = dict(record) if hasattr(record, "keys") else (record or {})
        self.setWindowTitle("Çeviri Detayı ve Okuma Kartı")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(1020, 680)
        self.drag_position = None

        self.setStyleSheet("""
            QDialog {
                background-color: #0c0c0f;
                border: 2px solid #10b981;
                border-radius: 14px;
            }
        """)

        # Ekranın tam ortasına konumlandır
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - 510,
                geo.center().y() - 340
            )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        # 1. ÜST BAŞLIK VE KAPATMA BUTONU
        header = QHBoxLayout()
        header.setSpacing(10)

        ctx = self.record.get("context_type", "SELECTION")
        badge_text = "⚡ METİN SEÇİMİ" if ctx == "SELECTION" else ("💬 CHAT ÇEVİRİSİ" if ctx == "CHAT_OUT" else "🖼️ EKRAN KIRPMA (OCR)")
        badge = QLabel(badge_text, self)
        badge.setStyleSheet("""
            background-color: #059669;
            color: #ffffff;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 6px;
        """)
        header.addWidget(badge)

        phonetic = self.record.get("phonetic", "")
        if phonetic and phonetic.strip().upper() not in ["YOK", "NONE", "NULL", ""]:
            # Uzun fonetik metinlerin başlığı patlatmasını önle
            pho_text = phonetic if len(phonetic) <= 45 else phonetic[:42] + "..."
            pho_lbl = QLabel(pho_text, self)
            pho_lbl.setToolTip(phonetic)
            pho_lbl.setStyleSheet("""
                color: #34d399;
                background-color: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
                font-weight: bold;
                font-size: 12px;
                padding: 4px 12px;
                border-radius: 6px;
            """)
            header.addWidget(pho_lbl)

        title_lbl = QLabel("📖 Detaylı Karşılaştırmalı Okuma Modu", self)
        title_lbl.setStyleSheet("color: #71717a; font-size: 12px; font-weight: 500;")
        header.addWidget(title_lbl)

        header.addStretch()

        btn_close = QPushButton("✕", self)
        btn_close.setFixedSize(30, 30)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #18181b;
                color: #a1a1aa;
                border: 1px solid #27272a;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                padding: 0;
            }
            QPushButton:hover { background-color: #7f1d1d; color: #f87171; border-color: #ef4444; }
        """)
        header.addWidget(btn_close)
        layout.addLayout(header)

        # 2. YAN YANA (2 SÜTUNLU) PARALEL OKUMA ALANI
        split_layout = QHBoxLayout()
        split_layout.setSpacing(14)

        # SOL: Orijinal Metin Kartı
        left_box = QFrame(self)
        left_box.setStyleSheet("""
            QFrame {
                background-color: #121216;
                border: 1px solid #232328;
                border-radius: 10px;
            }
        """)
        left_lay = QVBoxLayout(left_box)
        left_lay.setContentsMargins(14, 10, 14, 10)
        left_lay.setSpacing(6)

        left_title = QLabel("🇬🇧 ORİJİNAL METİN", left_box)
        left_title.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: bold;")
        left_lay.addWidget(left_title)

        left_scroll = QScrollArea(left_box)
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet("background: transparent; border: none;")
        src_val = QLabel(self.record.get("source_text", ""))
        src_val.setStyleSheet("""
            color: #ffffff;
            font-size: 15px;
            font-weight: 600;
            line-height: 1.55;
            background: transparent;
        """)
        src_val.setWordWrap(True)
        src_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        left_scroll.setWidget(src_val)
        left_lay.addWidget(left_scroll)
        split_layout.addWidget(left_box, stretch=1)

        # SAĞ: Türkçe Çeviri Kartı
        right_box = QFrame(self)
        right_box.setStyleSheet("""
            QFrame {
                background-color: #121216;
                border: 1px solid #232328;
                border-left: 3.5px solid #10b981;
                border-radius: 10px;
            }
        """)
        right_lay = QVBoxLayout(right_box)
        right_lay.setContentsMargins(14, 10, 14, 10)
        right_lay.setSpacing(6)

        right_title = QLabel("🇹🇷 TÜRKÇE ÇEVİRİSİ & ANLAMI", right_box)
        right_title.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold;")
        right_lay.addWidget(right_title)

        right_scroll = QScrollArea(right_box)
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet("background: transparent; border: none;")
        tr_val = QLabel(self.record.get("translated_text", ""))
        tr_val.setStyleSheet("""
            color: #f4f4f5;
            font-size: 15px;
            line-height: 1.6;
            background: transparent;
        """)
        tr_val.setWordWrap(True)
        tr_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        right_scroll.setWidget(tr_val)
        right_lay.addWidget(right_scroll)
        split_layout.addWidget(right_box, stretch=1)

        layout.addLayout(split_layout, stretch=1)

        # 3. 💡 DEYİM / PHRASAL VERB KARTI (Varsa)
        idiom = self.record.get("idiom", "")
        if idiom:
            idiom_box = QFrame(self)
            idiom_box.setMaximumHeight(85)
            idiom_box.setStyleSheet("background-color: rgba(30, 24, 16, 0.9); border: 1.5px solid #d97706; border-radius: 8px;")
            i_lay = QVBoxLayout(idiom_box)
            i_lay.setContentsMargins(10, 6, 10, 6)
            i_lay.setSpacing(2)
            i_title = QLabel("💡 DEYİM / PHRASAL VERB ANALİZİ", idiom_box)
            i_title.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: bold;")
            i_lay.addWidget(i_title)
            i_val = QLabel(idiom, idiom_box)
            i_val.setStyleSheet("color: #fef3c7; font-size: 12px; line-height: 1.4;")
            i_val.setWordWrap(True)
            i_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            i_lay.addWidget(i_val)
            layout.addWidget(idiom_box)

        # 4. 🎭 NATIVE ALTERNATİFLER (Varsa)
        alternatives = self.record.get("alternatives", "")
        if alternatives:
            alt_box = QFrame(self)
            alt_box.setMaximumHeight(85)
            alt_box.setStyleSheet("background-color: rgba(18, 24, 38, 0.9); border: 1.5px solid #3b82f6; border-radius: 8px;")
            a_lay = QVBoxLayout(alt_box)
            a_lay.setContentsMargins(10, 6, 10, 6)
            a_lay.setSpacing(2)
            a_title = QLabel("🎭 NATIVE ALTERNATİFLER ('Bunu Başka Nasıl Söylersin?')", alt_box)
            a_title.setStyleSheet("color: #60a5fa; font-size: 11px; font-weight: bold;")
            a_lay.addWidget(a_title)
            a_val = QLabel(alternatives, alt_box)
            a_val.setStyleSheet("color: #dbeafe; font-size: 12px; line-height: 1.4;")
            a_val.setWordWrap(True)
            a_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            a_lay.addWidget(a_val)
            layout.addWidget(alt_box)

        # 5. 📖 KELİME ANATOMİSİ VE ÖRNEK CÜMLELER (Varsa)
        examples = self.record.get("examples", "")
        if examples:
            ex_box = QFrame(self)
            ex_box.setMaximumHeight(100)
            ex_box.setStyleSheet("background-color: rgba(16, 28, 22, 0.9); border: 1.5px solid #059669; border-radius: 8px;")
            e_lay = QVBoxLayout(ex_box)
            e_lay.setContentsMargins(10, 6, 10, 6)
            e_lay.setSpacing(2)
            e_title = QLabel("📖 KELİME ANATOMİSİ VE ÖRNEK CÜMLELER", ex_box)
            e_title.setStyleSheet("color: #34d399; font-size: 11px; font-weight: bold;")
            e_lay.addWidget(e_title)
            e_val = QLabel(examples, ex_box)
            e_val.setStyleSheet("color: #ecfdf5; font-size: 12px; line-height: 1.4;")
            e_val.setWordWrap(True)
            e_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            e_lay.addWidget(e_val)
            layout.addWidget(ex_box)

        # 6. ÇÖZÜM REÇETESİ (Varsa Alt Şeritte Gösterilir)
        recipe = self.record.get("explanation", "")
        if recipe:
            rec_box = QFrame(self)
            rec_box.setMaximumHeight(95)
            rec_box.setStyleSheet("""
                QFrame {
                    background-color: rgba(30, 25, 18, 0.9);
                    border: 1.5px solid #d97706;
                    border-radius: 8px;
                }
            """)
            rec_lay = QVBoxLayout(rec_box)
            rec_lay.setContentsMargins(10, 6, 10, 6)
            rec_lay.setSpacing(2)

            rec_title = QLabel("🛠️ HATA TEŞHİSİ VE ÇÖZÜM REÇETESİ:", rec_box)
            rec_title.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: bold;")
            rec_lay.addWidget(rec_title)

            rec_val = QLabel(recipe, rec_box)
            rec_val.setStyleSheet("color: #fef3c7; font-size: 12px; line-height: 1.4;")
            rec_val.setWordWrap(True)
            rec_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            rec_lay.addWidget(rec_val)
            layout.addWidget(rec_box)

        # 7. ALT AKSİYON BUTONLARI
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)

        btn_speak = QPushButton("🔊 Dinle (1.0x)", self)
        btn_speak.setFixedHeight(38)
        btn_speak.setCursor(Qt.PointingHandCursor)
        btn_speak.setStyleSheet("background-color: #059669; font-size: 12px; font-weight: bold; border-radius: 6px; padding: 0 16px;")
        btn_speak.clicked.connect(lambda: tts_engine.speak_single(self.record.get("source_text", ""), lang="en", slow=False))
        btn_bar.addWidget(btn_speak)

        btn_slow = QPushButton("🐢 Yavaş (0.5x)", self)
        btn_slow.setFixedHeight(38)
        btn_slow.setCursor(Qt.PointingHandCursor)
        btn_slow.setStyleSheet("""
            QPushButton {
                background-color: #18181b;
                color: #e4e4e7;
                border: 1px solid #27272a;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                padding: 0 14px;
            }
            QPushButton:hover { background-color: #27272a; border-color: #10b981; color: #ffffff; }
        """)
        btn_slow.clicked.connect(lambda: tts_engine.speak_single(self.record.get("source_text", ""), lang="en", slow=True))
        btn_bar.addWidget(btn_slow)

        btn_copy_tr = QPushButton("📋 Türkçeyi Kopyala", self)
        btn_copy_tr.setFixedHeight(38)
        btn_copy_tr.setCursor(Qt.PointingHandCursor)
        btn_copy_tr.setStyleSheet("""
            QPushButton {
                background-color: #18181b;
                color: #34d399;
                border: 1px solid #059669;
                font-size: 12px;
                font-weight: 600;
                border-radius: 6px;
                padding: 0 14px;
            }
            QPushButton:hover { background-color: #059669; color: #ffffff; }
        """)
        btn_copy_tr.clicked.connect(self._copy_tr)
        btn_bar.addWidget(btn_copy_tr)

        btn_bar.addStretch()

        btn_done = QPushButton("Tamam", self)
        btn_done.setFixedHeight(38)
        btn_done.setCursor(Qt.PointingHandCursor)
        btn_done.setStyleSheet("""
            QPushButton {
                background-color: #27272a;
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                padding: 0 22px;
            }
            QPushButton:hover { background-color: #3f3f46; }
        """)
        btn_done.clicked.connect(self.close)
        btn_bar.addWidget(btn_done)

        layout.addLayout(btn_bar)

    def _copy_tr(self):
        text = self.record.get("translated_text", "")
        if text:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position') and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


# ==========================================
# KELİME KARTI BİLEŞENİ (GRID KARTLARI)
# ==========================================
class WordCardWidget(QFrame):
    favorite_toggled = pyqtSignal(int)
    deleted = pyqtSignal(int)

    def __init__(self, record, parent=None):
        super().__init__(parent)
        self.record = dict(record) if hasattr(record, "keys") else (record or {})
        self.setObjectName("wordCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(225)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QFrame#wordCard {
                background-color: #121216;
                border: 1.5px solid #232328;
                border-radius: 12px;
            }
            QFrame#wordCard:hover {
                border: 1.5px solid #10b981;
                background-color: #15151a;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(6)

        # 1. ÜST BAŞLIK VE ROZETLER
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        ctx = self.record.get("context_type", "SELECTION")
        badge_text = "⚡ METİN" if ctx == "SELECTION" else ("💬 CHAT" if ctx == "CHAT_OUT" else "🖼️ OCR")
        badge = QLabel(badge_text, self)
        badge.setStyleSheet("""
            background-color: #059669;
            color: #ffffff;
            font-size: 10px;
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 5px;
        """)
        header_layout.addWidget(badge)

        if self.record.get("explanation"):
            rec_badge = QLabel("🛠️ DOKTOR", self)
            rec_badge.setStyleSheet("background-color: #d97706; color: #ffffff; font-size: 10px; font-weight: bold; padding: 3px 8px; border-radius: 5px;")
            header_layout.addWidget(rec_badge)

        date_str = self.record.get("created_at", "")
        if date_str:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%d.%m %H:%M")
            except Exception:
                pass
        date_lbl = QLabel(date_str, self)
        date_lbl.setStyleSheet("color: #71717a; font-size: 11px; font-weight: 500;")
        header_layout.addWidget(date_lbl)

        header_layout.addStretch()

        is_fav = bool(self.record.get("is_favorite", 0))
        self.btn_fav = QPushButton("⭐" if is_fav else "☆", self)
        self.btn_fav.setFixedSize(26, 26)
        self.btn_fav.setCursor(Qt.PointingHandCursor)
        self.btn_fav.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {'#f59e0b' if is_fav else '#71717a'};
                font-size: 16px;
                border: none;
                padding: 0;
            }}
            QPushButton:hover {{ color: #f59e0b; background-color: rgba(245, 158, 11, 0.12); border-radius: 4px; }}
        """)
        self.btn_fav.clicked.connect(self._toggle_fav)
        header_layout.addWidget(self.btn_fav)

        btn_del = QPushButton("🗑️", self)
        btn_del.setFixedSize(26, 26)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton {
                background: transparent;
                font-size: 12px;
                border: none;
                padding: 0;
            }
            QPushButton:hover { background-color: #3f1d1d; border-radius: 4px; }
        """)
        btn_del.clicked.connect(self._delete_self)
        header_layout.addWidget(btn_del)

        main_layout.addLayout(header_layout)

        # 2. İÇERİK BÖLÜMÜ
        source_text = self.record.get("source_text", "")
        self.source_lbl = QLabel(source_text[:110] + "..." if len(source_text) > 110 else source_text, self)
        self.source_lbl.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            line-height: 1.35;
        """)
        self.source_lbl.setWordWrap(True)
        main_layout.addWidget(self.source_lbl)

        phonetic = self.record.get("phonetic", "")
        if phonetic and phonetic.strip().upper() not in ["YOK", "NONE", "NULL", ""]:
            pho_lbl = QLabel(phonetic[:50] + "..." if len(phonetic) > 50 else phonetic, self)
            pho_lbl.setStyleSheet("color: #34d399; font-size: 12px; font-weight: 600;")
            main_layout.addWidget(pho_lbl)

        trans_text = self.record.get("translated_text", "")
        self.meaning_lbl = QLabel(trans_text[:140] + "..." if len(trans_text) > 140 else trans_text, self)
        self.meaning_lbl.setStyleSheet("""
            color: #a1a1aa;
            font-size: 13px;
            line-height: 1.4;
        """)
        self.meaning_lbl.setWordWrap(True)
        main_layout.addWidget(self.meaning_lbl)

        main_layout.addStretch()

        # 3. ALT AKSİYON BUTONLARI
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)

        btn_speak = QPushButton("🔊 Dinle", self)
        btn_speak.setFixedHeight(32)
        btn_speak.setCursor(Qt.PointingHandCursor)
        btn_speak.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                padding: 0 12px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        btn_speak.clicked.connect(self._speak_normal)
        btn_bar.addWidget(btn_speak)

        btn_expand = QPushButton("🔍 Büyüt", self)
        btn_expand.setFixedHeight(32)
        btn_expand.setCursor(Qt.PointingHandCursor)
        btn_expand.setStyleSheet("""
            QPushButton {
                background-color: #18181b;
                color: #e4e4e7;
                border: 1px solid #27272a;
                font-size: 12px;
                font-weight: 600;
                padding: 0 12px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #27272a; border-color: #10b981; color: #ffffff; }
        """)
        btn_expand.clicked.connect(self._open_detail)
        btn_bar.addWidget(btn_expand)

        main_layout.addLayout(btn_bar)

    def mouseDoubleClickEvent(self, event):
        self._open_detail()

    def _open_detail(self):
        self.dialog = CardDetailDialog(self.record)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def _speak_normal(self):
        text = self.record.get("source_text", "")
        if text:
            tts_engine.speak_single(text, lang="en", slow=False)

    def _toggle_fav(self):
        rec_id = self.record.get("id")
        if rec_id:
            db.toggle_favorite(rec_id)
            is_fav = not bool(self.record.get("is_favorite", 0))
            self.record["is_favorite"] = 1 if is_fav else 0
            self.btn_fav.setText("⭐" if is_fav else "☆")
            self.btn_fav.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {'#f59e0b' if is_fav else '#71717a'};
                    font-size: 16px;
                    border: none;
                    padding: 0;
                }}
                QPushButton:hover {{ color: #f59e0b; }}
            """)
            self.favorite_toggled.emit(rec_id)

    def _delete_self(self):
        rec_id = self.record.get("id")
        if rec_id:
            db.delete_record(rec_id)
            self.deleted.emit(rec_id)
            self.setParent(None)
            self.deleteLater()


# ==========================================
# ANA UYGULAMA PENCERESİ
# ==========================================
class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ghost Translator & AI Desktop Co-Pilot")
        self.resize(1200, 850)
        self.setMinimumSize(850, 600)

        # Özel İkon (Görev Çubuğu ve Pencere)
        icon_path = str(BASE_DIR / "assets" / "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # QSS Yükle
        self._load_stylesheet()

        # Ana Arayüz
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(16)

        # Tab Widget
        self.tabs = QTabWidget(self)
        self.main_layout.addWidget(self.tabs)

        # Sekmeler
        self.tab_history = QWidget()
        self.tab_quiz = QWidget()
        self.tab_settings = QWidget()

        self.tabs.addTab(self.tab_history, "📚 Kelime Hafızası")
        self.tabs.addTab(self.tab_quiz, "🎯 Günlük Pratik (Flashcard)")
        self.tabs.addTab(self.tab_settings, "⚙️ Ayarlar ve Kısayollar")

        # Sekme İçeriklerini Kur
        self._setup_history_tab(self.tab_history)
        self._setup_quiz_tab(self.tab_quiz)
        self._setup_settings_tab(self.tab_settings)

        # Alt İmza Barı (Footer Signature)
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(10, 4, 10, 0)

        status_info = QLabel("⚡ Ghost Translator v2.0 • AI Desktop Co-Pilot", self)
        status_info.setStyleSheet("color: #71717a; font-size: 11px; font-weight: 500;")
        footer_layout.addWidget(status_info)

        footer_layout.addStretch()

        author_lbl = QLabel('Designed & Developed by <a href="https://github.com/Xgosh-Johan" style="color: #10b981; font-weight: bold; text-decoration: none;">Xgosh-Johan</a>', self)
        author_lbl.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        author_lbl.setOpenExternalLinks(True)
        author_lbl.setCursor(Qt.PointingHandCursor)
        footer_layout.addWidget(author_lbl)

        self.main_layout.addLayout(footer_layout)

        # Tab Değişimi Bağlantısı
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Başlangıçta Geçmişi ve Quiz'i Yükle
        self.load_history()
        self._load_next_quiz()

    def _on_tab_changed(self, index):
        if index == 0:
            self.load_history()
        elif index == 1:
            self._load_next_quiz()

    def changeEvent(self, event):
        """Pencere simge durumuna küçültüldüğünde (Minimize) görev çubuğundan kaybolup tepside bekler"""
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                event.ignore()
                QTimer.singleShot(0, self.hide)
                return
        super().changeEvent(event)

    def closeEvent(self, event):
        """Kapatıldığında tamamen çıkmak yerine tepside arka planda bekler"""
        event.ignore()
        self.hide()

    def _load_stylesheet(self):
        qss_path = BASE_DIR / "gui" / "style.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    # ==========================
    # SEKME 1: KELİME HAFIZASI
    # ==========================
    def _setup_history_tab(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Üst Araç Çubuğu
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("🔍 Kelime, cümle veya çeviri ara...")
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.search_input, stretch=4)

        self.btn_fav_filter = QPushButton("⭐ Sadece Favoriler", self)
        self.btn_fav_filter.setFixedHeight(40)
        self.btn_fav_filter.setCheckable(True)
        self.btn_fav_filter.setCursor(Qt.PointingHandCursor)
        self.btn_fav_filter.setProperty("class", "btn-secondary")
        self.btn_fav_filter.toggled.connect(self._on_fav_filter_toggled)
        toolbar.addWidget(self.btn_fav_filter, stretch=1)

        self.btn_clear_history = QPushButton("🗑️ Tüm Geçmişi Temizle", self)
        self.btn_clear_history.setFixedHeight(40)
        self.btn_clear_history.setCursor(Qt.PointingHandCursor)
        self.btn_clear_history.setStyleSheet("""
            QPushButton {
                background-color: #1f1f23;
                color: #f87171;
                border: 1px solid #7f1d1d;
                border-radius: 8px;
                font-weight: bold;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: #7f1d1d;
                color: #ffffff;
            }
        """)
        self.btn_clear_history.clicked.connect(self._confirm_and_clear_history)
        toolbar.addWidget(self.btn_clear_history)

        self.count_label = QLabel("0 Kayıt", self)
        self.count_label.setStyleSheet("color: #a1a1aa; font-weight: 500; font-size: 13px;")
        toolbar.addWidget(self.count_label)

        layout.addLayout(toolbar)

        # Grid Görünümü
        # Grid Görünümü
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(4, 8, 12, 16)
        self.grid_layout.setSpacing(14)
        self.grid_layout.setAlignment(Qt.AlignTop)
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setColumnStretch(2, 1)

        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area)

    def load_history(self):
        query = self.search_input.text().strip()
        favs_only = self.btn_fav_filter.isChecked()
        records = db.get_history(limit=150, search_query=query, favorites_only=favs_only)

        # Mevcut kartları temizle
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        columns = 3
        for index, record in enumerate(records):
            row = index // columns
            col = index % columns
            card = WordCardWidget(record, self)
            card.favorite_toggled.connect(self._on_card_favorite_toggled)
            card.deleted.connect(self._on_card_deleted)
            self.grid_layout.addWidget(card, row, col)

        self.count_label.setText(f"{len(records)} Kayıt")

    def _on_search_changed(self, text):
        self.load_history()

    def _on_fav_filter_toggled(self, checked):
        self.btn_fav_filter.setStyleSheet(
            "background-color: #d97706; color: #ffffff; font-weight: bold;" if checked else ""
        )
        self.load_history()

    def _on_card_favorite_toggled(self, record_id):
        if self.btn_fav_filter.isChecked():
            self.load_history()

    def _on_card_deleted(self, record_id):
        self.load_history()

    def _confirm_and_clear_history(self):
        records = db.get_history(limit=5000)
        if not records:
            QMessageBox.information(self, "Bilgi", "Temizlenecek geçmiş kaydı bulunmuyor.")
            return

        reply = QMessageBox.question(
            self, "Tüm Geçmişi Temizle",
            f"Toplam {len(records)} adet çeviri kaydı kalıcı olarak temizlenecektir.\n\n"
            "Tüm kayıtlar silinmeden önce 'Gecmis_Arsivi' klasörüne Markdown (.md) dosyası olarak yedeklenecektir.\n\n"
            "Onaylıyor musunuz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._export_markdown_and_clear(records)

    def _export_markdown_and_clear(self, records):
        try:
            archive_dir = BASE_DIR / "Gecmis_Arsivi"
            archive_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_path = archive_dir / f"Gecmis_Arsivi_{timestamp}.md"

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# 📚 Ghost Translator & AI Co-Pilot - Geçmiş Çeviri Arşivi\n\n")
                f.write(f"- **Oluşturulma Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write(f"- **Toplam Kayıt Sayısı:** {len(records)}\n\n")
                f.write("---\n\n")

                for idx, r in enumerate(records, 1):
                    ctx = r.get('context_type', 'SELECTION')
                    badge = "⚡ METİN SEÇİMİ" if ctx == "SELECTION" else ("💬 CHAT ÇEVİRİSİ" if ctx == "CHAT_OUT" else "🖼️ EKRAN KIRPMA (OCR)")
                    f.write(f"### {idx}. [{badge}] {r.get('source_text', '')}\n\n")
                    if r.get('phonetic'):
                        f.write(f"- **🗣️ Okunuşu:** `{r.get('phonetic')}`\n")
                    f.write(f"- **🇹🇷 Türkçe Anlamı:** {r.get('translated_text', '')}\n")
                    if r.get('explanation'):
                        f.write(f"- **🛠️ Çözüm Reçetesi:** {r.get('explanation')}\n")
                    f.write(f"\n---\n\n")

            db.clear_all()
            self.load_history()

            QMessageBox.information(
                self, "Arşivleme Başarılı",
                f"Tüm geçmiş başarıyla kaydedildi ve ekran temizlendi!\n\n📂 Dosya Yolu:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Markdown arşivi oluşturulurken hata: {e}")

    # ==========================
    # SEKME 2: QUIZ / FLASHCARD
    # ==========================
    def _setup_quiz_tab(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        header = QLabel("🎯 Spaced Repetition (Aralıklı Tekrar) & Günlük Pratik", self)
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #10b981;")
        layout.addWidget(header)

        desc = QLabel("SuperMemo SM-2 algoritması ile unutulma eğrisine göre kelimelerini pekiştir ve hafızada tut.", self)
        desc.setStyleSheet("color: #a1a1aa; font-size: 14px;")
        layout.addWidget(desc)

        # Flashcard Kutusu
        self.quiz_card = QFrame(self)
        self.quiz_card.setStyleSheet("""
            QFrame {
                background-color: #121215;
                border: 2px solid #059669;
                border-radius: 16px;
            }
        """)
        quiz_card_layout = QVBoxLayout(self.quiz_card)
        quiz_card_layout.setContentsMargins(40, 40, 40, 40)
        quiz_card_layout.setSpacing(16)

        self.quiz_word = QLabel("Kelime yükleniyor...", self)
        self.quiz_word.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        self.quiz_word.setAlignment(Qt.AlignCenter)
        self.quiz_word.setWordWrap(True)
        quiz_card_layout.addWidget(self.quiz_word)

        self.quiz_phonetic = QLabel("", self)
        self.quiz_phonetic.setStyleSheet("font-size: 15px; font-weight: 600; color: #34d399;")
        self.quiz_phonetic.setAlignment(Qt.AlignCenter)
        quiz_card_layout.addWidget(self.quiz_phonetic)

        self.quiz_meaning = QLabel("", self)
        self.quiz_meaning.setStyleSheet("""
            font-size: 18px;
            color: #e4e4e7;
            background-color: #1a1a1e;
            padding: 18px;
            border-radius: 10px;
            border-left: 3px solid #10b981;
        """)
        self.quiz_meaning.setWordWrap(True)
        self.quiz_meaning.setAlignment(Qt.AlignCenter)
        self.quiz_meaning.hide()
        quiz_card_layout.addWidget(self.quiz_meaning)

        layout.addWidget(self.quiz_card)

        # Kontrol Butonları
        self.btn_reveal = QPushButton("👁️ Anlamı & Okunuşu Gör", self)
        self.btn_reveal.setFixedHeight(48)
        self.btn_reveal.setStyleSheet("background-color: #059669; font-size: 14px; font-weight: bold;")
        self.btn_reveal.clicked.connect(self._reveal_quiz_answer)
        layout.addWidget(self.btn_reveal)

        # SM-2 Derecelendirme Butonları (Anlamı gördükten sonra açılır)
        self.sm2_layout = QHBoxLayout()
        self.sm2_layout.setSpacing(12)

        self.btn_sm2_hard = QPushButton("❌ Zor / Unuttum (Yarın)", self)
        self.btn_sm2_hard.setFixedHeight(44)
        self.btn_sm2_hard.setStyleSheet("background-color: #7f1d1d; color: #ffffff; font-weight: bold; border-radius: 8px;")
        self.btn_sm2_hard.clicked.connect(lambda: self._rate_sm2(1))
        self.sm2_layout.addWidget(self.btn_sm2_hard)

        self.btn_sm2_good = QPushButton("👍 Hatırladım (3 Gün)", self)
        self.btn_sm2_good.setFixedHeight(44)
        self.btn_sm2_good.setStyleSheet("background-color: #1e3a8a; color: #ffffff; font-weight: bold; border-radius: 8px;")
        self.btn_sm2_good.clicked.connect(lambda: self._rate_sm2(3))
        self.sm2_layout.addWidget(self.btn_sm2_good)

        self.btn_sm2_easy = QPushButton("⭐ Çok Kolay (1 Hafta)", self)
        self.btn_sm2_easy.setFixedHeight(44)
        self.btn_sm2_easy.setStyleSheet("background-color: #065f46; color: #ffffff; font-weight: bold; border-radius: 8px;")
        self.btn_sm2_easy.clicked.connect(lambda: self._rate_sm2(5))
        self.sm2_layout.addWidget(self.btn_sm2_easy)

        layout.addLayout(self.sm2_layout)
        self._toggle_sm2_buttons(False)

        layout.addStretch()
        self.current_quiz_record = None

    def _toggle_sm2_buttons(self, show=True):
        self.btn_sm2_hard.setVisible(show)
        self.btn_sm2_good.setVisible(show)
        self.btn_sm2_easy.setVisible(show)

    def _load_next_quiz(self):
        flashcards = db.get_flashcards(limit=1)
        if not flashcards:
            self.quiz_word.setText("Henüz kayıtlı kelime bulunamadı. F8 ile yeni kelimeler çevirdikçe burası dolacaktır!")
            self.quiz_phonetic.setText("")
            self.quiz_meaning.hide()
            self.current_quiz_record = None
            self._toggle_sm2_buttons(False)
            return

        self.current_quiz_record = flashcards[0]
        self.quiz_word.setText(self.current_quiz_record["source_text"])
        self.quiz_phonetic.setText("")
        self.quiz_meaning.setText(self.current_quiz_record["translated_text"])
        self.quiz_meaning.hide()
        self.btn_reveal.setEnabled(True)
        self.btn_reveal.show()
        self._toggle_sm2_buttons(False)

    def _reveal_quiz_answer(self):
        if self.current_quiz_record:
            self.quiz_phonetic.setText(self.current_quiz_record.get("phonetic", ""))
            self.quiz_meaning.show()
            self.btn_reveal.hide()
            self._toggle_sm2_buttons(True)
            tts_engine.speak_single(self.current_quiz_record["source_text"], lang="en")

    def _rate_sm2(self, quality):
        if self.current_quiz_record:
            db.update_sm2_review(self.current_quiz_record["id"], quality=quality)
            self._load_next_quiz()

    # ==========================
    # SEKME 3: AYARLAR
    # ==========================
    def _setup_settings_tab(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(16)

        scroll = QScrollArea(tab)
        scroll.setWidgetResizable(True)
        container = QWidget()
        form_layout = QVBoxLayout(container)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(18)

        # 0. Sistem & Başlangıç Ayarları
        sys_group = QFrame()
        sys_group.setProperty("class", "settings-card")
        sys_lay = QVBoxLayout(sys_group)
        sys_lay.setContentsMargins(22, 18, 22, 18)
        sys_lay.setSpacing(12)

        sys_title = QLabel("Sistem & Başlangıç Tercihleri", self)
        sys_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #10b981;")
        sys_lay.addWidget(sys_title)

        self.chk_autostart = QCheckBox("🖥️ Bilgisayar açıldığında arka planda sessizce başlat (Tepside hazır bekler)", self)
        self.chk_autostart.setChecked(config_manager.is_windows_autostart_enabled())
        sys_lay.addWidget(self.chk_autostart)

        self.chk_code_doctor = QCheckBox("🛠️ Kod & Syserr Doktoru (Hata satırlarında otomatik çözüm reçetesi sun)", self)
        self.chk_code_doctor.setChecked(config_manager.get("features", "code_doctor", True))
        sys_lay.addWidget(self.chk_code_doctor)

        form_layout.addWidget(sys_group)

        # 1. Gemini API Ayarları
        api_group = QFrame()
        api_group.setProperty("class", "settings-card")
        api_lay = QVBoxLayout(api_group)
        api_lay.setContentsMargins(22, 18, 22, 18)
        api_lay.setSpacing(14)

        api_title = QLabel("Google Gemini Yapay Zeka API Ayarları", self)
        api_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #10b981;")
        api_lay.addWidget(api_title)

        api_key_row = QHBoxLayout()
        api_key_lbl = QLabel("API Anahtarı:", self)
        api_key_lbl.setFixedWidth(160)
        api_key_lbl.setStyleSheet("color: #d4d4d8; font-weight: 500;")
        api_key_row.addWidget(api_key_lbl)

        self.input_api_key = QLineEdit(self)
        self.input_api_key.setFixedHeight(40)
        self.input_api_key.setEchoMode(QLineEdit.Password)
        self.input_api_key.setPlaceholderText("Google AI Studio'dan aldığınız API anahtarını buraya yapıştırın")
        self.input_api_key.setText(config_manager.get("api", "gemini_api_key", ""))
        api_key_row.addWidget(self.input_api_key)

        self.btn_show_key = QPushButton("Göster", self)
        self.btn_show_key.setFixedSize(80, 40)
        self.btn_show_key.setProperty("class", "btn-secondary")
        self.btn_show_key.setCursor(Qt.PointingHandCursor)
        self.btn_show_key.clicked.connect(self._toggle_api_visibility)
        api_key_row.addWidget(self.btn_show_key)
        api_lay.addLayout(api_key_row)

        model_row = QHBoxLayout()
        model_lbl = QLabel("Model Tercihi:", self)
        model_lbl.setFixedWidth(160)
        model_lbl.setStyleSheet("color: #d4d4d8; font-weight: 500;")
        model_row.addWidget(model_lbl)

        self.combo_model = QComboBox(self)
        self.combo_model.setFixedHeight(40)
        self.combo_model.addItems(["gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-flash-latest", "gemini-pro-latest"])
        current_model = config_manager.get("api", "gemini_model", "gemini-flash-lite-latest")
        idx = self.combo_model.findText(current_model)
        if idx >= 0:
            self.combo_model.setCurrentIndex(idx)
        model_row.addWidget(self.combo_model)
        model_row.addStretch()
        api_lay.addLayout(model_row)

        form_layout.addWidget(api_group)

        # 2. Kısayol Tuşları (Hotkeys)
        hotkey_group = QFrame()
        hotkey_group.setProperty("class", "settings-card")
        hk_lay = QVBoxLayout(hotkey_group)
        hk_lay.setContentsMargins(22, 18, 22, 18)
        hk_lay.setSpacing(14)

        hk_title = QLabel("Global Kısayol Tuşları (Hotkeys)", self)
        hk_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #10b981;")
        hk_lay.addWidget(hk_title)

        hk_grid = QVBoxLayout()
        hk_grid.setSpacing(10)
        self.input_hk_listen = self._create_hk_row(hk_grid, "Metin Seçip Çevir ve Dinle:", "listen", "f8")
        self.input_hk_chat = self._create_hk_row(hk_grid, "Tersine Chat / Yazışma Çevirisi:", "chat", "f9")
        self.input_hk_ocr = self._create_hk_row(hk_grid, "Ekran Kırpma (OCR Görsel Çeviri):", "ocr", "ctrl+shift+s")
        self.input_hk_gui = self._create_hk_row(hk_grid, "Ghost Translator Paneli Aç / Kapat:", "gui", "ctrl+shift+o")
        hk_lay.addLayout(hk_grid)

        form_layout.addWidget(hotkey_group)

        # 3. Seslendirme ve Telaffuz (TTS)
        tts_group = QFrame()
        tts_group.setProperty("class", "settings-card")
        tts_lay = QVBoxLayout(tts_group)
        tts_lay.setContentsMargins(22, 18, 22, 18)
        tts_lay.setSpacing(14)

        tts_title = QLabel("Seslendirme ve Telaffuz Ayarları (TTS)", self)
        tts_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #10b981;")
        tts_lay.addWidget(tts_title)

        voice_en_row = QHBoxLayout()
        voice_en_lbl = QLabel("İngilizce Ses Tercihi:", self)
        voice_en_lbl.setFixedWidth(160)
        voice_en_lbl.setStyleSheet("color: #d4d4d8; font-weight: 500;")
        voice_en_row.addWidget(voice_en_lbl)

        self.combo_voice_en = QComboBox(self)
        self.combo_voice_en.setFixedHeight(40)
        self.combo_voice_en.addItem("[Erkek] en-US-GuyNeural (Amerikan Erkek Sesi)", "en-US-GuyNeural")
        self.combo_voice_en.addItem("[Erkek] en-US-ChristopherNeural (Amerikan Erkek - Net)", "en-US-ChristopherNeural")
        self.combo_voice_en.addItem("[Kadın] en-US-JennyNeural (Amerikan Kadın Sesi)", "en-US-JennyNeural")
        cur_voice_en = config_manager.get("tts", "voice_en", "en-US-GuyNeural")
        for i in range(self.combo_voice_en.count()):
            if self.combo_voice_en.itemData(i) == cur_voice_en:
                self.combo_voice_en.setCurrentIndex(i)
                break
        voice_en_row.addWidget(self.combo_voice_en)
        voice_en_row.addStretch()
        tts_lay.addLayout(voice_en_row)

        voice_tr_row = QHBoxLayout()
        voice_tr_lbl = QLabel("Türkçe Ses Tercihi:", self)
        voice_tr_lbl.setFixedWidth(160)
        voice_tr_lbl.setStyleSheet("color: #d4d4d8; font-weight: 500;")
        voice_tr_row.addWidget(voice_tr_lbl)

        self.combo_voice_tr = QComboBox(self)
        self.combo_voice_tr.setFixedHeight(40)
        self.combo_voice_tr.addItem("[Erkek] tr-TR-AhmetNeural (Türkçe Erkek Sesi)", "tr-TR-AhmetNeural")
        self.combo_voice_tr.addItem("[Kadın] tr-TR-EmelNeural (Türkçe Kadın Sesi)", "tr-TR-EmelNeural")
        cur_voice_tr = config_manager.get("tts", "voice_tr", "tr-TR-AhmetNeural")
        for i in range(self.combo_voice_tr.count()):
            if self.combo_voice_tr.itemData(i) == cur_voice_tr:
                self.combo_voice_tr.setCurrentIndex(i)
                break
        voice_tr_row.addWidget(self.combo_voice_tr)
        voice_tr_row.addStretch()
        tts_lay.addLayout(voice_tr_row)

        opts_row = QVBoxLayout()
        opts_row.setSpacing(8)
        self.chk_speak_en = QCheckBox("İngilizce seçildiğinde önce İngilizce orijinalini de oku (İsteğe bağlı)", self)
        self.chk_speak_en.setChecked(config_manager.get("tts", "speak_english", False))
        self.chk_speak_tr = QCheckBox("Türkçe Anlamını Oku (Varsayılan Açık)", self)
        self.chk_speak_tr.setChecked(config_manager.get("tts", "speak_turkish", True))
        opts_row.addWidget(self.chk_speak_en)
        opts_row.addWidget(self.chk_speak_tr)
        tts_lay.addLayout(opts_row)

        form_layout.addWidget(tts_group)

        # 4. Mini HUD Bildirim Kartı
        hud_group = QFrame()
        hud_group.setProperty("class", "settings-card")
        hud_lay = QVBoxLayout(hud_group)
        hud_lay.setContentsMargins(22, 18, 22, 18)
        hud_lay.setSpacing(14)

        hud_title = QLabel("Mini HUD Bildirim Kartı Ayarları", self)
        hud_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #10b981;")
        hud_lay.addWidget(hud_title)

        self.chk_hud_enable = QCheckBox("Kısayola basıldığında ekranda şeffaf bildirim kartı göster", self)
        self.chk_hud_enable.setChecked(config_manager.get("hud", "enabled", True))
        hud_lay.addWidget(self.chk_hud_enable)

        pos_row = QHBoxLayout()
        pos_lbl = QLabel("Kart Konumu:", self)
        pos_lbl.setFixedWidth(160)
        pos_lbl.setStyleSheet("color: #d4d4d8; font-weight: 500;")
        pos_row.addWidget(pos_lbl)

        self.combo_hud_pos = QComboBox(self)
        self.combo_hud_pos.setFixedHeight(40)
        self.combo_hud_pos.addItem("Farenin İmlecinin Yanında", "cursor")
        self.combo_hud_pos.addItem("Ekranın Sağ Alt Köşesinde Sabit", "bottom_right")
        cur_pos = config_manager.get("hud", "position", "cursor")
        for i in range(self.combo_hud_pos.count()):
            if self.combo_hud_pos.itemData(i) == cur_pos:
                self.combo_hud_pos.setCurrentIndex(i)
                break
        pos_row.addWidget(self.combo_hud_pos)
        pos_row.addStretch()
        hud_lay.addLayout(pos_row)

        form_layout.addWidget(hud_group)

        # Kaydet Butonu
        self.btn_save_settings = QPushButton("💾 Tüm Ayarları Kaydet", self)
        self.btn_save_settings.setFixedHeight(48)
        self.btn_save_settings.setStyleSheet("background-color: #059669; font-size: 15px; font-weight: bold;")
        self.btn_save_settings.clicked.connect(self._save_all_settings)
        form_layout.addWidget(self.btn_save_settings)

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _create_hk_row(self, parent_layout, label_text, action_key, default_val):
        row = QHBoxLayout()
        lbl = QLabel(label_text, self)
        lbl.setFixedWidth(280)
        lbl.setStyleSheet("color: #d4d4d8; font-weight: 500;")
        row.addWidget(lbl)

        btn_recorder = HotkeyRecorderButton(action_key, label_text, default_val, self)
        row.addWidget(btn_recorder)

        parent_layout.addLayout(row)
        return btn_recorder

    def _toggle_api_visibility(self):
        if self.input_api_key.echoMode() == QLineEdit.Password:
            self.input_api_key.setEchoMode(QLineEdit.Normal)
            self.btn_show_key.setText("Gizle")
        else:
            self.input_api_key.setEchoMode(QLineEdit.Password)
            self.btn_show_key.setText("Göster")

    def _save_all_settings(self):
        # 0. Sistem
        config_manager.set_windows_autostart(self.chk_autostart.isChecked())
        config_manager.set("features", "code_doctor", self.chk_code_doctor.isChecked())

        # 1. API
        api_key = self.input_api_key.text().strip()
        config_manager.set("api", "gemini_api_key", api_key)
        config_manager.set("api", "gemini_model", self.combo_model.currentText())
        ai_engine.reload_api_key()

        # 2. Hotkeys
        hk_listen = self.input_hk_listen.current_hotkey
        hk_chat = self.input_hk_chat.current_hotkey
        hk_ocr = self.input_hk_ocr.current_hotkey
        hk_gui = self.input_hk_gui.current_hotkey

        hotkey_listener.update_hotkey("listen", hk_listen)
        hotkey_listener.update_hotkey("chat", hk_chat)
        hotkey_listener.update_hotkey("ocr", hk_ocr)
        hotkey_listener.update_hotkey("gui", hk_gui)

        # 3. TTS
        config_manager.set("tts", "voice_en", self.combo_voice_en.currentData())
        config_manager.set("tts", "voice_tr", self.combo_voice_tr.currentData())
        config_manager.set("tts", "speak_english", self.chk_speak_en.isChecked())
        config_manager.set("tts", "speak_turkish", self.chk_speak_tr.isChecked())

        # 4. HUD
        config_manager.set("hud", "enabled", self.chk_hud_enable.isChecked())
        config_manager.set("hud", "position", self.combo_hud_pos.currentData())

        QMessageBox.information(self, "Başarılı", "Tüm ayarlar ve kısayollar anında kaydedildi ve uygulandı!")

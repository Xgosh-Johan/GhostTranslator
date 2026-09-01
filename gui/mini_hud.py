import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QApplication, QFrame, QScrollArea
)
from PyQt5.QtGui import QColor, QFont, QCursor
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint

from config import config_manager
from core.tts_engine import tts_engine


class MiniHUD(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.current_source = ""
        self.current_phonetic = ""
        self.current_meaning = ""
        self.current_recipe = ""
        self.current_idiom = ""
        self.current_alternatives = ""
        self.current_examples = ""
        self.current_badge = "⚡ ÇEVİRİ"
        self.drag_position = None
        self.is_expanded = False

        self._init_ui()

        # Fade-In Animasyonu
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(180)

    def _init_ui(self):
        # Ana kart çerçevesi (OLED Deep Black + Emerald Vurgulu Çerçeve)
        self.container = QWidget(self)
        self.container.setObjectName("hudContainer")
        self.container.setStyleSheet("""
            QWidget#hudContainer {
                background-color: rgba(14, 14, 17, 0.98);
                border: 1.5px solid #10b981;
                border-radius: 14px;
            }
        """)

        # Derin gölge efekti
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 220))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

        self.card_layout = QVBoxLayout(self.container)
        self.card_layout.setContentsMargins(18, 14, 18, 14)
        self.card_layout.setSpacing(10)

        # 1. ÜST BAŞLIK VE BUTONLAR SATIRI
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.badge_label = QLabel("⚡ ÇEVİRİ", self)
        self.badge_label.setStyleSheet("""
            background-color: #059669;
            color: #ffffff;
            font-size: 11px;
            font-weight: bold;
            padding: 3px 10px;
            border-radius: 5px;
        """)
        header_layout.addWidget(self.badge_label)

        self.phonetic_label = QLabel("", self)
        self.phonetic_label.setStyleSheet("""
            background-color: rgba(16, 185, 129, 0.12);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.25);
            font-size: 12px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 5px;
        """)
        header_layout.addWidget(self.phonetic_label)

        # 💡 Deyim Rozeti (Kompakt modda hemen fark edilir)
        self.idiom_chip = QLabel("", self)
        self.idiom_chip.setStyleSheet("""
            background-color: rgba(245, 158, 11, 0.16);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.35);
            font-size: 11px;
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 5px;
        """)
        header_layout.addWidget(self.idiom_chip)
        self.idiom_chip.hide()

        header_layout.addStretch()

        # 1.0x Normal Dinle Butonu
        self.btn_speak = QPushButton("🔊 Dinle", self)
        self.btn_speak.setCursor(Qt.PointingHandCursor)
        self.btn_speak.setFixedHeight(28)
        self.btn_speak.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                padding: 0 10px;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        self.btn_speak.clicked.connect(self._on_speak_clicked)
        header_layout.addWidget(self.btn_speak)

        # 0.5x Yavaş Dinle Butonu
        self.btn_slow = QPushButton("🐢 Yavaş", self)
        self.btn_slow.setCursor(Qt.PointingHandCursor)
        self.btn_slow.setFixedHeight(28)
        self.btn_slow.setStyleSheet("""
            QPushButton {
                background-color: #1f1f23;
                color: #d4d4d8;
                border: 1px solid #27272a;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 8px;
            }
            QPushButton:hover { background-color: #27272a; border-color: #10b981; color: #ffffff; }
        """)
        self.btn_slow.clicked.connect(self._on_slow_clicked)
        header_layout.addWidget(self.btn_slow)

        # 🔍 BÜYÜT / KÜÇÜLT BUTONU (Aynı Kart İçinde Genişletme)
        self.btn_expand = QPushButton("🔍 Büyüt", self)
        self.btn_expand.setCursor(Qt.PointingHandCursor)
        self.btn_expand.setFixedHeight(28)
        self.btn_expand.setStyleSheet("""
            QPushButton {
                background-color: #1f1f23;
                color: #34d399;
                border: 1px solid #059669;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                padding: 0 10px;
            }
            QPushButton:hover { background-color: #059669; color: #ffffff; }
        """)
        self.btn_expand.clicked.connect(self._on_expand_clicked)
        header_layout.addWidget(self.btn_expand)

        # Kapat Butonu (✕)
        self.btn_close = QPushButton("✕", self)
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setToolTip("Kapat (ESC)")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #1f1f23;
                color: #a1a1aa;
                border: 1px solid #27272a;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #7f1d1d;
                color: #f87171;
                border-color: #ef4444;
            }
        """)
        self.btn_close.clicked.connect(self.hide)
        header_layout.addWidget(self.btn_close)

        self.card_layout.addLayout(header_layout)

        # İnce Çizgi
        self.sep_line = QFrame()
        self.sep_line.setFrameShape(QFrame.HLine)
        self.sep_line.setStyleSheet("background-color: #222226; height: 1px; border: none;")
        self.card_layout.addWidget(self.sep_line)

        # ==========================================
        # GÖRÜNÜM A: KOMPAKT MİNİ GÖRÜNÜM
        # ==========================================
        self.compact_widget = QWidget(self.container)
        c_layout = QVBoxLayout(self.compact_widget)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(8)

        self.source_label = QLabel("", self.compact_widget)
        self.source_label.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
            line-height: 1.45;
        """)
        self.source_label.setWordWrap(True)
        self.source_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        c_layout.addWidget(self.source_label)

        self.meaning_label = QLabel("", self.compact_widget)
        self.meaning_label.setStyleSheet("""
            color: #e4e4e7;
            font-size: 14px;
            line-height: 1.55;
            background-color: rgba(22, 22, 26, 0.75);
            padding: 10px 12px;
            border-radius: 8px;
            border-left: 3.5px solid #10b981;
        """)
        self.meaning_label.setWordWrap(True)
        self.meaning_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        c_layout.addWidget(self.meaning_label)

        self.card_layout.addWidget(self.compact_widget)

        # ==========================================
        # GÖRÜNÜM B: BÜYÜTÜLMÜŞ ÇİFT SÜTUNLU PARALEL OKUMA GÖRÜNÜMÜ
        # ==========================================
        self.expanded_widget = QWidget(self.container)
        exp_layout = QVBoxLayout(self.expanded_widget)
        exp_layout.setContentsMargins(0, 4, 0, 0)
        exp_layout.setSpacing(10)

        # 1. Yan yana çift kutu (Orijinal & Çeviri)
        split_layout = QHBoxLayout()
        split_layout.setSpacing(12)

        # Sol Kutu (İngilizce)
        left_box = QFrame(self.expanded_widget)
        left_box.setStyleSheet("background-color: #121216; border: 1px solid #232328; border-radius: 10px;")
        l_lay = QVBoxLayout(left_box)
        l_lay.setContentsMargins(12, 10, 12, 10)
        l_lay.setSpacing(6)
        l_title = QLabel("🇬🇧 ORİJİNAL METİN", left_box)
        l_title.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: bold;")
        l_lay.addWidget(l_title)

        l_scroll = QScrollArea(left_box)
        l_scroll.setWidgetResizable(True)
        l_scroll.setStyleSheet("background: transparent; border: none;")
        self.exp_src_label = QLabel("", l_scroll)
        self.exp_src_label.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 600; line-height: 1.55;")
        self.exp_src_label.setWordWrap(True)
        self.exp_src_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        l_scroll.setWidget(self.exp_src_label)
        l_lay.addWidget(l_scroll)
        split_layout.addWidget(left_box, stretch=1)

        # Sağ Kutu (Türkçe)
        right_box = QFrame(self.expanded_widget)
        right_box.setStyleSheet("background-color: #121216; border: 1px solid #232328; border-left: 3px solid #10b981; border-radius: 10px;")
        r_lay = QVBoxLayout(right_box)
        r_lay.setContentsMargins(12, 10, 12, 10)
        r_lay.setSpacing(6)
        r_title = QLabel("🇹🇷 TÜRKÇE ÇEVİRİSİ & ANLAMI", right_box)
        r_title.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold;")
        r_lay.addWidget(r_title)

        r_scroll = QScrollArea(right_box)
        r_scroll.setWidgetResizable(True)
        r_scroll.setStyleSheet("background: transparent; border: none;")
        self.exp_tr_label = QLabel("", r_scroll)
        self.exp_tr_label.setStyleSheet("color: #f4f4f5; font-size: 14px; line-height: 1.6;")
        self.exp_tr_label.setWordWrap(True)
        self.exp_tr_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        r_scroll.setWidget(self.exp_tr_label)
        r_lay.addWidget(r_scroll)
        split_layout.addWidget(right_box, stretch=1)

        exp_layout.addLayout(split_layout, stretch=1)

        # 2. 💡 DEYİM / PHRASAL VERB KARTI (Varsa)
        self.exp_idiom_card = QFrame(self.expanded_widget)
        self.exp_idiom_card.setStyleSheet("background-color: rgba(30, 24, 16, 0.9); border: 1.5px solid #d97706; border-radius: 8px;")
        idiom_lay = QVBoxLayout(self.exp_idiom_card)
        idiom_lay.setContentsMargins(10, 7, 10, 7)
        idiom_lay.setSpacing(3)
        idiom_title = QLabel("💡 DEYİM / PHRASAL VERB ANALİZİ", self.exp_idiom_card)
        idiom_title.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: bold;")
        idiom_lay.addWidget(idiom_title)
        self.exp_idiom_label = QLabel("", self.exp_idiom_card)
        self.exp_idiom_label.setStyleSheet("color: #fef3c7; font-size: 12px; line-height: 1.4;")
        self.exp_idiom_label.setWordWrap(True)
        self.exp_idiom_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        idiom_lay.addWidget(self.exp_idiom_label)
        exp_layout.addWidget(self.exp_idiom_card)
        self.exp_idiom_card.hide()

        # 3. 🎭 NATIVE ALTERNATİFLER KARTI (Varsa)
        self.exp_alt_card = QFrame(self.expanded_widget)
        self.exp_alt_card.setStyleSheet("background-color: rgba(18, 24, 38, 0.9); border: 1.5px solid #3b82f6; border-radius: 8px;")
        alt_lay = QVBoxLayout(self.exp_alt_card)
        alt_lay.setContentsMargins(10, 7, 10, 7)
        alt_lay.setSpacing(3)
        alt_title = QLabel("🎭 NATIVE ALTERNATİFLER (\"Bunu Başka Nasıl Söylersin?\")", self.exp_alt_card)
        alt_title.setStyleSheet("color: #60a5fa; font-size: 11px; font-weight: bold;")
        alt_lay.addWidget(alt_title)
        self.exp_alt_label = QLabel("", self.exp_alt_card)
        self.exp_alt_label.setStyleSheet("color: #dbeafe; font-size: 12px; line-height: 1.4;")
        self.exp_alt_label.setWordWrap(True)
        self.exp_alt_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        alt_lay.addWidget(self.exp_alt_label)
        exp_layout.addWidget(self.exp_alt_card)
        self.exp_alt_card.hide()

        # 4. 📖 KELİME ANATOMİSİ VE ÖRNEK CÜMLELER (Tek kelime ise)
        self.exp_ex_card = QFrame(self.expanded_widget)
        self.exp_ex_card.setStyleSheet("background-color: rgba(16, 28, 22, 0.9); border: 1.5px solid #059669; border-radius: 8px;")
        ex_lay = QVBoxLayout(self.exp_ex_card)
        ex_lay.setContentsMargins(10, 7, 10, 7)
        ex_lay.setSpacing(3)
        ex_title = QLabel("📖 KELİME ANATOMİSİ VE ÖRNEK CÜMLELER", self.exp_ex_card)
        ex_title.setStyleSheet("color: #34d399; font-size: 11px; font-weight: bold;")
        ex_lay.addWidget(ex_title)
        self.exp_ex_label = QLabel("", self.exp_ex_card)
        self.exp_ex_label.setStyleSheet("color: #ecfdf5; font-size: 12px; line-height: 1.4;")
        self.exp_ex_label.setWordWrap(True)
        self.exp_ex_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ex_lay.addWidget(self.exp_ex_label)
        exp_layout.addWidget(self.exp_ex_card)
        self.exp_ex_card.hide()

        # Alt Kopyalama Butonları
        exp_bar = QHBoxLayout()
        exp_bar.setSpacing(10)

        btn_copy = QPushButton("📋 Türkçeyi Kopyala", self.expanded_widget)
        btn_copy.setFixedHeight(32)
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #18181b;
                color: #34d399;
                border: 1px solid #059669;
                font-size: 11px;
                font-weight: 600;
                border-radius: 6px;
                padding: 0 12px;
            }
            QPushButton:hover { background-color: #059669; color: #ffffff; }
        """)
        btn_copy.clicked.connect(self._copy_tr)
        exp_bar.addWidget(btn_copy)
        exp_bar.addStretch()

        exp_layout.addLayout(exp_bar)
        self.card_layout.addWidget(self.expanded_widget)
        self.expanded_widget.hide()

        # ==========================================
        # 🛠️ KOD / SYSERR ÇÖZÜM REÇETESİ KUTUSU
        # ==========================================
        self.recipe_card = QFrame(self.container)
        self.recipe_card.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 25, 18, 0.9);
                border: 1.5px solid #d97706;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        rec_lay = QVBoxLayout(self.recipe_card)
        rec_lay.setContentsMargins(10, 8, 10, 8)
        rec_lay.setSpacing(4)
        rec_title = QLabel("🛠️ HATA TEŞHİSİ VE ÇÖZÜM REÇETESİ", self.recipe_card)
        rec_title.setStyleSheet("color: #f59e0b; font-size: 12px; font-weight: bold;")
        rec_lay.addWidget(rec_title)

        self.recipe_label = QLabel("", self.recipe_card)
        self.recipe_label.setStyleSheet("color: #fef3c7; font-size: 13px; line-height: 1.45;")
        self.recipe_label.setWordWrap(True)
        self.recipe_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        rec_lay.addWidget(self.recipe_label)
        self.card_layout.addWidget(self.recipe_card)
        self.recipe_card.hide()

        # Bilgi Notu
        self.hint_lbl = QLabel("📌 Kapatmak için [✕] veya ESC'ye basın, geniş okumak için [🔍 Büyüt]'e tıklayın.", self.container)
        self.hint_lbl.setStyleSheet("color: #52525b; font-size: 11px; margin-top: 2px;")
        self.card_layout.addWidget(self.hint_lbl)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(self.container)

    # ==========================
    # KARTI FAREYLE TAŞIMA (DRAG & DROP)
    # ==========================
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
            self.hide()
        else:
            super().keyPressEvent(event)

    def _on_speak_clicked(self):
        # Türkçe seçildiyse İngilizce çeviriyi oku, İngilizce seçildiyse orijinal İngilizceyi oku
        text_to_speak = self.current_meaning if getattr(self, "detected_lang", "EN") == "TR" else self.current_source
        if text_to_speak:
            tts_engine.speak_single(text_to_speak, lang="en", slow=False)

    def _on_slow_clicked(self):
        text_to_speak = self.current_meaning if getattr(self, "detected_lang", "EN") == "TR" else self.current_source
        if text_to_speak:
            tts_engine.speak_single(text_to_speak, lang="en", slow=True)

    def _copy_tr(self):
        if self.current_meaning:
            QApplication.clipboard().setText(self.current_meaning)

    def _on_expand_clicked(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            # BÜYÜTÜLMÜŞ MODA GEÇ
            self.btn_expand.setText("🔍 Küçült")
            self.compact_widget.hide()
            self.expanded_widget.show()
            self.exp_src_label.setText(self.current_source)
            self.exp_tr_label.setText(self.current_meaning)

            extra_count = 0
            if self.current_idiom:
                self.exp_idiom_label.setText(self.current_idiom)
                self.exp_idiom_card.show()
                extra_count += 1
            else:
                self.exp_idiom_card.hide()

            if self.current_alternatives:
                self.exp_alt_label.setText(self.current_alternatives)
                self.exp_alt_card.show()
                extra_count += 1
            else:
                self.exp_alt_card.hide()

            if self.current_examples:
                self.exp_ex_label.setText(self.current_examples)
                self.exp_ex_card.show()
                extra_count += 1
            else:
                self.exp_ex_card.hide()

            target_h = 520 + (extra_count * 55)
            self.setFixedSize(940, target_h)
            self.container.setFixedSize(920, target_h - 20)

            # Ekranın tam ortasına al
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(
                    geo.center().x() - 470,
                    geo.center().y() - (target_h // 2)
                )
        else:
            # KOMPAKT MODA GERİ DÖN
            self.btn_expand.setText("🔍 Büyüt")
            self.expanded_widget.hide()
            self.compact_widget.show()
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)
            self.container.setMinimumSize(0, 0)
            self.container.setMaximumSize(16777215, 16777215)

            target_w = 640 if len(self.current_source) > 120 else 520
            self.setFixedWidth(target_w)
            self.container.setFixedWidth(target_w - 20)
            self.container.adjustSize()
            self.layout().activate()
            self.adjustSize()
            self._position_hud()

    def show_info(self, source_text, meaning, phonetic="", recipe="", badge="⚡ ÇEVİRİ", idiom="", alternatives="", examples=""):
        if not config_manager.get("hud", "enabled", True):
            return

        self.current_source = source_text
        self.current_meaning = meaning
        self.current_phonetic = phonetic
        self.current_recipe = recipe
        self.current_idiom = idiom
        self.current_alternatives = alternatives
        self.current_examples = examples
        self.current_badge = badge
        self.detected_lang = "TR" if ("TR ➔ EN" in badge or "TR➔EN" in badge) else "EN"

        self.badge_label.setText(badge)
        
        if phonetic and phonetic.strip().upper() not in ["YOK", "NONE", "NULL", ""]:
            self.phonetic_label.setText(phonetic)
            self.phonetic_label.show()
        else:
            self.phonetic_label.hide()

        if idiom and idiom.strip().upper() not in ["YOK", "NONE", "NULL", ""]:
            short_idiom = idiom.split(":")[0].strip() if ":" in idiom else "DEYİM"
            self.idiom_chip.setText(f"💡 {short_idiom}")
            self.idiom_chip.show()
        else:
            self.idiom_chip.hide()

        # Varsayılan kompakt mod
        self.is_expanded = False
        self.btn_expand.setText("🔍 Büyüt")
        self.expanded_widget.hide()
        self.compact_widget.show()
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self.container.setMinimumSize(0, 0)
        self.container.setMaximumSize(16777215, 16777215)

        total_len = len(source_text) + len(meaning)
        target_width = 640 if total_len > 120 else 520

        self.setFixedWidth(target_width)
        self.container.setFixedWidth(target_width - 20)

        self.source_label.setText(source_text)
        self.meaning_label.setText(meaning)

        if recipe:
            self.recipe_label.setText(recipe)
            self.recipe_card.show()
        else:
            self.recipe_card.hide()

        self.container.adjustSize()
        self.layout().activate()
        self.adjustSize()
        self._position_hud()

        self.setWindowOpacity(0.0)
        self.show()
        self.anim.stop()
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

    def _position_hud(self):
        pos_mode = config_manager.get("hud", "position", "cursor")
        screen = QApplication.primaryScreen()
        if not screen:
            return

        screen_geo = screen.availableGeometry()

        if pos_mode == "cursor":
            cursor_pos = QCursor.pos()
            x = cursor_pos.x() + 25
            y = cursor_pos.y() + 25

            if x + self.width() > screen_geo.right():
                x = cursor_pos.x() - self.width() - 15
            if y + self.height() > screen_geo.bottom():
                y = cursor_pos.y() - self.height() - 15
        else:
            x = screen_geo.right() - self.width() - 24
            y = screen_geo.bottom() - self.height() - 24

        self.move(QPoint(max(screen_geo.left() + 15, x), max(screen_geo.top() + 15, y)))

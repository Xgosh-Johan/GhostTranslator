"""
======================================================================
 Ghost Translator & AI Desktop Co-Pilot
 Author & Creator: Xgosh-Johan (https://github.com/Xgosh-Johan)
 License: MIT License
 Version: 2.0.0
======================================================================
"""
__author__ = "Xgosh-Johan"
__github__ = "https://github.com/Xgosh-Johan"
__version__ = "2.0.0"

import sys
import os
from pathlib import Path

# 1. Çalışma Dizinini Kesin Olarak Proje Klasörüne Al (Windows Başlangıç Koruması)
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# 2. Windows Qt Platform Plugin (qwindows.dll) Yolunu Kesin Olarak Tanımla
try:
    import PyQt5
    qt_plugins = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
    if os.path.exists(qt_plugins):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_plugins
        platforms_path = os.path.join(qt_plugins, "platforms")
        if hasattr(os, 'add_dll_directory') and os.path.exists(platforms_path):
            os.add_dll_directory(platforms_path)
except Exception:
    pass

import re
import ctypes
import threading
import traceback
from datetime import datetime

# 3. Windows Görev Çubuğunda Python İkonu Yerine Özel İkonun Görünmesini Sağla
try:
    myappid = 'ghost.translator.desktop.copilot.v2'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# ==========================================
# 🚨 GLOBAL SYSERR LOG SİSTEMİ (Metin2 Tarzı)
# ==========================================
SYSERR_FILE = BASE_DIR / "syserr.txt"

def write_syserr(msg):
    try:
        timestamp = datetime.now().strftime("%m%d %H:%M:%S")
        with open(SYSERR_FILE, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"SYSERR: {timestamp} :: {msg}\n")
    except Exception:
        pass

def global_excepthook(exc_type, exc_value, exc_traceback):
    err_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    write_syserr(f"CRASH (Main Thread):\n{err_str}")
    print(f"[SYSERR] {err_str}", file=sys.stderr)

def thread_excepthook(args):
    err_str = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
    write_syserr(f"CRASH (Thread {args.thread.name}):\n{err_str}")
    print(f"[SYSERR] {err_str}", file=sys.stderr)

sys.excepthook = global_excepthook
if hasattr(threading, 'excepthook'):
    threading.excepthook = thread_excepthook

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QObject, pyqtSignal, Qt, qInstallMessageHandler, QtMsgType

from config import config_manager, BASE_DIR
from database import db
from core.tts_engine import tts_engine
from core.ai_engine import ai_engine
from core.text_handler import text_handler
from core.ocr_engine import SnippingOverlay
from core.hotkey_listener import hotkey_listener
from gui.app_window import AppWindow
from gui.mini_hud import MiniHUD


class AppSignals(QObject):
    # source, meaning, phonetic, recipe, badge, idiom, alternatives, examples
    show_hud_signal = pyqtSignal(str, str, str, str, str, str, str, str)
    toggle_gui_signal = pyqtSignal()
    refresh_history_signal = pyqtSignal()
    start_ocr_signal = pyqtSignal()


class GhostTranslatorService:
    def __init__(self, app):
        self.app = app
        self.signals = AppSignals()

        # UI Bileşenleri
        self.window = AppWindow()
        self.hud = MiniHUD()
        self.snip_overlay = SnippingOverlay()

        # Sinyal Bağlantıları
        self.signals.show_hud_signal.connect(self.hud.show_info)
        self.signals.toggle_gui_signal.connect(self._toggle_gui)
        self.signals.refresh_history_signal.connect(self.window.load_history)
        self.signals.start_ocr_signal.connect(self.snip_overlay.start_selection)
        self.snip_overlay.snip_image_completed.connect(self._on_ocr_completed)

        # Sistem Tepsisi (System Tray)
        self._init_tray()

        # Kısayol Dinleyicisi
        self._init_hotkeys()

        # Sessiz Başlangıç: Pencere masaüstüne fırlamaz, arka planda hazır bekler
        self.window.hide()

    def _init_tray(self):
        self.tray_icon = QSystemTrayIcon(self.app)

        # Özel Zümrüt İkon
        icon_path = str(BASE_DIR / "assets" / "icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.green)
            self.tray_icon.setIcon(QIcon(pixmap))

        self.tray_icon.setToolTip("Ghost Translator & AI Desktop Co-Pilot (Arka Planda Aktif)")

        tray_menu = QMenu()

        act_open = QAction("📖 Ghost Translator Paneli", tray_menu)
        act_open.triggered.connect(self._toggle_gui)
        tray_menu.addAction(act_open)

        tray_menu.addSeparator()

        act_listen = QAction(f"🔊 Seçili Metni Çevir ({config_manager.get('hotkeys', 'listen', 'F8').upper()})", tray_menu)
        act_listen.triggered.connect(self.handle_listen_action)
        tray_menu.addAction(act_listen)

        act_chat = QAction(f"💬 Chat Çevirisi ({config_manager.get('hotkeys', 'chat', 'F9').upper()})", tray_menu)
        act_chat.triggered.connect(self.handle_chat_action)
        tray_menu.addAction(act_chat)

        act_ocr = QAction(f"🖼️ Ekran Kırpma OCR ({config_manager.get('hotkeys', 'ocr', 'CTRL+SHIFT+S').upper()})", tray_menu)
        act_ocr.triggered.connect(self.handle_ocr_action)
        tray_menu.addAction(act_ocr)

        tray_menu.addSeparator()

        act_exit = QAction("❌ Programı Tamamen Kapat", tray_menu)
        act_exit.triggered.connect(self._exit_app)
        tray_menu.addAction(act_exit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self._toggle_gui()

    def _init_hotkeys(self):
        hotkey_listener.register_callback("listen", self.handle_listen_action)
        hotkey_listener.register_callback("chat", self.handle_chat_action)
        hotkey_listener.register_callback("ocr", self.handle_ocr_action)
        hotkey_listener.register_callback("gui", self.handle_gui_action)
        hotkey_listener.start()

    def _toggle_gui(self):
        if self.window.isVisible() and not self.window.isMinimized():
            self.window.hide()
        else:
            self.window.load_history()
            self.window._load_next_quiz()
            self.window.showMaximized()
            self.window.activateWindow()
            self.window.raise_()

    def handle_gui_action(self):
        self.signals.toggle_gui_signal.emit()

    # --- MODÜL A: SEÇİLİ METNİ ÇEVİR & DİNLE ---
    def handle_listen_action(self):
        def _worker():
            selected_text = text_handler.get_selected_text()
            if not selected_text:
                print("[Ghost] Seçili metin bulunamadı.")
                return

            print(f"[Ghost] Seçili Metin: {selected_text}")
            result = ai_engine.analyze_incoming_text(selected_text)

            phonetic = result.get("phonetic", "")
            meaning = result.get("meaning", "")
            recipe = result.get("recipe", "")
            speech_tr = result.get("speech_tr", meaning)
            detected_lang = result.get("detected_lang", "EN")
            idiom = result.get("idiom", "")
            alternatives = result.get("alternatives", "")
            examples = result.get("examples", "")

            # Veritabanına kaydet
            db.add_record(
                source_text=selected_text,
                translated_text=meaning,
                phonetic=phonetic,
                context_type="SELECTION",
                explanation=recipe,
                idiom=idiom,
                alternatives=alternatives,
                examples=examples
            )

            # Mini HUD Göster
            badge = "⚡ TR ➔ EN" if detected_lang == "TR" else "⚡ EN ➔ TR"
            self.signals.show_hud_signal.emit(
                selected_text, meaning, phonetic, recipe, badge, idiom, alternatives, examples
            )
            self.signals.refresh_history_signal.emit()

            # Akıllı Seslendirme Sırası
            if detected_lang == "TR":
                # Türkçe seçildi -> Hedef İngilizce karşılığını Amerikan sesiyle oku
                clean_target = speech_tr if (speech_tr and speech_tr.lower() != selected_text.lower()) else meaning
                clean_target = re.sub(r'[/\\()\[\]]+', ', ', clean_target).strip()
                tts_engine.speak_single(clean_target, lang="en")
            else:
                # İngilizce seçildi -> Hedef Türkçe anlamı Türkçe sesiyle oku
                clean_target = speech_tr if (speech_tr and speech_tr.lower() != selected_text.lower()) else meaning
                clean_target = re.sub(r'[/\\()\[\]]+', ', ', clean_target).strip()
                tts_engine.speak_single(clean_target, lang="tr")

        threading.Thread(target=_worker, daemon=True).start()

    # --- MODÜL B: TERSİNE CHAT / JARGON ÇEVİRİSİ ---
    def handle_chat_action(self):
        def _worker():
            selected_text = text_handler.get_selected_text()
            if not selected_text:
                print("[Ghost] Chat için seçili metin bulunamadı.")
                return

            print(f"[Ghost] Chat Türkçe Girdi: {selected_text}")
            english_translation = ai_engine.translate_chat_reverse(selected_text)

            if english_translation:
                text_handler.replace_selected_text(english_translation)

                db.add_record(
                    source_text=selected_text,
                    translated_text=english_translation,
                    phonetic="",
                    context_type="CHAT_OUT"
                )

                self.signals.show_hud_signal.emit(
                    selected_text, f"💬 Çeviri: {english_translation}", "", "", "💬 CHAT ÇEVİRİ", "", "", ""
                )
                self.signals.refresh_history_signal.emit()
                tts_engine.speak_single(english_translation, lang="en")

        threading.Thread(target=_worker, daemon=True).start()

    # --- MODÜL C: EKRAN KIRPMA (OCR) ---
    def handle_ocr_action(self):
        self.signals.start_ocr_signal.emit()

    def _on_ocr_completed(self, img):
        if not img:
            return

        def _worker():
            print("[Ghost] Kırpılan görsel yapay zeka ile analiz ediliyor...")
            result = ai_engine.analyze_image(img)
            if not result:
                print("[Ghost] Görsel analizi başarısız oldu.")
                return

            source_text = result.get("source_text", "Görsel Metni")
            phonetic = result.get("phonetic", "")
            meaning = result.get("meaning", "")
            recipe = result.get("recipe", "")
            speech_tr = result.get("speech_tr", meaning)
            detected_lang = result.get("detected_lang", "EN")

            db.add_record(
                source_text=source_text,
                translated_text=meaning,
                phonetic=phonetic,
                context_type="OCR",
                explanation=recipe
            )

            badge = "🖼️ OCR (TR➔EN)" if detected_lang == "TR" else "🖼️ OCR (EN➔TR)"
            self.signals.show_hud_signal.emit(source_text, meaning, phonetic, recipe, badge, "", "", "")
            self.signals.refresh_history_signal.emit()

            if detected_lang == "TR":
                target = meaning if meaning else source_text
                tts_engine.speak_single(target, lang="en")
            else:
                clean_target = speech_tr if (speech_tr and speech_tr.lower() != source_text.lower()) else meaning
                clean_target = re.sub(r'[/\\()\[\]]+', ', ', clean_target).strip()
                tts_engine.speak_single(clean_target, lang="tr")

        threading.Thread(target=_worker, daemon=True).start()

    def _exit_app(self):
        hotkey_listener.stop()
        tts_engine.stop()
        self.tray_icon.hide()
        self.app.quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icon_path = str(BASE_DIR / "assets" / "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    service = GhostTranslatorService(app)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

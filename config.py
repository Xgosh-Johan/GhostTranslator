import os
import sys
import json
import winreg
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "api": {
        "gemini_api_key": "",
        "gemini_model": "gemini-flash-lite-latest"
    },
    "hotkeys": {
        "listen": "f8",
        "chat": "f9",
        "ocr": "ctrl+shift+s",
        "gui": "ctrl+shift+o"
    },
    "tts": {
        "engine": "edge-tts",
        "voice_en": "en-US-GuyNeural",
        "voice_tr": "tr-TR-AhmetNeural",
        "rate_en": "+0%",
        "rate_tr": "+10%",
        "pyttsx3_rate": 180,
        "pause_between_sec": 0.25,
        "speak_english": False,
        "speak_turkish": True
    },
    "hud": {
        "enabled": True,
        "position": "cursor"
    },
    "features": {
        "auto_start": False,
        "start_silent": True,
        "code_doctor": True,
        "chat_multi_style": False
    },
    "ui": {
        "dark_mode": True,
        "start_minimized": True
    }
}


class ConfigManager:
    def __init__(self, filepath=CONFIG_FILE):
        self.filepath = filepath
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.filepath):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                for k, v in data.items():
                    if isinstance(v, dict) and k in merged:
                        merged[k].update(v)
                    else:
                        merged[k] = v
                return merged
        except Exception:
            return DEFAULT_CONFIG.copy()

    def save_config(self, config=None):
        if config is None:
            config = self.config
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Kaydetme hatası: {e}")

    def get(self, section, key=None, default=None):
        if key is None:
            return self.config.get(section, default)
        return self.config.get(section, {}).get(key, default)

    def set(self, section, key, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save_config()

    # ==========================
    # WINDOWS AUTO-START REGISTRY
    # ==========================
    @staticmethod
    def is_windows_autostart_enabled():
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            val, _ = winreg.QueryValueEx(key, "GhostTranslator")
            winreg.CloseKey(key)
            return bool(val)
        except Exception:
            return False

    @staticmethod
    def set_windows_autostart(enable=True):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            if enable:
                pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
                main_script = str(BASE_DIR / "main.pyw")
                cmd = f'"{pythonw_path}" "{main_script}"'
                winreg.SetValueEx(key, "GhostTranslator", 0, winreg.REG_SZ, cmd)
                print(f"[Config] Windows Başlangıcına Eklendi: {cmd}")
            else:
                try:
                    winreg.DeleteValue(key, "GhostTranslator")
                    print("[Config] Windows Başlangıcından Kaldırıldı")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"[Config] Windows başlangıç kayıt hatası: {e}")
            return False


config_manager = ConfigManager()

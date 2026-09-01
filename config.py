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
            # 1. Yöntem: Windows Registry (Kayıt Defteri)
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            if enable:
                python_dir = Path(sys.executable).parent
                pythonw_candidate = python_dir / "pythonw.exe"
                pythonw_path = str(pythonw_candidate) if pythonw_candidate.exists() else sys.executable
                main_script = str(BASE_DIR / "main.pyw")
                cmd = f'"{pythonw_path}" "{main_script}"'
                winreg.SetValueEx(key, "GhostTranslator", 0, winreg.REG_SZ, cmd)
                print(f"[Config] Windows Başlangıcına Eklendi (Registry): {cmd}")
            else:
                try:
                    winreg.DeleteValue(key, "GhostTranslator")
                    print("[Config] Windows Başlangıcından Kaldırıldı (Registry)")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)

            # 2. Yöntem: Windows Başlangıç Klasörü Garantisi (shell:startup)
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                startup_dir = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
                if startup_dir.exists():
                    bat_file = startup_dir / "GhostTranslator_Autostart.bat"
                    if enable:
                        with open(bat_file, "w", encoding="utf-8") as f:
                            f.write(f'@echo off\ncd /d "{BASE_DIR}"\nstart pythonw main.pyw\nexit\n')
                        print(f"[Config] Windows Başlangıç Klasörüne Eklendi: {bat_file}")
                    else:
                        if bat_file.exists():
                            bat_file.unlink()
                            print(f"[Config] Windows Başlangıç Klasöründen Silindi: {bat_file}")

            return True
        except Exception as e:
            print(f"[Config] Windows başlangıç kayıt hatası: {e}")
            return False


config_manager = ConfigManager()

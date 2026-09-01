import threading
import keyboard
from pynput import mouse
from config import config_manager


class HotkeyListener:
    def __init__(self):
        self.registered_hooks = []
        self.callbacks = {}
        self.mouse_listener = None
        self.is_running = False
        self.lock = threading.Lock()

    def register_callback(self, action_name, callback):
        """Action isimleri: 'listen', 'chat', 'ocr', 'gui'"""
        self.callbacks[action_name] = callback

    def bind_all_hotkeys(self):
        with self.lock:
            self.unbind_all_hotkeys()

            hotkeys = config_manager.get("hotkeys", default={})

            # 1. Klavye Kısayollarını Bağla
            for action_name, hotkey_str in hotkeys.items():
                if action_name in self.callbacks and hotkey_str:
                    clean_hk = hotkey_str.lower().strip()
                    # Eğer fare butonu değilse klavye kütüphanesine bağla
                    if not clean_hk.startswith("mouse") and clean_hk not in ["xbutton1", "xbutton2", "middle"]:
                        try:
                            callback = self.callbacks[action_name]
                            hook = keyboard.add_hotkey(clean_hk, callback, suppress=False)
                            self.registered_hooks.append((clean_hk, hook))
                            print(f"[Hotkey] Klavye Kısayolu Bağlandı: {action_name} -> [{clean_hk}]")
                        except Exception as e:
                            print(f"[Hotkey] Kısayol bağlama hatası ({action_name}: {clean_hk}): {e}")

            # Chat için ek F9 & Alt+W garantisi
            if "chat" in self.callbacks:
                chat_cb = self.callbacks["chat"]
                chat_hk = hotkeys.get("chat", "").lower()
                for alias in ["f9", "alt+w"]:
                    if alias != chat_hk and not chat_hk.startswith("mouse"):
                        try:
                            hook = keyboard.add_hotkey(alias, chat_cb, suppress=False)
                            self.registered_hooks.append((alias, hook))
                        except Exception:
                            pass

            # 2. Fare Butonlarını (Yan Tuşlar, Orta Tuş) Global Dinle
            self._start_mouse_listener(hotkeys)

    def _start_mouse_listener(self, hotkeys):
        # Fare dinleyicisini başlat
        def on_click(x, y, button, pressed):
            if not pressed:
                return

            btn_name = ""
            if button == mouse.Button.x1:
                btn_name = "xbutton1"
            elif button == mouse.Button.x2:
                btn_name = "xbutton2"
            elif button == mouse.Button.middle:
                btn_name = "middle"

            if btn_name:
                for action_name, hk_str in hotkeys.items():
                    if hk_str.lower().strip() in [btn_name, f"mouse_{btn_name}"] and action_name in self.callbacks:
                        print(f"[Hotkey] Fare Yan Tuşu Tetiklendi: {action_name} -> [{btn_name}]")
                        self.callbacks[action_name]()

        try:
            if self.mouse_listener:
                self.mouse_listener.stop()
            self.mouse_listener = mouse.Listener(on_click=on_click)
            self.mouse_listener.daemon = True
            self.mouse_listener.start()
        except Exception as e:
            print(f"[Hotkey] Fare dinleyicisi başlatılamadı: {e}")

    def unbind_all_hotkeys(self):
        for hotkey_str, hook in self.registered_hooks:
            try:
                keyboard.remove_hotkey(hook)
            except Exception:
                try:
                    keyboard.remove_hotkey(hotkey_str)
                except Exception:
                    pass
        self.registered_hooks.clear()

        if self.mouse_listener:
            try:
                self.mouse_listener.stop()
            except Exception:
                pass
            self.mouse_listener = None

    def update_hotkey(self, action_name, new_hotkey_str):
        with self.lock:
            config_manager.set("hotkeys", action_name, new_hotkey_str.lower().strip())
            self.bind_all_hotkeys()
            return True

    def start(self):
        self.is_running = True
        self.bind_all_hotkeys()

    def stop(self):
        self.is_running = False
        self.unbind_all_hotkeys()


hotkey_listener = HotkeyListener()

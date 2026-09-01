import time
import pyperclip
import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.03


class TextHandler:
    @staticmethod
    def get_selected_text(timeout=0.35):
        """
        Kullanıcının seçtiği metni panoya (Ctrl+C) alıp okur.
        """
        old_clipboard = pyperclip.paste()
        try:
            pyperclip.copy("")
        except Exception:
            pass

        # Tuşların serbest kalması için kısa bekleme
        time.sleep(0.08)

        # Ctrl+C
        pyautogui.hotkey('ctrl', 'c')

        start_time = time.time()
        selected_text = ""
        while time.time() - start_time < timeout:
            time.sleep(0.03)
            current = pyperclip.paste()
            if current:
                selected_text = current
                break

        if not selected_text:
            try:
                pyperclip.copy(old_clipboard)
            except Exception:
                pass
            return ""

        return selected_text.strip()

    @staticmethod
    def replace_selected_text(new_text):
        """
        Seçili olan metni silip yerine 'new_text' yapıştırır (Ctrl+V).
        """
        if not new_text:
            return False

        try:
            pyperclip.copy(new_text)
            time.sleep(0.06)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.05)
            return True
        except Exception as e:
            print(f"[TextHandler] Metin yapıştırma hatası: {e}")
            return False


text_handler = TextHandler()

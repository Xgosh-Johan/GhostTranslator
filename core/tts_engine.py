import os
import sys
import re
import time
import asyncio
import tempfile
import threading
import ctypes
from pathlib import Path

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

from config import config_manager


class TTSEngine:
    def __init__(self):
        self._current_process_id = 0
        self._play_thread = None
        self._audio_cache = {}
        self._lock = threading.Lock()

    def stop(self):
        """Mevcut çalan sesi anında keser"""
        self._current_process_id += 1
        try:
            ctypes.windll.winmm.mciSendStringW("stop ghost_audio", None, 0, 0)
            ctypes.windll.winmm.mciSendStringW("close ghost_audio", None, 0, 0)
        except Exception:
            pass

    def _play_mp3_safe(self, mp3_path, req_id):
        """Windows MCI ile sıfır gecikmeli, iptal edilebilir MP3 çalma"""
        try:
            # Önceki ses varsa kapat
            ctypes.windll.winmm.mciSendStringW("stop ghost_audio", None, 0, 0)
            ctypes.windll.winmm.mciSendStringW("close ghost_audio", None, 0, 0)

            if req_id != self._current_process_id:
                return

            cmd_open = f'open "{mp3_path}" type mpegvideo alias ghost_audio'
            ctypes.windll.winmm.mciSendStringW(cmd_open, None, 0, 0)
            ctypes.windll.winmm.mciSendStringW("play ghost_audio", None, 0, 0)

            # Ses çalarken döngüde kontrol et (yeni istek gelirse anında durdur)
            status_buf = ctypes.create_unicode_buffer(128)
            while req_id == self._current_process_id:
                ctypes.windll.winmm.mciSendStringW("status ghost_audio mode", status_buf, 128, 0)
                mode = status_buf.value.strip().lower()
                if mode in ["stopped", ""]:
                    break
                time.sleep(0.04)

            ctypes.windll.winmm.mciSendStringW("close ghost_audio", None, 0, 0)
        except Exception as e:
            print(f"[TTS] MCI Çalma hatası: {e}")

    async def _generate_edge_tts(self, text, voice, rate="+0%"):
        fd, output_file = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(output_file)
        return output_file

    def _clean_speech_text(self, text):
        if not text:
            return ""
        # 1. Unicode Emojileri ve piktogramları tamamen temizle
        emoji_pattern = re.compile(
            r'[\U00010000-\U0010ffff\u2600-\u27BF\u2300-\u23FF\u2B50\u2B55\u200d\uFE0F\u20E3\u2190-\u21FF\u2900-\u297F]+',
            flags=re.UNICODE
        )
        clean = emoji_pattern.sub(' ', text)

        # 2. Markdown ve dekoratif sembolleri temizle
        clean = re.sub(r'[*_#`"\'\[\](){}~<>=|\\]+', ' ', clean)
        clean = re.sub(r'[\r\n\t]+', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def _get_audio_file(self, text, voice, rate="+0%"):
        # Metni emojilerden ve sembollerden arındır
        clean_text = self._clean_speech_text(text)
        if not clean_text:
            return None

        # Çok uzun paragraflarda TTS motorunun boğulmaması için ilk 2500 karakter
        if len(clean_text) > 2500:
            clean_text = clean_text[:2500]

        cache_key = f"{voice}_{rate}_{clean_text}"
        if cache_key in self._audio_cache and os.path.exists(self._audio_cache[cache_key]):
            return self._audio_cache[cache_key]

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            temp_file = loop.run_until_complete(
                asyncio.wait_for(self._generate_edge_tts(clean_text, voice, rate=rate), timeout=20.0)
            )
            loop.close()

            if temp_file and os.path.exists(temp_file):
                self._audio_cache[cache_key] = temp_file
                return temp_file
        except Exception as e:
            print(f"[TTS] Edge-TTS üretim hatası: {e}")
        return None

    def speak_single(self, text, lang="en", slow=False):
        """Tekil seslendirme (Asenkron & Asla Donmaz)"""
        if not text or not text.strip():
            return

        self._current_process_id += 1
        req_id = self._current_process_id

        def _worker():
            rate = "-35%" if slow else ("+0%" if lang == "en" else "+10%")
            if lang == "en":
                voice = config_manager.get("tts", "voice_en", "en-US-GuyNeural")
            else:
                voice = config_manager.get("tts", "voice_tr", "tr-TR-AhmetNeural")

            audio_file = self._get_audio_file(text, voice, rate=rate)
            if audio_file and req_id == self._current_process_id:
                self._play_mp3_safe(audio_file, req_id)

        threading.Thread(target=_worker, daemon=True).start()

    def speak_bilingual(self, text_en, text_tr):
        """Önce İngilizce ardından Türkçe seslendirme"""
        if not text_en and not text_tr:
            return

        self._current_process_id += 1
        req_id = self._current_process_id

        def _worker():
            voice_en = config_manager.get("tts", "voice_en", "en-US-GuyNeural")
            voice_tr = config_manager.get("tts", "voice_tr", "tr-TR-AhmetNeural")

            # 1. İngilizce Çal
            if text_en:
                file_en = self._get_audio_file(text_en, voice_en, "+0%")
                if file_en and req_id == self._current_process_id:
                    self._play_mp3_safe(file_en, req_id)

            # Kısa nefes payı
            if req_id != self._current_process_id:
                return
            time.sleep(0.25)

            # 2. Türkçe Çal
            if text_tr and req_id == self._current_process_id:
                file_tr = self._get_audio_file(text_tr, voice_tr, "+10%")
                if file_tr and req_id == self._current_process_id:
                    self._play_mp3_safe(file_tr, req_id)

        threading.Thread(target=_worker, daemon=True).start()


tts_engine = TTSEngine()

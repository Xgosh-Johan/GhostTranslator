import io
import os
import wave
import time
import threading
import sounddevice as sd
import numpy as np
import speech_recognition as sr
from difflib import SequenceMatcher

from config import config_manager


class VoiceCoach:
    def __init__(self):
        self.sample_rate = 16000
        self.channels = 1
        self.is_recording = False
        self.recorded_chunks = []
        self.stream = None
        self.lock = threading.Lock()
        self.recognizer = sr.Recognizer()

    def _audio_callback(self, indata, frames, time_info, status):
        if self.is_recording:
            self.recorded_chunks.append(indata.copy())

    def start_recording(self):
        """Kullanıcı butona bastığında kaydı başlatır"""
        with self.lock:
            if self.is_recording:
                return False
            self.recorded_chunks = []
            self.is_recording = True
            try:
                self.stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype='int16',
                    callback=self._audio_callback
                )
                self.stream.start()
                print("[VoiceCoach] Kayıt başladı...")
                return True
            except Exception as e:
                print(f"[VoiceCoach] Kayıt başlatma hatası: {e}")
                self.is_recording = False
                return False

    def stop_and_evaluate(self, target_text):
        """Kullanıcı tekrar butona bastığında kaydı durdurur ve anında puanlar"""
        with self.lock:
            if not self.is_recording:
                return {
                    "score": 0,
                    "feedback": "Kayıt zaten durdurulmuş."
                }
            self.is_recording = False
            try:
                if self.stream:
                    self.stream.stop()
                    self.stream.close()
                    self.stream = None
            except Exception as e:
                print(f"[VoiceCoach] Stream kapatma hatası: {e}")

        if not self.recorded_chunks:
            return {
                "score": 0,
                "feedback": "Hiç ses kaydedilemedi. Lütfen mikrofona konuşun."
            }

        try:
            # Ses parçalarını birleştir
            audio_np = np.concatenate(self.recorded_chunks, axis=0)
            wav_bytes = self._numpy_to_wav_bytes(audio_np)

            # SpeechRecognition ile sesi metne dök (STT)
            audio_data = sr.AudioData(wav_bytes, self.sample_rate, 2)
            try:
                recognized_text = self.recognizer.recognize_google(audio_data, language="en-US")
                print(f"[VoiceCoach] Algılanan Ses: '{recognized_text}' | Hedef: '{target_text}'")
            except sr.UnknownValueError:
                return {
                    "score": 15,
                    "feedback": "Ses algılandı ancak kelimeler net anlaşılamadı. Lütfen biraz daha net ve yüksek sesle söyleyin."
                }
            except Exception as e:
                print(f"[VoiceCoach] STT Hatası: {e}")
                recognized_text = ""

            if not recognized_text:
                return {
                    "score": 20,
                    "feedback": "Ses net duyulamadı, lütfen tekrar deneyin."
                }

            # Hedef metin ile söylenen metni karşılaştır
            clean_target = self._clean_text(target_text)
            clean_rec = self._clean_text(recognized_text)

            similarity = SequenceMatcher(None, clean_target, clean_rec).ratio()
            score = int(similarity * 100)

            # Detaylı geri bildirim
            if score >= 90:
                feedback = f"🌟 Mükemmel Telaffuz! (%{score}) - Algılanan: '{recognized_text}'"
            elif score >= 70:
                feedback = f"👍 Gayet İyi! (%{score}) - Algılanan: '{recognized_text}'. Hedefe çok yakınsın."
            elif score >= 45:
                feedback = f"⚡ Biraz Daha Pratik (%{score}) - Algılanan: '{recognized_text}'. Vurguları daha net yapabilirsin."
            else:
                feedback = f"⚠️ Algılanan: '{recognized_text}'. Hedef metni dinleyip tekrar dene."

            return {
                "score": score,
                "recognized": recognized_text,
                "feedback": feedback
            }
        except Exception as e:
            print(f"[VoiceCoach] Değerlendirme hatası: {e}")
            return {
                "score": 0,
                "feedback": f"Hata oluştu: {e}"
            }

    def _clean_text(self, text):
        import re
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        return ' '.join(text.split())

    def _numpy_to_wav_bytes(self, audio_data):
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
        return buf.getvalue()


voice_coach = VoiceCoach()

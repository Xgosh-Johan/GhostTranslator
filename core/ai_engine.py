import json
import re
import io
import base64
import requests
from config import config_manager


class AIEngine:
    def __init__(self):
        pass

    def reload_api_key(self):
        return bool(config_manager.get("api", "gemini_api_key", "").strip())

    def _call_gemini(self, prompt):
        """
        Ultra hızlı ve kararlı doğrudan Google Gemini REST API çağrısı.
        """
        api_key = config_manager.get("api", "gemini_api_key", "").strip()
        if not api_key:
            return None, "API Anahtarı eksik. Lütfen Ayarlar sekmesinden API anahtarınızı girin."

        user_model = config_manager.get("api", "gemini_model", "gemini-flash-lite-latest")
        candidate_models = [user_model, "gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-flash-latest", "gemini-pro-latest"]
        seen_models = []
        for m in candidate_models:
            if m and m not in seen_models:
                seen_models.append(m)

        last_error = ""
        for model_name in seen_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
                headers = {"Content-Type": "application/json"}
                r = requests.post(url, json=payload, headers=headers, timeout=12)
                if r.status_code == 200:
                    data = r.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip(), None
                else:
                    last_error = f"HTTP {r.status_code}: {r.text}"
            except Exception as e:
                last_error = str(e)

        return None, last_error

    def analyze_incoming_text(self, text):
        """
        Modül A: Seçilen metni iki yönlü analiz eder.
        Kod/Syserr hatası tespit ederse otomatik 'RECETE' üretir.
        """
        prompt = f"""
Sen geliştiriciler (C++, Python, MySQL, Metin2), oyuncular ve dil öğrenenler için çalışan ultra hızlı, iki yönlü çalışan uzman bir AI Co-Pilot ve çeviri asistanısın.

Girdi Metni: "{text}"

GÖREVLERİN:
1. Girdi dilini tespit et (İngilizce mi, Türkçe mi?).

2. EĞER GİRDİ BİR HATA, KOD, SYSERR VEYA EXCEPTION İSE (Örn: nullptr, segfault, assertion, syserr log, compiler error):
   - "ANLAM:" alanına hatanın Türkçe net açıklamasını yaz.
   - "RECETE:" alanına geliştiricinin ne yapması gerektiğini 1-2 nokta atışı Türkçe maddeyle yaz.
   - "SES_TR:" alanına hatanın özet seslendirmesini yaz.
   - "DIL:" alanına EN yaz.
   - "DEYIM:", "ALTERNATIF:", "ORNEKLER:" alanlarına YOK yaz.

3. EĞER GİRDİ NORMAL İNGİLİZCE İSE:
   - "FONETİK:" alanına İngilizce metnin okunuşunu yaz.
   - "ANLAM:" alanına girdideki metnin TAM, EKSİKSİZ ve DOĞAL Türkçe çevirisini yaz.
   - "SES_TR:" alanına KESİNLİKLE VE SADECE Türkçe çevirinin metnini yaz (Örn: "Ghost Translator" için SES_TR: Hayalet Çevirmen yaz. Asla İngilizce orijinali veya okunuşu yazma!).
   - "RECETE:" YOK yaz.
   - "DIL:" alanına EN yaz.
   - "DEYIM:" Metinde bir deyim (idiom) veya kalıp fiil (phrasal verb) varsa, o kalıbı ve Türkçe mecazi anlamını yaz (Örn: "Bite the bullet: Zor bir duruma katlanmak / Dişini sıkmak"). Yoksa YOK yaz.
   - "ALTERNATIF:" Ana dili İngilizce olanların (Native) bunu günlük veya iş hayatında doğalca söyleyebileceği 1-2 alternatif ifade yaz (Örn: "• I'm completely exhausted."). Yoksa YOK yaz.
   - "ORNEKLER:" Eğer girdi TEK BİR KELİME ise (cümle değilse), kelimenin türünü (İsim/Fiil/Sıfat) ve içinde geçtiği 2 kısa İngilizce-Türkçe örnek cümle yaz. Cümle ise YOK yaz.

4. EĞER GİRDİ TÜRKÇE İSE:
   - "ANLAM:" alanına tam ve eksiksiz İNGİLİZCE çevirisini yaz.
   - "SES_TR:" alanına sesli okunacak net İNGİLİZCE çeviriyi yaz.
   - "FONETİK:" alanına İngilizce çevirinin okunuşunu yaz.
   - "RECETE:" YOK yaz.
   - "DIL:" alanına TR yaz.
   - "DEYIM:" Türkçe girdi bir deyimse İngilizce karşılığını veya deyimsel açıklamasını yaz. Yoksa YOK yaz.
   - "ALTERNATIF:" İngilizce çevirinin 1-2 doğal/yerel alternatif söyleyişini yaz. Yoksa YOK yaz.
   - "ORNEKLER:" Eğer girdi TEK BİR KELİME ise, İngilizce karşılığıyla 2 kısa örnek cümle yaz. Yoksa YOK yaz.

Format:
DIL: <EN veya TR>
FONETİK: <fonetik_okunus>
ANLAM: <tam_ceviri>
RECETE: <hata_cozum_recetesi_veya_YOK>
SES_TR: <sesli_okunacak_hedef_ceviri>
DEYIM: <deyim_veya_YOK>
ALTERNATIF: <alternatifler_veya_YOK>
ORNEKLER: <ornek_cumleler_veya_YOK>
"""

        response_text, error = self._call_gemini(prompt)

        if not response_text:
            return {
                "detected_lang": "EN",
                "phonetic": "[Bağlantı Hatası]",
                "meaning": f"Çeviri yapılamadı: {error}",
                "recipe": "",
                "speech_tr": "Yapay zeka bağlantısı kurulamadı.",
                "idiom": "",
                "alternatives": "",
                "examples": ""
            }

        try:
            lang_match = re.search(r'DIL:\s*([^\n\r]*)', response_text, re.IGNORECASE)
            phonetic_match = re.search(r'FONETİK:\s*([^\n\r]*)', response_text, re.IGNORECASE)
            meaning_match = re.search(r'ANLAM:\s*(.*?)(?=\n\s*RECETE:|\n\s*SES_TR:|\n\s*DEYIM:|\n\s*ALTERNATIF:|\n\s*ORNEKLER:|\Z)', response_text, re.DOTALL | re.IGNORECASE)
            recipe_match = re.search(r'RECETE:\s*(.*?)(?=\n\s*SES_TR:|\n\s*DEYIM:|\n\s*ALTERNATIF:|\n\s*ORNEKLER:|\Z)', response_text, re.DOTALL | re.IGNORECASE)
            speech_match = re.search(r'SES_TR:\s*(.*?)(?=\n\s*DEYIM:|\n\s*ALTERNATIF:|\n\s*ORNEKLER:|\Z)', response_text, re.DOTALL | re.IGNORECASE)
            idiom_match = re.search(r'DEYIM:\s*(.*?)(?=\n\s*ALTERNATIF:|\n\s*ORNEKLER:|\Z)', response_text, re.DOTALL | re.IGNORECASE)
            alt_match = re.search(r'ALTERNATIF:\s*(.*?)(?=\n\s*ORNEKLER:|\Z)', response_text, re.DOTALL | re.IGNORECASE)
            ex_match = re.search(r'ORNEKLER:\s*(.*?)(?=\Z)', response_text, re.DOTALL | re.IGNORECASE)

            detected_lang = lang_match.group(1).strip().upper() if lang_match else "EN"
            phonetic = phonetic_match.group(1).strip() if phonetic_match else ""
            meaning = meaning_match.group(1).strip() if meaning_match else response_text
            recipe = recipe_match.group(1).strip() if recipe_match and "YOK" not in recipe_match.group(1).upper() else ""
            
            # Hedef Seslendirme: Girdi EN ise daima Türkçe Çeviriyi (meaning) al
            if detected_lang == "EN":
                speech_tr = meaning
            else:
                speech_tr = meaning if meaning else (speech_match.group(1).strip() if speech_match else text)

            idiom_raw = idiom_match.group(1).strip() if idiom_match else ""
            idiom = idiom_raw if idiom_raw and "YOK" not in idiom_raw.upper() else ""

            alt_raw = alt_match.group(1).strip() if alt_match else ""
            alternatives = alt_raw if alt_raw and "YOK" not in alt_raw.upper() else ""

            ex_raw = ex_match.group(1).strip() if ex_match else ""
            examples = ex_raw if ex_raw and "YOK" not in ex_raw.upper() else ""

            speech_tr = re.sub(r'[*_#`]', '', speech_tr).strip()
            meaning = re.sub(r'[*_#`]', '', meaning).strip()
            recipe = re.sub(r'[*_#`]', '', recipe).strip()
            idiom = re.sub(r'[*#`]', '', idiom).strip()
            alternatives = re.sub(r'[*#`]', '', alternatives).strip()
            examples = re.sub(r'[*#`]', '', examples).strip()

            return {
                "detected_lang": detected_lang,
                "phonetic": phonetic,
                "meaning": meaning,
                "recipe": recipe,
                "speech_tr": speech_tr,
                "idiom": idiom,
                "alternatives": alternatives,
                "examples": examples
            }
        except Exception as e:
            return {
                "detected_lang": "EN",
                "phonetic": "",
                "meaning": response_text,
                "recipe": "",
                "speech_tr": response_text,
                "idiom": "",
                "alternatives": "",
                "examples": ""
            }

    def analyze_image(self, pil_image):
        """
        Kırpılan görseli Gemini Vision ile analiz eder.
        """
        api_key = config_manager.get("api", "gemini_api_key", "").strip()
        if not api_key:
            return {
                "source_text": "Görsel Metni",
                "detected_lang": "EN",
                "phonetic": "[API Key Eksik]",
                "meaning": "Lütfen API anahtarınızı girin.",
                "recipe": "",
                "speech_tr": "API anahtarı eksik."
            }

        try:
            buffered = io.BytesIO()
            pil_image.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            prompt = """
Sen oyun (Metin2 vb.) ve yazılım ekranlarını okuyan uzman bir OCR ve çeviri asistanısın.
Görseldeki metni dikkatle oku ve analiz et:

1. Görseldeki metnin tamamını "ORIJINAL:" alanına yaz.
2. Girdi dilini "DIL:" alanına EN veya TR olarak belirt.
3. EĞER GİRDİ İNGİLİZCE İSE:
   - "ANLAM:" alanına tam Türkçe çevirisini yaz.
   - "SES_TR:" alanına seslendirilecek net Türkçe çeviriyi yaz.
   - "FONETİK:" alanına İngilizce orijinalin okunuşunu yaz.
4. EĞER GİRDİ TÜRKÇE İSE:
   - "ANLAM:" alanına tam İngilizce çevirisini yaz.
   - "SES_TR:" alanına seslendirilecek net İngilizce çeviriyi yaz.
   - "FONETİK:" alanına İngilizce çevirinin okunuşunu yaz.
5. Eğer metin bir hata veya syserr ise "RECETE:" alanına çözümünü yaz, yoksa YOK yaz.

Format:
ORIJINAL: <gorseldeki_yazi>
DIL: <EN veya TR>
FONETİK: <fonetik_okunus>
ANLAM: <hedef_dilde_ceviri>
RECETE: <cozum_recetesi_veya_YOK>
SES_TR: <seslendirilecek_hedef_ceviri>
"""
            models = ["gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-flash-latest"]
            for model_name in models:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": prompt},
                                {
                                    "inlineData": {
                                        "mimeType": "image/png",
                                        "data": img_b64
                                    }
                                }
                            ]
                        }]
                    }
                    headers = {"Content-Type": "application/json"}
                    r = requests.post(url, json=payload, headers=headers, timeout=12)
                    if r.status_code == 200:
                        data = r.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                resp = parts[0].get("text", "").strip()
                                orig_m = re.search(r'ORIJINAL:\s*(.*?)(?=\n\s*DIL:|\Z)', resp, re.DOTALL | re.IGNORECASE)
                                lang_m = re.search(r'DIL:\s*([^\n\r]*)', resp, re.IGNORECASE)
                                pho_m = re.search(r'FONETİK:\s*([^\n\r]*)', resp, re.IGNORECASE)
                                mean_m = re.search(r'ANLAM:\s*(.*?)(?=\n\s*RECETE:|\n\s*SES_TR:|\Z)', resp, re.DOTALL | re.IGNORECASE)
                                rec_m = re.search(r'RECETE:\s*(.*?)(?=\n\s*SES_TR:|\Z)', resp, re.DOTALL | re.IGNORECASE)
                                speech_m = re.search(r'SES_TR:\s*(.*?)(?=\Z)', resp, re.DOTALL | re.IGNORECASE)

                                orig = orig_m.group(1).strip() if orig_m else "Görsel Metni"
                                detected_lang = lang_m.group(1).strip().upper() if lang_m else "EN"
                                phonetic = pho_m.group(1).strip() if pho_m else ""
                                meaning = mean_m.group(1).strip() if mean_m else resp
                                recipe = rec_m.group(1).strip() if rec_m and "YOK" not in rec_m.group(1).upper() else ""
                                speech_tr = speech_m.group(1).strip() if speech_m else meaning

                                # Güvenlik: Eğer speech_tr yanlışlıkla orijinal İngilizce kaldıysa meaning'e eşitle
                                if speech_tr.lower() == orig.lower() and detected_lang == "EN":
                                    speech_tr = meaning

                                return {
                                    "source_text": orig,
                                    "detected_lang": detected_lang,
                                    "phonetic": phonetic,
                                    "meaning": meaning,
                                    "recipe": recipe,
                                    "speech_tr": speech_tr
                                }
                except Exception as e:
                    print(f"[AI Vision] Hata ({model_name}): {e}")
        except Exception as e:
            print(f"[AI Vision] Görsel hazırlama hatası: {e}")

        return None

    def translate_chat_reverse(self, text):
        """
        Modül B: Akıllı İki Yönlü Yerinde Çeviri (TR <-> EN).
        Girdi Türkçe ise -> Doğal ve net İngilizceye çevirip yerine yapıştırır.
        Girdi İngilizce ise -> Doğal ve net Türkçeye çevirip yerine yapıştırır.
        """
        prompt = f"""
Sen iki yönlü çalışan (Türkçe <-> İngilizce) uzman bir metin ve chat çevirmenisin.

Girdi Metni: "{text}"

GÖREVİN:
1. Girdinin dilini tespit et.
2. Eğer girdi TÜRKÇE ise: Doğrudan ve eksiksiz olarak en doğal İNGİLİZCE karşılığına çevir.
3. Eğer girdi İNGİLİZCE ise: Doğrudan ve eksiksiz olarak en doğal TÜRKÇE karşılığına çevir.

KURALLAR:
- SADECE hedef dildeki çevrilmiş cümleyi ver.
- Asla açıklama, tırnak işareti, başlık veya gereksiz ekstra kelimeler ekleme.
- Metin ne kadar uzun veya kısa olursa olsun BİREBİR ve net çevir.
"""
        response_text, error = self._call_gemini(prompt)
        if response_text:
            cleaned = response_text.strip().strip('\'"')
            return cleaned
        return None


ai_engine = AIEngine()

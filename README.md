# Ghost Translator & AI Desktop Co-Pilot

<div align="center">

![Author](https://img.shields.io/badge/Author-Xgosh--Johan-059669?style=flat-square&logo=github)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)
![Framework](https://img.shields.io/badge/GUI-PyQt5-10b981?style=flat-square&logo=qt)
![Engine](https://img.shields.io/badge/AI-Google%20Gemini-EA580C?style=flat-square&logo=google)
![TTS](https://img.shields.io/badge/Audio-Microsoft%20Edge%20TTS-7C3AED?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-0284C7?style=flat-square)

**Geliştiriciler, Oyuncular ve Profesyoneller İçin Yeni Nesil Masaüstü Çeviri ve Yapay Zeka Asistanı**

Created & Designed by **[Xgosh-Johan](https://github.com/Xgosh-Johan)**

[Genel Bakış](#genel-bakış) • [Temel Yetenekler](#temel-yetenekler) • [Kurulum](#kurulum) • [API Yapılandırması](#api-yapılandırması) • [Kısayol Matrisi](#kısayol-matrisi) • [English Documentation](#english-documentation)

</div>

---

## Genel Bakış

Ghost Translator, ekranınızda arka planda çalışan ve sistem kaynaklarını tüketmeden sadece ihtiyaç anında tek tuşla devreye giren yüksek performanslı bir masaüstü yapay zeka asistanıdır.

Standart çeviri araçlarının aksine; metin içi deyimleri, sokak ve iş hayatı İngilizcesi alternatiflerini, oyun içi kopyalanamayan diyalogları ve yazılım loglarındaki (C++, Syserr) hata satırlarını analiz ederek doğrudan çözüm reçetesi sunar.

---

## Temel Yetenekler

### 1. Akıllı HUD ve Paralel Okuma Modu (F8)
* Ekranda seçilen herhangi bir metnin üzerinde anında yerinde genişleyen OLED arayüz kartı belirir.
* Büyütme modunda sabit çerçeveli (1020x680) çift sütunlu okuma stüdyosuna dönüşür; uzun makaleler ve paragraflar bağımsız kaydırma çubukları ile rahatça okunabilir.

### 2. Deyim ve Kalıp Fiil Analizi (Idioms & Phrasal Verbs)
* Metin içerisindeki deyimsel kalıpları ("Bite the bullet", "Burn the midnight oil" vb.) otomatik olarak tespit eder ve mecazi anlamını tek satırda açıklar.

### 3. Native Alternatif İfadeler
* Cümlelerin ana dili İngilizce olan konuşucular tarafından gündelik ve profesyonel hayatta nasıl ifade edildiğini gösteren 2-3 alternatif cümle sunar.

### 4. Kelime Anatomisi ve Örnek Cümleler
* Tekil kelimeler seçildiğinde kelime türünü (İsim / Fiil / Sıfat) ve kelimenin yer aldığı 2 adet örnek cümleyi Türkçe çevirisiyle listeler.

### 5. Yerinde İki Yönlü Chat Değiştirici (F9)
* Oyun içi sohbet kutularında, Discord'da veya metin editörlerinde yazılan Türkçe cümleyi seçip F9 tuşuna basıldığında metin doğrudan doğal İngilizce karşılığıyla değiştirilir.

### 6. Ekran Kırpma ile Optik Karakter Tanıma (OCR - CTRL+SHIFT+S)
* Ekranda kopyalanamayan oyun içi diyalogları, resimleri veya kilitli belgeleri fareyle seçerek Google Gemini Vision üzerinden anında metne ve hedef dile dönüştürür.

### 7. C++ ve Syserr Hata Teşhis Doktoru
* Kod satırları veya sunucu çökme logları seçildiğinde hatanın kök nedenini analiz ederek uygulanabilir çözüm reçetesi üretir.

### 8. Aralıklı Tekrar (SM-2 Spaced Repetition) Kelime Hafızası
* Çevrilen tüm içerikler yerel SQLite veritabanına kaydedilir. Flashcard ve Quiz modülü SuperMemo SM-2 algoritması ile kelimelerin unutulmasını engeller.

### 9. İki Yönlü Doğal Seslendirme Motoru (Microsoft Edge-TTS)
* Türkçe girdilerde hedef İngilizceyi Amerikan aksanıyla, İngilizce girdilerde hedef Türkçeyi doğal tonlamayla seslendirir.

---

## Kurulum

### Gereksinimler
* Windows 10 / 11 (64-bit)
* Python 3.9 veya daha güncel sürüm ([python.org](https://www.python.org/downloads/))

### Adımlar
1. Projeyi bilgisayarınıza indirin veya klonlayın:
   ```bash
   git clone https://github.com/Xgosh-Johan/GhostTranslator.git
   ```
2. Klasör içindeki `Kurulum_ve_Baslat.bat` dosyasını çalıştırın.
3. Gerekli bağımlılıklar otomatik olarak kurulacak ve uygulama sistem tepsisinde (System Tray) çalışmaya başlayacaktır.

---

## API Yapılandırması

Uygulama, Google Gemini Flash Lite yapay zeka modelini kullanmaktadır:

1. [Google AI Studio](https://aistudio.google.com/app/apikey) adresinden ücretsiz bir API anahtarı edinin.
2. Ghost Translator ana panelindeki **Ayarlar ve Kısayollar** sekmesine gidin.
3. API anahtarınızı ilgili alana yapıştırıp **Ayarları Kaydet** butonuna basın.

> **Veri Güvenliği Notu:** API anahtarınız ve tüm çeviri geçmişiniz yalnızca yerel bilgisayarınızda (`config.json` ve `ghost_translator.db`) saklanır. Hiçbir üçüncü taraf sunucuya veri aktarımı yapılmaz.

---

## Kısayol Matrisi

| Kısayol | Fonksiyon | Açıklama |
| :--- | :--- | :--- |
| `F8` | Seçili Metin Çevirisi | Seçilen metni analiz eder, HUD kartını açar ve seslendirir. |
| `F9` | Yerinde Chat Çevirisi | Seçili Türkçe metni silip yerine İngilizce çevirisini yapıştırır. |
| `CTRL + SHIFT + S` | Ekran Kırpma (OCR) | Ekrandan seçilen görsel alanı metne dönüştürüp çevirir. |
| `CTRL + SHIFT + O` | Ana Yönetim Paneli | Kelime hafıza kartları ve geçmiş listesini açar. |
| `ESC` | Arayüz Kapatma | Açık olan mini HUD kartını kapatır. |

---

## English Documentation

### Overview
Ghost Translator is a lightweight, zero-latency desktop AI Co-Pilot engineered for developers, gamers, and language learners.

### Core Features
* **Zero-Latency HUD (F8):** Instant on-screen overlay with expandable dual-column comparative reader.
* **Idiom Recognition:** Identifies figurative expressions and provides accurate contextual translations.
* **Native Alternatives:** Recommends authentic native phrasing for everyday and professional communication.
* **In-Place Chat Translation (F9):** Replaces selected text in-place across any active window or game chat.
* **Vision OCR (CTRL+SHIFT+S):** High-precision screen snipping powered by Gemini Vision.
* **Systems & Compiler Doctor:** Diagnoses C++, Python, and server syserr crash logs with actionable fixes.
* **Spaced Repetition Flashcards:** Long-term lexical retention backed by the SM-2 algorithm.
* **Bilingual Neural TTS:** Studio-grade pronunciation via Microsoft Edge Neural Speech engine.

### Quick Start
1. Ensure Python 3.9+ is installed with PATH enabled.
2. Run `Kurulum_ve_Baslat.bat`.
3. Enter your Gemini API key in the Settings tab.

---

## Proje Sahibi & Geliştirici

* **Yazar:** [Xgosh-Johan](https://github.com/Xgosh-Johan)
* **Lisans:** [MIT License with Attribution Clause](LICENSE)

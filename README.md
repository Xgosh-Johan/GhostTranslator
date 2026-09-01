# 👻 Ghost Translator & AI Desktop Co-Pilot

<div align="center">

![Author](https://img.shields.io/badge/Author-Xgosh--Johan-10b981?style=for-the-badge&logo=github)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-059669?style=for-the-badge&logo=qt)
![Gemini AI](https://img.shields.io/badge/AI-Google%20Gemini-EA580C?style=for-the-badge&logo=google)
![Edge TTS](https://img.shields.io/badge/Audio-Microsoft%20Edge%20TTS-7C3AED?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-0284C7?style=for-the-badge)

**Geliştiriciler, Oyuncular ve Dil Öğrenenler İçin Yeni Nesil Yapay Zeka Destekli Masaüstü Çeviri & Co-Pilot Asistanı**

Created & Designed by **[Xgosh-Johan](https://github.com/Xgosh-Johan)**

[✨ Özellikler](#-özellikler) • [🚀 Hızlı Kurulum](#-hızlı-kurulum) • [🔑 Ücretsiz API Alma](#-30-saniyede-ücretsiz-gemini-api-anahtarı-alma) • [⌨️ Kısayollar](#️-varsayılan-kısayol-tuşları) • [English Guide](#-english-quick-guide)

</div>

---

## 🌟 Neden Ghost Translator?

Piyasadaki klasik çeviri araçları (DeepL, Google Translate) sadece düz kelimeleri çevirir; oyun içi diyalogları, sokak İngilizcesi deyimlerini, alternatif söyleyiş tarzlarını ve geliştirici C++/Syserr hatalarını anlamaz.

**Ghost Translator**, ekranınızda sessizce hazır bekleyen ve sadece bir tuşla devreye giren **hepsi-bir-arada bir masaüstü süper asistanıdır:**

```
  ┌─────────────────────────────────────────────────────────────┐
  │  ⚡ F8: Anında HUD Çevirisi & Deyim Dedektörü                │
  │  💬 F9: Chatte / Oyunda Yerinde Doğal Çeviri                │
  │  🖼️ CTRL+SHIFT+S: Kopyalanamayan Alanlar İçin OCR Çevirisi  │
  │  🛠️ C++ & Syserr Hata Reçetesi Doktoru                      │
  │  🧠 Unutma Eğrili (SM-2) Kelime Hafıza Kartları & Quiz      │
  └─────────────────────────────────────────────────────────────┘
```

---

## ✨ Öne Çıkan Süper Güçler

### 1. ⚡ Akıllı Mini HUD & Devasa Okuma Modu (`F8`)
* Seçtiğiniz metnin üzerinde anında kararmaz ve donmaz bir OLED koyu kart belirir.
* **`🔍 Büyüt`**'e bastığınızda kart yerinde **`1020x680` sabit çerçeveli paralel okuma stüdyosuna** dönüşür. Uzun makaleleri ve paragrafları yan yana, kaydırma çubuğuyla (Scrollbar) rahatça okuyabilirsiniz.

### 2. 💡 Deyim & Phrasal Verb (Kalıp Fiil) Dedektörü
* Metinde bir deyim (*"Bite the bullet"*, *"Burn the midnight oil"*, *"Break a leg"*) veya kalıp fiil geçtiğinde altın sarısı **`💡 DEYİM`** rozeti açılır ve ifadenin gerçek mecazi anlamını tek satırda açıklar.

### 3. 🎭 "Bunu Başka Nasıl Söylersin?" (Native Alternatifler)
* Ana dili İngilizce olanların gündelik veya iş hayatında kullandığı **2-3 doğal alternatif ifade** (Daily & Native) sunar.

### 4. 📖 Kelime Anatomisi & Örnek Cümleler
* Tek bir kelime seçtiğinizde kelimenin türünü (*İsim / Fiil / Sıfat*) ve içinde geçtiği **2 adet kısa canlı örnek cümle + Türkçe çevirisini** listeler.

### 5. 💬 İki Yönlü Yerinde Chat Değiştirici (`F9`)
* Discord'da, oyunda veya tarayıcıda Türkçe bir şey yazıp seçin ve `F9`'a basın; yazınız anında silinir, yerine **doğal yerel İngilizce karşılığı yapışır** ve telaffuzunu kulağınıza okur.

### 6. 🖼️ Ekran Kırpma OCR Çevirisi (`CTRL + SHIFT + S`)
* Metin olarak kopyalanamayan her şeyi (oyun içi NPC diyalogları, resimler, kilitli PDF'ler) fareyle kutu içine alın; Google Vision anında okuyup çevirsin.

### 7. 🛠️ C++ & Syserr Geliştirici Doktoru
* Kod logları veya Metin2/C++ syserr satırları seçildiğinde, yapay zeka hatayı teşhis edip **1-2 maddelik net çözüm reçetesi** üretir.

### 8. 🧠 SM-2 Spaced Repetition (Aralıklı Tekrar) Kelime Stüdyosu
* Çevirdiğiniz her kelime SQLite veritabanına kaydedilir. Ana paneldeki **Flashcard / Quiz** modu unutma eğrinize göre kelimeleri size periyodik olarak hatırlatır.

### 9. 🎧 Akıllı İki Yönlü Stüdyo Seslendirmesi (Microsoft Edge-TTS)
* Türkçe seçildiğinde İngilizce karşılığını Amerikan aksanıyla (`en-US-GuyNeural`), İngilizce seçildiğinde Türkçesini (`tr-TR-AhmetNeural`) kristal netliğinde okur.

---

## 🚀 Hızlı Kurulum

### Adım 1: Python Yükleyin
Bilgisayarınızda Python 3.9 veya daha yenisi kurulu olmalıdır.
* [Python İndir (Resmi Site)](https://www.python.org/downloads/) *(Yüklerken "Add Python to PATH" kutucuğunu işaretleyin!)*

### Adım 2: Tek Tıkla Kurun ve Başlatın
1. Bu projeyi ZIP olarak indirin veya klonlayın:
   ```bash
   git clone https://github.com/Xgosh-Johan/GhostTranslator.git
   ```
2. Klasörün içindeki **`Kurulum_ve_Baslat.bat`** dosyasına çift tıklayın.
3. Gerekli kütüphaneler otomatik kurulacak ve program saatinizin yanında (Sistem Tepsisi) sessizce çalışmaya başlayacaktır!

---

## 🔑 30 Saniyede Ücretsiz Gemini API Anahtarı Alma

Ghost Translator, piyasadaki en hızlı ve cömert ücretsiz yapay zeka olan **Google Gemini Flash Lite** modelini kullanır:

1. **[Google AI Studio](https://aistudio.google.com/app/apikey)** adresine gidin ve Google hesabınızla giriş yapın.
2. **"Create API Key"** (API Anahtarı Oluştur) butonuna tıklayın.
3. Verilen anahtarı kopyalayın.
4. Ghost Translator ana penceresinde **"Ayarlar ve Kısayollar"** sekmesine gidin, anahtarı yapıştırıp **"Ayarları Kaydet"** butonuna basın.

> 🔒 **Gizlilik Garantisi:** API anahtarınız kesinlikle hiçbir üçüncü tarafa gönderilmez; sadece sizin bilgisayarınızdaki yerel `config.json` dosyasında saklanır.

---

## ⌨️ Varsayılan Kısayol Tuşları

| Kısayol | İşlev | Açıklama |
| :--- | :--- | :--- |
| **`F8`** | ⚡ **Seçili Metni Çevir** | Ekranda fareyle seçtiğiniz herhangi bir metni çevirir, seslendirir ve HUD kartını açar. |
| **`F9`** | 💬 **Chatte Yerinde Çevir** | Yazdığınız metni seçip `F9` basınca anında yerine çevirisini yapıştırır. |
| **`CTRL + SHIFT + S`** | 🖼️ **Ekran Kırpma (OCR)** | Ekrandaki kopyalanamayan alanı fareyle seçip çevirir. |
| **`CTRL + SHIFT + O`** | 📖 **Ana Paneli Aç/Kapat** | Kelime hafıza kartları ve geçmiş listesini tam ekran açar. |
| **`ESC`** | ✕ **Kartı Kapat** | Açık olan mini kartı anında gizler. |

---

## 👨‍💻 Project Creator & Lead Developer

Bu proje **[Xgosh-Johan](https://github.com/Xgosh-Johan)** tarafından tasarlanmış ve geliştirilmiştir.

* **GitHub:** [@Xgosh-Johan](https://github.com/Xgosh-Johan)
* **Lisans:** [MIT License](LICENSE)

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında açık kaynak olarak paylaşılmıştır. Dilediğiniz gibi kullanabilir, geliştirebilir ve paylaşabilirsiniz.

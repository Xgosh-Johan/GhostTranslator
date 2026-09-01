import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).resolve().parent / "ghost_translator.db"


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    phonetic TEXT,
                    context_type TEXT CHECK(context_type IN ('SELECTION', 'CHAT_OUT', 'OCR', 'MANUAL')),
                    explanation TEXT,
                    is_favorite INTEGER DEFAULT 0,
                    review_count INTEGER DEFAULT 0,
                    interval_days INTEGER DEFAULT 1,
                    ease_factor REAL DEFAULT 2.5,
                    next_review_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Otomatik Kolon Göçü (Mevcut veritabanını bozmadan yeni alanları ekle)
            cursor.execute("PRAGMA table_info(translation_history)")
            existing_cols = [row["name"] for row in cursor.fetchall()]

            if "interval_days" not in existing_cols:
                cursor.execute("ALTER TABLE translation_history ADD COLUMN interval_days INTEGER DEFAULT 1")
            if "ease_factor" not in existing_cols:
                cursor.execute("ALTER TABLE translation_history ADD COLUMN ease_factor REAL DEFAULT 2.5")
            if "next_review_at" not in existing_cols:
                cursor.execute("ALTER TABLE translation_history ADD COLUMN next_review_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            if "explanation" not in existing_cols:
                cursor.execute("ALTER TABLE translation_history ADD COLUMN explanation TEXT")
            if "idiom" not in existing_cols:
                cursor.execute("ALTER TABLE translation_history ADD COLUMN idiom TEXT")
            if "alternatives" not in existing_cols:
                cursor.execute("ALTER TABLE translation_history ADD COLUMN alternatives TEXT")
            if "examples" not in existing_cols:
                cursor.execute("ALTER TABLE translation_history ADD COLUMN examples TEXT")

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON translation_history(created_at DESC);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_is_favorite ON translation_history(is_favorite);
            """)
            conn.commit()

    def add_record(self, source_text, translated_text, phonetic="", context_type="SELECTION", explanation="", idiom="", alternatives="", examples=""):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO translation_history 
                    (source_text, translated_text, phonetic, context_type, explanation, idiom, alternatives, examples, is_favorite, review_count, interval_days, ease_factor, next_review_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 1, 2.5, datetime('now', 'localtime'), datetime('now', 'localtime'))
                """, (source_text.strip(), translated_text.strip(), phonetic.strip(), context_type, explanation.strip(), idiom.strip(), alternatives.strip(), examples.strip()))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"[DB] Kayıt ekleme hatası: {e}")
            return None

    def get_history(self, limit=200, search_query="", favorites_only=False):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM translation_history WHERE 1=1"
                params = []

                if favorites_only:
                    query += " AND is_favorite = 1"

                if search_query:
                    query += " AND (source_text LIKE ? OR translated_text LIKE ? OR explanation LIKE ?)"
                    wildcard = f"%{search_query}%"
                    params.extend([wildcard, wildcard, wildcard])

                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[DB] Geçmiş çekme hatası: {e}")
            return []

    def get_flashcards(self, limit=30):
        """Aralıklı tekrar zamanı gelen veya en çok ihtiyaç duyulan kelimeleri getirir"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM translation_history
                    ORDER BY next_review_at ASC, is_favorite DESC, review_count ASC
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[DB] Flashcard çekme hatası: {e}")
            return []

    def update_sm2_review(self, record_id, quality=4):
        """
        SuperMemo SM-2 Aralıklı Tekrar Algoritması:
        quality: 1 (Zor/Unuttum), 3 (Hatırladım), 5 (Çok Kolay)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT review_count, interval_days, ease_factor FROM translation_history WHERE id = ?", (record_id,))
                row = cursor.fetchone()
                if not row:
                    return

                reviews = row["review_count"]
                interval = row["interval_days"]
                ef = row["ease_factor"]

                # Yeni Ease Factor hesapla
                ef = max(1.3, ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

                if quality < 3:
                    reviews = 0
                    interval = 1
                else:
                    if reviews == 0:
                        interval = 1
                    elif reviews == 1:
                        interval = 3
                    elif reviews == 2:
                        interval = 6
                    else:
                        interval = int(interval * ef)
                    reviews += 1

                next_date = (datetime.now() + timedelta(days=interval)).strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute("""
                    UPDATE translation_history
                    SET review_count = ?, interval_days = ?, ease_factor = ?, next_review_at = ?
                    WHERE id = ?
                """, (reviews, interval, ef, next_date, record_id))
                conn.commit()
        except Exception as e:
            print(f"[DB] SM-2 Güncelleme hatası: {e}")

    def toggle_favorite(self, record_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE translation_history 
                    SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END 
                    WHERE id = ?
                """, (record_id,))
                conn.commit()
                cursor.execute("SELECT is_favorite FROM translation_history WHERE id = ?", (record_id,))
                row = cursor.fetchone()
                return bool(row["is_favorite"]) if row else False
        except Exception as e:
            print(f"[DB] Favori güncelleme hatası: {e}")
            return False

    def delete_record(self, record_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM translation_history WHERE id = ?", (record_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"[DB] Kayıt silme hatası: {e}")
            return False

    def clear_all(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM translation_history")
                conn.commit()
                return True
        except Exception as e:
            print(f"[DB] Veritabanı temizleme hatası: {e}")
            return False


db = Database()

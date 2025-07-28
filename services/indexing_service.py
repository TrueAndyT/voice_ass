import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

class IndexingService:
    def __init__(self):
        self.index_db_path = os.path.join("config", "file_index.db")
        self._ensure_db()

    def _ensure_db(self):
        os.makedirs(os.path.dirname(self.index_db_path), exist_ok=True)
        conn = sqlite3.connect(self.index_db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS file_index (
                id INTEGER PRIMARY KEY,
                path TEXT,
                content TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def _load_search_paths_from_config(self, config_path="config/search_config.json"):
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                paths = data.get("search_paths", [])
                valid_paths = [p for p in paths if os.path.exists(p)]
                return valid_paths
        except Exception as e:
            print(f"[ERROR] Failed to load search paths: {e}")
            return []

    def index_files(self, folder_paths=None):
        if folder_paths is None:
            folder_paths = self._load_search_paths_from_config()

        print("Indexing started...")
        conn = sqlite3.connect(self.index_db_path)
        c = conn.cursor()
        c.execute("DELETE FROM file_index")  # reset

        for folder in folder_paths:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    full_path = os.path.join(root, file)
                    try:
                        content = ""
                        if file.endswith(".txt"):
                            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                        elif file.endswith(".pdf"):
                            content = self._extract_pdf_text(full_path)
                        elif file.endswith(".docx"):
                            content = self._extract_docx_text(full_path)

                        c.execute("INSERT INTO file_index (path, content) VALUES (?, ?)", (full_path, content))
                        print(f"[OK] Indexed: {full_path}")
                    except Exception as e:
                        print(f"[WARN] Skipped {full_path}: {e}")

        conn.commit()
        conn.close()
        print("Indexing complete.")

    def load_index(self):
        conn = sqlite3.connect(self.index_db_path)
        c = conn.cursor()
        c.execute("SELECT path, content FROM file_index")
        results = c.fetchall()
        conn.close()
        return results

    def search(self, keyword):
        conn = sqlite3.connect(self.index_db_path)
        c = conn.cursor()
        c.execute("SELECT path FROM file_index WHERE path LIKE ? OR content LIKE ?", (f"%{keyword}%", f"%{keyword}%"))
        results = [row[0] for row in c.fetchall()]
        conn.close()
        return results

    def _extract_pdf_text(self, path):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            print(f"[PDF ERROR] {e}")
            return ""

    def _extract_docx_text(self, path):
        try:
            from docx import Document
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            print(f"[DOCX ERROR] {e}")
            return ""

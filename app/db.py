
import json
import sqlite3
from contextlib import AbstractContextManager
from pathlib import Path
from .config import settings

class DB(AbstractContextManager):
    """SQLite database - replaces PostgreSQL for running without Docker"""
    def __init__(self):
        self.conn = None
        self.db_path = Path(settings.DATABASE_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if it doesn't exist
        if not self.db_path.exists():
            self._init_database()

    def _init_database(self):
        """Create database tables"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_image (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id TEXT,
                lot_no TEXT,
                item_code TEXT,
                line_id TEXT,
                s3_uri TEXT,
                width_px INTEGER,
                height_px INTEGER,
                exposure_ms REAL,
                meta TEXT,
                capture_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_result (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qa_image_id INTEGER,
                model_name TEXT,
                model_version TEXT,
                inference_ms REAL,
                pass INTEGER,
                grade TEXT,
                confidence REAL,
                reason_codes TEXT,
                metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (qa_image_id) REFERENCES qa_image(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_erp_event (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qa_result_id INTEGER,
                target TEXT,
                status TEXT,
                payload TEXT,
                error TEXT,
                pushed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (qa_result_id) REFERENCES qa_result(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                s3_uri TEXT,
                label TEXT,
                quality_grade TEXT,
                item_code TEXT,
                width_px INTEGER,
                height_px INTEGER,
                meta TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()

    def __enter__(self):
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.conn:
            if exc:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()

    def insert_qa_image(self, camera_id, lot_no, item_code, line_id, s3_uri, width, height, exposure_ms, meta):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO qa_image (camera_id, lot_no, item_code, line_id, s3_uri, width_px, height_px, exposure_ms, meta)
            VALUES (?,?,?,?,?,?,?,?,?)
            """, (camera_id, lot_no, item_code, line_id, s3_uri, width, height, exposure_ms, json.dumps(meta))
        )
        return cursor.lastrowid

    def insert_qa_result(self, qa_image_id, model_name, model_version, inference_ms, passed, grade, confidence, reason_codes, metrics):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO qa_result (qa_image_id, model_name, model_version, inference_ms, pass, grade, confidence, reason_codes, metrics)
            VALUES (?,?,?,?,?,?,?,?,?)
            """, (qa_image_id, model_name, model_version, inference_ms, passed, grade, confidence, json.dumps(reason_codes), json.dumps(metrics))
        )
        return cursor.lastrowid

    def insert_erp_event_pending(self, qa_result_id, target):
        cursor = self.conn.cursor()
        cursor.execute(
            """ INSERT INTO qa_erp_event (qa_result_id, target, status, payload) VALUES (?, ?, 'PENDING', '{}') """, (qa_result_id, target)
        )

    def get_qa_result_with_image(self, qa_result_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT qr.*, qi.s3_uri, qi.lot_no, qi.item_code, qi.capture_ts
            FROM qa_result qr
            JOIN qa_image qi ON qi.id = qr.qa_image_id
            WHERE qr.id = ?
            """, (qa_result_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def mark_erp_event(self, qa_result_id: int, status: str, error: str | None = None, payload: dict | None = None):
        cursor = self.conn.cursor()
        current_payload = {}
        if payload:
            current_payload.update(payload)
        
        cursor.execute(
            """
            UPDATE qa_erp_event
            SET pushed_at = CURRENT_TIMESTAMP, status = ?, error = ?, payload = ?
            WHERE qa_result_id = ?
            """, (status, error, json.dumps(current_payload), qa_result_id)
        )

    def insert_training_data(self, s3_uri, label, quality_grade, item_code, width, height, meta):
        """Insert training data for model fine-tuning (quality_grade is now optional)"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO training_data (s3_uri, label, quality_grade, item_code, width_px, height_px, meta, created_at)
            VALUES (?,?,?,?,?,?,?, CURRENT_TIMESTAMP)
            """, (s3_uri, label, quality_grade, item_code, width, height, json.dumps(meta))
        )
        return cursor.lastrowid

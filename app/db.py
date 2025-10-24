
import json
from contextlib import AbstractContextManager
import psycopg2
import psycopg2.extras
from .config import settings

class DB(AbstractContextManager):
    def __init__(self):
        self.conn = None

    def __enter__(self):
        self.conn = psycopg2.connect(settings.DATABASE_URL)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.conn:
            if exc:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()

    def insert_qa_image(self, camera_id, lot_no, item_code, line_id, s3_uri, width, height, exposure_ms, meta):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO qa_image (camera_id, lot_no, item_code, line_id, s3_uri, width_px, height_px, exposure_ms, meta)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
                """, (camera_id, lot_no, item_code, line_id, s3_uri, width, height, exposure_ms, json.dumps(meta))
            )
            return cur.fetchone()[0]

    def insert_qa_result(self, qa_image_id, model_name, model_version, inference_ms, passed, grade, confidence, reason_codes, metrics):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO qa_result (qa_image_id, model_name, model_version, inference_ms, pass, grade, confidence, reason_codes, metrics)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
                """, (qa_image_id, model_name, model_version, inference_ms, passed, grade, confidence, reason_codes, json.dumps(metrics))
            )
            return cur.fetchone()[0]

    def insert_erp_event_pending(self, qa_result_id, target):
        with self.conn.cursor() as cur:
            cur.execute(
                """ INSERT INTO qa_erp_event (qa_result_id, target, status, payload) VALUES (%s, %s, 'PENDING', '{}') """, (qa_result_id, target)
            )

    def get_qa_result_with_image(self, qa_result_id: int):
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT qr.*, qi.s3_uri, qi.lot_no, qi.item_code, qi.capture_ts
                FROM qa_result qr
                JOIN qa_image qi ON qi.id = qr.qa_image_id
                WHERE qr.id = %s
                """, (qa_result_id,)
            )
            return cur.fetchone()

    def mark_erp_event(self, qa_result_id: int, status: str, error: str | None = None, payload: dict | None = None):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE qa_erp_event
                SET pushed_at = now(), status = %s, error = %s, payload = COALESCE(payload, '{}'::jsonb) || %s::jsonb
                WHERE qa_result_id = %s
                """, (status, error, json.dumps(payload or {}), qa_result_id)
            )

    def insert_training_data(self, s3_uri, label, quality_grade, item_code, width, height, meta):
        """Insert training data for model fine-tuning"""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO training_data (s3_uri, label, quality_grade, item_code, width_px, height_px, meta, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s, now())
                RETURNING id
                """, (s3_uri, label, quality_grade, item_code, width, height, json.dumps(meta))
            )
            return cur.fetchone()[0]

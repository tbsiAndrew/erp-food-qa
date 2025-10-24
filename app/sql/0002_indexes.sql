
CREATE INDEX IF NOT EXISTS ix_qi_capture_ts ON qa_image (capture_ts);
CREATE INDEX IF NOT EXISTS ix_qi_lot_item ON qa_image (lot_no, item_code);
CREATE INDEX IF NOT EXISTS ix_qr_pass ON qa_result (pass);
CREATE INDEX IF NOT EXISTS ix_qr_model ON qa_result (model_name, model_version);


CREATE TABLE IF NOT EXISTS qa_image (
  id BIGSERIAL PRIMARY KEY,
  capture_ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  camera_id TEXT NOT NULL,
  lot_no TEXT,
  item_code TEXT,
  line_id TEXT,
  s3_uri TEXT NOT NULL,
  width_px INT,
  height_px INT,
  exposure_ms NUMERIC,
  meta JSONB
);

CREATE TABLE IF NOT EXISTS qa_result (
  id BIGSERIAL PRIMARY KEY,
  qa_image_id BIGINT NOT NULL REFERENCES qa_image(id) ON DELETE CASCADE,
  model_name TEXT NOT NULL,
  model_version TEXT NOT NULL,
  inference_ms NUMERIC,
  pass BOOLEAN NOT NULL,
  grade TEXT,
  confidence NUMERIC,
  reason_codes TEXT[],
  metrics JSONB
);

CREATE TABLE IF NOT EXISTS qa_erp_event (
  id BIGSERIAL PRIMARY KEY,
  qa_result_id BIGINT NOT NULL REFERENCES qa_result(id) ON DELETE CASCADE,
  pushed_at TIMESTAMPTZ,
  target TEXT,
  payload JSONB,
  status TEXT,
  error TEXT
);

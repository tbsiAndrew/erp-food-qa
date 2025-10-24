-- Create training_data table for storing fine-tuning images
CREATE TABLE IF NOT EXISTS training_data (
    id SERIAL PRIMARY KEY,
    s3_uri TEXT NOT NULL,
    label TEXT NOT NULL,
    quality_grade TEXT NOT NULL,
    item_code TEXT,
    width_px INTEGER NOT NULL,
    height_px INTEGER NOT NULL,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT now(),
    used_in_training BOOLEAN DEFAULT FALSE,
    training_batch_id TEXT
);

CREATE INDEX idx_training_data_label ON training_data(label);
CREATE INDEX idx_training_data_item_code ON training_data(item_code);
CREATE INDEX idx_training_data_created_at ON training_data(created_at DESC);

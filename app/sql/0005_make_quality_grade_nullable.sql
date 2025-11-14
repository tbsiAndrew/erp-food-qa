-- Migration to make quality_grade nullable in training_data table
-- This allows training data to be submitted with only label (good/bad) without quality grade

ALTER TABLE training_data 
ALTER COLUMN quality_grade DROP NOT NULL;

COMMENT ON COLUMN training_data.quality_grade IS 'Quality grade (e.g., A, B, C, reject). Optional - can be NULL for simple good/bad classification';

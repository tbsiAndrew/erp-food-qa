-- Migration to allow NULL s3_uri when images are not saved
-- This fixes the issue where save_image=False causes database errors

ALTER TABLE qa_image 
ALTER COLUMN s3_uri DROP NOT NULL;

COMMENT ON COLUMN qa_image.s3_uri IS 'S3 URI of the image. NULL when save_image=False';

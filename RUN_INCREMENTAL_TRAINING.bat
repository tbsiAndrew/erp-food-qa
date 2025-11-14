@echo off
REM Incremental YOLO Training - Fine-tune existing model with new data
REM This updates your current model instead of creating a new one from scratch

echo.
echo ============================================================
echo   Incremental YOLO Training - Fine-tune Existing Model
echo ============================================================
echo.
echo This will:
echo  1. Move new images from good/bad folders to train/val
echo  2. Fine-tune your EXISTING model with new data
echo  3. Update runs/detect/bread_qa/weights/best.pt
echo.
echo Press Ctrl+C to cancel, or
pause

python incremental_train.py --epochs 10 --batch 8 --patience 5

echo.
echo ============================================================
echo   Training Complete!
echo ============================================================
echo.
echo Next steps:
echo  1. Restart your FastAPI server to load the updated model
echo  2. Test the updated model with new images
echo  3. Continue adding training data to improve accuracy
echo.
pause

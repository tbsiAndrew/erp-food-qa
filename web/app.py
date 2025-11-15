from flask import Flask, render_template, request, jsonify, Response
import requests
import base64
import cv2
import numpy as np

app = Flask(__name__)

FASTAPI_URL = "http://127.0.0.1:8000"

# Try to load YOLO model, fallback to OpenCV DNN if ultralytics fails
try:
    from ultralytics import YOLO
    import os
    
    # # Try to use the LATEST trained bread quality model
    # base_dir = os.path.dirname(os.path.dirname(__file__))
    
    # # Check for models in order: bread_qa3 (latest) -> bread_qa2 -> bread_qa
    # for model_name in ['bread_qa3', 'bread_qa2', 'bread_qa']:
    #     trained_model_path = os.path.join(base_dir, 'runs', 'detect', model_name, 'weights', 'best.pt')
    #     if os.path.exists(trained_model_path):
    #         model_path = trained_model_path
    #         print(f"✓ Using TRAINED Bread Quality YOLO model: {model_name}")
    #         break
    # else:
    #     model_path = os.path.join(os.path.dirname(__file__), 'yolov8n.pt')
    #     print("⚠ Trained model not found, using default yolov8n.pt")

    # Load trained bread quality model
    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'runs', 'detect', 'bread_qa2', 'weights', 'best.pt')
    print("⚠️  ALERT: Using bread_qa2")
    
    # Load model with VERY LOW confidence threshold due to poor training
    model = YOLO(model_path)
    USE_ULTRALYTICS = True
    print(f"✓ Loaded model: {model_path}")
except Exception as e:
    print(f"⚠ Ultralytics YOLO not available: {e}")
    print("⚠ Falling back to OpenCV contour detection")
    USE_ULTRALYTICS = False
    model = None



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/train')
def train_page():
    return render_template('train.html')

@app.route('/inspect', methods=['POST'])
def inspect():
    # Receive base64 image from frontend
    data = request.json
    img_data = data['image']
    lot_no = data.get('lot_no', 'LOT123')
    item_code = data.get('item_code', 'ITEM001')
    save_image = data.get('save_image', False)  # Default: don't save
    
    # Decode base64 image
    img_bytes = base64.b64decode(img_data.split(',')[1])
    
    # Save to temp file
    with open('temp.jpg', 'wb') as f:
        f.write(img_bytes)
    
    # Send to FastAPI backend
    files = {'file': open('temp.jpg', 'rb')}
    payload = {
        'lot_no': lot_no,
        'item_code': item_code,
        'save_image': save_image
    }
    
    response = requests.post(f'{FASTAPI_URL}/inspect', files=files, data=payload)
    
    return jsonify(response.json())

@app.route('/submit_training', methods=['POST'])
def submit_training():
    # Receive base64 image from frontend
    data = request.json
    img_data = data['image']
    label = data.get('label', 'good')
    item_code = data.get('item_code', '')
    auto_retrain = data.get('auto_retrain', False)
    
    # Decode base64 image
    img_bytes = base64.b64decode(img_data.split(',')[1])
    
    # Save to temp file
    with open('temp_train.jpg', 'wb') as f:
        f.write(img_bytes)
    
    # Send to FastAPI backend (no quality_grade needed)
    files = {'file': open('temp_train.jpg', 'rb')}
    payload = {
        'label': label,
        'item_code': item_code,
        'auto_retrain': str(auto_retrain).lower()  # Convert boolean to string for form data
    }
    
    response = requests.post(f'{FASTAPI_URL}/train', files=files, data=payload)
    
    return jsonify(response.json())


# MJPEG streaming endpoint for annotated frames
def gen_frames():
    # Auto-detect camera device (DroidCam might be at index 1, 2, etc.)
    cap = None
    for cam_index in range(5):  # Try indices 0-4
        test_cap = cv2.VideoCapture(cam_index)
        if test_cap.isOpened():
            ret, test_frame = test_cap.read()
            if ret and test_frame is not None:
                cap = test_cap
                print(f"✓ Camera found at index {cam_index}")
                break
            test_cap.release()
    
    if cap is None:
        print("❌ No camera found")
        return
    
    frame_count = 0
    while True:
        success, frame = cap.read()
        if not success:
            print("⚠ Failed to read frame, trying to reconnect...")
            cap.release()
            cap = cv2.VideoCapture(0)  # Try to reconnect
            continue
        
        frame_count += 1
        
        # Just stream clean frames without any detection boxes
        # Detection boxes will be drawn on the client-side canvas overlay when /inspect is called
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000, threaded=True)

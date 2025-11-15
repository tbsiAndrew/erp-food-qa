from flask import Flask, render_template, request, jsonify, Response
import requests
import base64
import cv2
import numpy as np

app = Flask(__name__)

FASTAPI_URL = "http://127.0.0.1:8000"

# Global variables for camera management
active_camera_index = None
camera_capture = None

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

@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    """Get list of available cameras with their names"""
    cameras = []
    for i in range(10):  # Check indices 0-9
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                # Try to get camera name (platform-specific)
                camera_name = f"Camera {i}"
                try:
                    # On Windows, try to get device name
                    backend = cap.getBackendName()
                    camera_name = f"Camera {i} ({backend})"
                except:
                    pass
                cameras.append({
                    'index': i,
                    'name': camera_name
                })
            cap.release()
    return jsonify({'cameras': cameras})

@app.route('/api/set_camera', methods=['POST'])
def set_camera():
    """Set the active camera index"""
    global active_camera_index, camera_capture
    data = request.json
    camera_index = data.get('camera_index')
    
    if camera_index is None:
        return jsonify({'success': False, 'error': 'camera_index is required'}), 400
    
    try:
        camera_index = int(camera_index)
        # Release old camera if exists
        if camera_capture is not None:
            camera_capture.release()
            camera_capture = None
        
        active_camera_index = camera_index
        return jsonify({'success': True, 'camera_index': camera_index})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid camera_index'}), 400

@app.route('/inspect', methods=['POST'])
def inspect():
    # Receive base64 image from frontend
    data = request.json
    img_data = data['image']
    lot_no = data.get('lot_no', 'LOT123')
    item_code = data.get('item_code', 'ITEM001')
    
    # Decode base64 image
    img_bytes = base64.b64decode(img_data.split(',')[1])
    
    # Save to temp file
    with open('temp.jpg', 'wb') as f:
        f.write(img_bytes)
    
    # Send to FastAPI backend
    files = {'file': open('temp.jpg', 'rb')}
    payload = {
        'lot_no': lot_no,
        'item_code': item_code
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
    global active_camera_index, camera_capture
    
    # Try to get camera index from environment variable, default to auto-detect
    import os
    preferred_camera = os.environ.get('CAMERA_INDEX', None)
    
    cap = None
    
    # First, check if user selected a camera via web UI
    if active_camera_index is not None:
        test_cap = cv2.VideoCapture(active_camera_index)
        if test_cap.isOpened():
            ret, test_frame = test_cap.read()
            if ret and test_frame is not None:
                cap = test_cap
                camera_capture = cap
                print(f"✓ Using selected camera at index {active_camera_index}")
            else:
                test_cap.release()
        else:
            test_cap.release()
    
    # If specific camera index is set via env variable, try it
    if cap is None and preferred_camera is not None:
        try:
            cam_index = int(preferred_camera)
            test_cap = cv2.VideoCapture(cam_index)
            if test_cap.isOpened():
                ret, test_frame = test_cap.read()
                if ret and test_frame is not None:
                    cap = test_cap
                    camera_capture = cap
                    print(f"✓ Using preferred camera at index {cam_index}")
                else:
                    test_cap.release()
            else:
                test_cap.release()
        except ValueError:
            print(f"⚠ Invalid CAMERA_INDEX value: {preferred_camera}")
    
    # Auto-detect only if no camera has ever been selected (active_camera_index is None and no env var)
    if cap is None and active_camera_index is None and preferred_camera is None:
        print("🔍 Auto-detecting camera...")
        for cam_index in range(10):  # Try indices 0-9 (increased range for more devices)
            test_cap = cv2.VideoCapture(cam_index)
            if test_cap.isOpened():
                ret, test_frame = test_cap.read()
                if ret and test_frame is not None:
                    cap = test_cap
                    camera_capture = cap
                    active_camera_index = cam_index
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

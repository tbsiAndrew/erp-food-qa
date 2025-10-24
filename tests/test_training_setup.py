"""
Quick test script to verify MinIO connection and YOLO setup
"""
import os
from dotenv import load_dotenv
import boto3
from pathlib import Path

# Load environment variables
load_dotenv()

def test_minio_connection():
    """Test connection to MinIO/S3"""
    print("🔌 Testing MinIO Connection...")
    print("-" * 60)
    
    s3_endpoint = os.getenv('S3_ENDPOINT', 'http://localhost:9000')
    s3_access_key = os.getenv('S3_ACCESS_KEY', 'minioadmin')
    s3_secret_key = os.getenv('S3_SECRET_KEY', 'minioadmin')
    s3_bucket = os.getenv('S3_BUCKET', 'qa-images')
    
    print(f"Endpoint: {s3_endpoint}")
    print(f"Bucket:   {s3_bucket}")
    
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=s3_endpoint,
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
        )
        
        # Test connection by listing buckets
        response = s3.list_buckets()
        print(f"\n✅ Connected successfully!")
        print(f"Available buckets: {[b['Name'] for b in response['Buckets']]}")
        
        # Check if our bucket exists
        if s3_bucket in [b['Name'] for b in response['Buckets']]:
            print(f"✅ Bucket '{s3_bucket}' exists")
        else:
            print(f"⚠️  Bucket '{s3_bucket}' not found")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure MinIO is running")
        print("2. Check your .env file settings")
        print("3. Verify endpoint URL and credentials")
        return False

def test_yolo_model():
    """Test YOLO model availability"""
    print("\n🤖 Testing YOLO Model...")
    print("-" * 60)
    
    model_path = Path('yolov8n.pt')
    
    if model_path.exists():
        print(f"✅ YOLO model found: {model_path}")
        print(f"   Size: {model_path.stat().st_size / (1024*1024):.1f} MB")
        
        try:
            from ultralytics import YOLO
            model = YOLO(str(model_path))
            print(f"✅ Model loaded successfully")
            print(f"   Model type: {model.type}")
            return True
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            return False
    else:
        print(f"⚠️  YOLO model not found: {model_path}")
        print("\nTo download the model:")
        print("  pip install ultralytics")
        print("  python -c 'from ultralytics import YOLO; YOLO(\"yolov8n.pt\")'")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\n📦 Testing Dependencies...")
    print("-" * 60)
    
    dependencies = [
        ('ultralytics', 'YOLOv8'),
        ('boto3', 'AWS S3/MinIO'),
        ('cv2', 'OpenCV'),
        ('torch', 'PyTorch'),
        ('dotenv', 'python-dotenv'),
    ]
    
    all_ok = True
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print(f"✅ {description:<20} ({module_name})")
        except ImportError:
            print(f"❌ {description:<20} ({module_name}) - NOT INSTALLED")
            all_ok = False
    
    return all_ok

def test_env_file():
    """Test .env file configuration"""
    print("\n⚙️  Testing .env Configuration...")
    print("-" * 60)
    
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file not found!")
        return False
    
    print(f"✅ .env file found")
    
    required_vars = [
        'S3_ENDPOINT',
        'S3_ACCESS_KEY',
        'S3_SECRET_KEY',
        'S3_BUCKET',
    ]
    
    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'PWD' in var:
                display_value = '*' * 8
            else:
                display_value = value
            print(f"✅ {var:<20} = {display_value}")
        else:
            print(f"❌ {var:<20} - NOT SET")
            all_ok = False
    
    return all_ok

def main():
    """Run all tests"""
    print("=" * 60)
    print("YOLO Training Setup Verification")
    print("=" * 60)
    
    results = []
    
    # Test 1: Dependencies
    results.append(("Dependencies", test_dependencies()))
    
    # Test 2: Environment file
    results.append(("Environment Config", test_env_file()))
    
    # Test 3: MinIO connection
    results.append(("MinIO Connection", test_minio_connection()))
    
    # Test 4: YOLO model
    results.append(("YOLO Model", test_yolo_model()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:<25} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed! You're ready to train.")
        print("\nNext step:")
        print("  python organize_minio_data.py  # Check your data")
        print("  python train_yolo_bread.py     # Start training")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
    print("=" * 60)

if __name__ == '__main__':
    main()

"""
Helper script to organize MinIO/S3 data for YOLO training
Helps you structure your images in the correct format
"""
import os
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MinIOOrganizer:
    def __init__(self):
        """Initialize MinIO client"""
        self.s3_endpoint = os.getenv('S3_ENDPOINT', 'http://localhost:9000')
        self.s3_access_key = os.getenv('S3_ACCESS_KEY', 'minioadmin')
        self.s3_secret_key = os.getenv('S3_SECRET_KEY', 'minioadmin')
        self.s3_bucket = os.getenv('S3_BUCKET', 'qa-images')
        self.s3_region = os.getenv('S3_REGION', 'us-east-1')
        
        # Initialize S3 client
        self.s3 = boto3.client(
            's3',
            endpoint_url=self.s3_endpoint,
            aws_access_key_id=self.s3_access_key,
            aws_secret_access_key=self.s3_secret_key,
            region_name=self.s3_region
        )
    
    def list_bucket_contents(self, prefix=''):
        """List all objects in bucket with given prefix"""
        print(f"\n📋 Listing contents of bucket '{self.s3_bucket}'")
        if prefix:
            print(f"   with prefix '{prefix}'")
        print("-" * 60)
        
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                print("⚠️  No objects found")
                return []
            
            objects = []
            for obj in response['Contents']:
                key = obj['Key']
                size = obj['Size']
                objects.append(key)
                
                # Format size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                
                print(f"  {key:<50} {size_str:>10}")
            
            print(f"\n✅ Total objects: {len(objects)}")
            return objects
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def check_training_structure(self):
        """Check if training data is properly structured"""
        print("\n🔍 Checking training data structure...")
        print("Expected structure:")
        print("  training/general/good/  (images of good bread)")
        print("  training/general/bad/   (images of bad bread)")
        print()
        
        # Check for good images
        good_prefix = 'training/general/good/'
        good_objects = self.list_bucket_contents(good_prefix)
        good_images = [obj for obj in good_objects if obj.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        # Check for bad images
        bad_prefix = 'training/general/bad/'
        bad_objects = self.list_bucket_contents(bad_prefix)
        bad_images = [obj for obj in bad_objects if obj.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        print("\n" + "=" * 60)
        print("📊 Training Data Summary:")
        print("=" * 60)
        print(f"  Good images: {len(good_images)}")
        print(f"  Bad images:  {len(bad_images)}")
        print(f"  Total:       {len(good_images) + len(bad_images)}")
        print("=" * 60)
        
        if len(good_images) == 0 and len(bad_images) == 0:
            print("\n⚠️  WARNING: No training images found!")
            print("\nTo prepare your data:")
            print("1. Collect images of good and bad bread")
            print("2. Upload them to MinIO using the web interface at:")
            print(f"   {self.s3_endpoint.replace('9000', '9001')}/browser/{self.s3_bucket}/")
            print("3. Create folders: training/general/good/ and training/general/bad/")
            print("4. Upload images to appropriate folders")
        elif len(good_images) < 10 or len(bad_images) < 10:
            print("\n⚠️  WARNING: You need more images for good training!")
            print("   Recommended: At least 50-100 images per class")
        else:
            print("\n✅ Data structure looks good! Ready for training.")
        
        return len(good_images), len(bad_images)
    
    def upload_sample_structure(self):
        """Create sample folder structure in MinIO"""
        print("\n📁 Creating sample folder structure in MinIO...")
        
        folders = [
            'training/general/good/',
            'training/general/bad/',
        ]
        
        for folder in folders:
            try:
                # Upload empty object to create folder
                self.s3.put_object(
                    Bucket=self.s3_bucket,
                    Key=folder,
                    Body=b''
                )
                print(f"  ✓ Created {folder}")
            except Exception as e:
                print(f"  ❌ Failed to create {folder}: {e}")
        
        print("\n✅ Folder structure created!")
        print(f"\nAccess MinIO web interface at:")
        print(f"  {self.s3_endpoint.replace('9000', '9001')}/browser/{self.s3_bucket}/")
        print(f"\nCredentials:")
        print(f"  Username: {self.s3_access_key}")
        print(f"  Password: {self.s3_secret_key}")


def main():
    """Main entry point"""
    organizer = MinIOOrganizer()
    
    print("=" * 60)
    print("MinIO Data Organizer for YOLO Training")
    print("=" * 60)
    
    # Check current structure
    good_count, bad_count = organizer.check_training_structure()
    
    # Offer to create structure if needed
    if good_count == 0 and bad_count == 0:
        create = input("\nCreate sample folder structure? (y/n): ").lower().strip()
        if create == 'y':
            organizer.upload_sample_structure()


if __name__ == '__main__':
    main()

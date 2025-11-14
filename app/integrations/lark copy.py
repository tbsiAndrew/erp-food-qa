"""
Lark (Feishu) Integration for QA Notifications
Sends inspection results to Lark via webhook
"""
import requests
import json
import base64
import cv2
import numpy as np
import os
from datetime import datetime
from ..config import settings


class LarkNotifier:
    def __init__(self, webhook_url: str = None, app_id: str = None, app_secret: str = None, drive_folder_token: str = None):
        """
        Initialize Lark notifier
        
        Args:
            webhook_url: Lark webhook URL for sending messages
            app_id: Lark app ID for file uploads
            app_secret: Lark app secret for authentication
            drive_folder_token: Lark Drive folder token for image uploads
        """
        self.webhook_url = webhook_url
        self.app_id = app_id
        self.app_secret = app_secret
        self.drive_folder_token = drive_folder_token or os.getenv('LARK_DRIVE_FOLDER_TOKEN')
        self._tenant_access_token = None
        
    def send_inspection_result(self, result_data: dict, image: np.ndarray = None) -> bool:
        """
        Send QA inspection result to Lark with optional detection image
        
        Args:
            result_data: Dictionary containing inspection results
            image: Optional OpenCV BGR image with detection boxes
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.webhook_url:
            print("⚠️ Lark webhook URL not configured, skipping notification")
            return False
        
        try:
            # Process and upload image
            image_bytes = None
            filename = None
            
            if image is not None:
                try:
                    _, buffer = cv2.imencode('.jpg', image)
                    image_bytes = buffer.tobytes()
                    
                    # --- Save image locally ---
                    save_dir = os.path.join('capture', 'image')
                    os.makedirs(save_dir, exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"capture_{timestamp}.jpg"
                    save_path = os.path.join(save_dir, filename)
                    cv2.imwrite(save_path, image)
                    print(f"✅ Image saved locally to {save_path}")
                        
                except Exception as e:
                    print(f"⚠️ Failed to process image: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Send to Anycross webhook with file attachment
            if image_bytes and filename:
                # Send as multipart/form-data with file attachment
                files = {
                    'file': (filename, image_bytes, 'image/jpeg')
                }
                # Include all other fields as form data
                data = result_data.copy()
                
                print(f"🔍 Sending to Anycross webhook with file attachment")
                response = requests.post(
                    self.webhook_url,
                    files=files,
                    data=data,
                    timeout=30
                )
            else:
                # Send as JSON without file attachment
                response = requests.post(
                    self.webhook_url,
                    json=result_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            
            
            # Debug: print response details
            print(f"🔍 Lark webhook response status: {response.status_code}")
            print(f"🔍 Lark webhook response body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0 or result.get("code") == "0":
                    print(f"✅ Lark notification sent successfully for QA result {result_data.get('qa_result_id', 'N/A')}")
                    return True
                else:
                    print(f"⚠️ Lark API error: {result}")
                    return False
            else:
                print(f"⚠️ Lark webhook request failed: {response.status_code}")
                print(f"⚠️ Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send Lark notification: {e}")
            return False
    
    def create_file_in_anycross_base(self, image_bytes: bytes, filename: str, anycross_url: str, base_id: str, table_id: str, field_id: str, access_token: str) -> dict:
        """
        Create a file in Lark Base via Anycross connector, passing image bytes as attachment.
        
        Args:
            image_bytes: Image data as bytes
            filename: Name of the file to create
            anycross_url: Anycross API endpoint (e.g., the webhook URL from Anycross connector)
            base_id: Lark Base ID
            table_id: Table ID in Lark Base
            field_id: Field ID for attachment
            access_token: Anycross/Lark API access token (if needed, may not be required for webhook)
            
        Returns:
            Response dict from Anycross API
        """
        try:
            # For Anycross connector, use multipart/form-data with the file
            files = {
                'file': (filename, image_bytes, 'image/jpeg')
            }
            
            # Include metadata in form data
            data = {
                'base_id': base_id,
                'table_id': table_id,
                'field_id': field_id,
                'filename': filename
            }
            
            headers = {}
            # Only add Authorization if access_token is provided
            if access_token and access_token != 'none':
                headers['Authorization'] = f'Bearer {access_token}'
            
            print(f"🔍 Uploading to Anycross: {anycross_url}")
            response = requests.post(anycross_url, files=files, data=data, headers=headers, timeout=30)
            
            print(f"🔍 Anycross create file response status: {response.status_code}")
            print(f"🔍 Anycross create file response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                print(f"⚠️ Anycross API error: {response.text}")
                return {'code': response.status_code, 'error': response.text}
                
        except Exception as e:
            print(f"⚠️ Failed to create file in Anycross Base: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}
    
    def _upload_file_to_lark_bitable(self, image_bytes: bytes, filename: str, tenant_access_token: str) -> str:
        """
        Upload file to Lark for Bitable attachment field
        
        Args:
            image_bytes: Image data as bytes
            filename: Filename
            tenant_access_token: Lark tenant access token
            
        Returns:
            file_token if successful, None otherwise
        """
        try:
            # Upload to Drive folder to get a file_token compatible with Bitable
            upload_url = "https://open.larksuite.com/open-apis/drive/v1/medias/upload_all"
            
            files = {
                'file': (filename, image_bytes, 'image/jpeg')
            }
            
            # Use the folder token from settings
            folder_token = self.drive_folder_token or settings.LARK_DRIVE_FOLDER_TOKEN
            
            data = {
                'file_name': filename,
                'parent_type': 'explorer',
                'parent_node': folder_token,
                'size': str(len(image_bytes))
            }
            headers = {
                'Authorization': f'Bearer {tenant_access_token}'
            }
            
            print(f"🔍 Uploading file to Drive folder: {folder_token}")
            response = requests.post(upload_url, files=files, data=data, headers=headers, timeout=30)
            
            print(f"🔍 Drive upload response status: {response.status_code}")
            print(f"🔍 Drive upload response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    file_token = result.get('data', {}).get('file_token')
                    if file_token:
                        print(f"✅ File uploaded to Drive, file_token: {file_token}")
                        return file_token
                    else:
                        print(f"⚠️ No file_token in response: {result}")
                else:
                    print(f"⚠️ Drive upload API error: {result}")
                    print(f"⚠️ Error message: {result.get('msg')}")
            else:
                print(f"⚠️ Drive upload failed with status {response.status_code}")
                print(f"⚠️ Response: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"⚠️ Failed to upload file to Drive: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_tenant_access_token(self) -> str:
        """
        Get tenant access token from Lark Open API
        
        Returns:
            tenant_access_token if successful, None otherwise
        """
        if not self.app_id or not self.app_secret:
            print("⚠️ Lark app credentials not configured")
            return None
            
        try:
            # Use open.larksuite.com for international version (Singapore)
            url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
            payload = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    return result.get("tenant_access_token")
            print(f"⚠️ Failed to get tenant access token: {response.text}")
            return None
        except Exception as e:
            print(f"⚠️ Error getting tenant access token: {e}")
            return None
    
    def _get_root_folder_token(self, tenant_access_token: str) -> str:
        """
        Get root folder token for Drive uploads
        
        Args:
            tenant_access_token: Lark tenant access token
            
        Returns:
            root folder token if successful, None otherwise
        """
        try:
            # Get root folder meta to obtain the folder token
            url = "https://open.larksuite.com/open-apis/drive/v1/metas/batch_query"
            headers = {
                'Authorization': f'Bearer {tenant_access_token}',
                'Content-Type': 'application/json'
            }
            payload = {
                "request_docs": [
                    {
                        "doc_type": "folder",
                        "doc_token": "root"
                    }
                ]
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    metas = result.get('data', {}).get('metas', [])
                    if metas and len(metas) > 0:
                        folder_token = metas[0].get('doc_token')
                        print(f"🔍 Got root folder token: {folder_token}")
                        return folder_token
            
            print(f"⚠️ Failed to get root folder token: {response.text}")
            # Fallback: use a common root folder token pattern or create a folder
            return None
        except Exception as e:
            print(f"⚠️ Error getting root folder token: {e}")
            return None
    
    def _upload_image_to_lark_drive(self, image_bytes: bytes) -> str:
        """
        Upload image to Lark Drive and get file_token for Bitable attachments
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            file_token if successful, None otherwise
        """
        try:
            # Get tenant access token
            tenant_access_token = self._get_tenant_access_token()
            if not tenant_access_token:
                print("⚠️ No tenant access token available")
                return None
            
            # Use the correct My Space folder token for QA Images
            qa_folder_token = self.drive_folder_token or 'Q9YsfWZgvlWwuLdhWUdliwdEgMQ'
            
            if not qa_folder_token:
                print("⚠️ No Drive folder token configured")
                return None
            
            upload_url = "https://open.larksuite.com/open-apis/drive/v1/medias/upload_all"
            files = {
                'file': ('qa_inspection.jpg', image_bytes, 'image/jpeg')
            }
            data = {
                'file_name': 'qa_inspection.jpg',
                'parent_type': 'explorer',
                'parent_node': qa_folder_token,
                'size': str(len(image_bytes))
            }
            headers = {
                'Authorization': f'Bearer {tenant_access_token}'
            }
            
            print(f"🔍 Uploading to folder token: {qa_folder_token}")
            response = requests.post(upload_url, files=files, data=data, headers=headers)
            
            print(f"🔍 Lark Drive upload_all response status: {response.status_code}")
            print(f"🔍 Lark Drive upload_all response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    file_token = result.get('data', {}).get('file_token')
                    print(f"✅ Image uploaded to Lark Drive, file_token: {file_token}")
                    return file_token
                else:
                    print(f"⚠️ Lark Drive upload_all error: {result}")
            else:
                print(f"⚠️ Lark Drive upload_all failed: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"⚠️ Failed to upload image to Lark Drive: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _upload_image_to_lark(self, image_bytes: bytes) -> str:
        """
        Upload image to Lark and get image_key (file_token)
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            image_key if successful, None otherwise
        """
        try:
            # Get tenant access token
            tenant_access_token = self._get_tenant_access_token()
            if not tenant_access_token:
                print("⚠️ No tenant access token available")
                return None
            
            # Upload image using IM Images API
            upload_url = "https://open.larksuite.com/open-apis/im/v1/images"
            
            files = {
                'image': ('qa_inspection.jpg', image_bytes, 'image/jpeg')
            }
            data = {
                'image_type': 'message'
            }
            headers = {
                'Authorization': f'Bearer {tenant_access_token}'
            }
            
            response = requests.post(upload_url, files=files, data=data, headers=headers)
            
            print(f"🔍 Lark upload response status: {response.status_code}")
            print(f"🔍 Lark upload response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    image_key = result.get('data', {}).get('image_key')
                    print(f"✅ Image uploaded to Lark, image_key: {image_key}")
                    return image_key
            
            print(f"⚠️ Lark image upload failed: {response.text}")
            return None
            
        except Exception as e:
            print(f"⚠️ Failed to upload image to Lark: {e}")
            return None


def send_lark_notification_async(result_data: dict, webhook_url: str = None, image: np.ndarray = None, app_id: str = None, app_secret: str = None, drive_folder_token: str = None):
    """
    Async helper to send Lark notification (for use with BackgroundTasks)
    
    Args:
        result_data: Inspection result data
        webhook_url: Lark webhook URL
        image: Optional OpenCV image with detections
        app_id: Lark app ID for file uploads
        app_secret: Lark app secret for authentication
        drive_folder_token: Lark Drive folder token for image uploads
    """
    notifier = LarkNotifier(webhook_url, app_id, app_secret, drive_folder_token)
    notifier.send_inspection_result(result_data, image)

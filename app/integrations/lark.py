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
from dotenv import load_dotenv
load_dotenv()

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
            # Upload image to Lark Drive to get a file_token compatible with Bitable attachments
            if image is not None:
                try:
                    # Image is already annotated with detection boxes from main.py
                    _, buffer = cv2.imencode('.jpg', image)
                    image_bytes = buffer.tobytes()
                    
                    # # --- Save image locally ---
                    # save_dir = os.path.join('capture', 'image')
                    # os.makedirs(save_dir, exist_ok=True)
                    # timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    # filename = f"capture_{timestamp}.jpg"
                    # save_path = os.path.join(save_dir, filename)
                    # cv2.imwrite(save_path, image)
                    # print(f"✅ Image saved locally to {save_path}")

                    print(f"🔍 Processing image: {len(image_bytes)} bytes")
                    
                    # Upload to Lark Drive
                    file_token = self._upload_image_to_lark_drive(image_bytes)
                    print(f"🔍 Received file_token from Drive upload: {file_token}")
                    
                    if file_token:
                        # Add file_token for Anycross/Bitable attachment
                        result_data['Image'] = [
                            {
                                "file_token": file_token
                            }
                        ]
                        print(f"✅ Image attached with file_token: {file_token}")
                    else:
                        print(f"⚠️ No valid file_token from Drive upload")
                except Exception as e:
                    print(f"⚠️ Failed to process image: {e}")
                    import traceback
                    traceback.print_exc()
            
            # --- Create file in Anycross Base ---
            # if image is not None:
            #     # Example usage, replace with your actual values
            #     anycross_url = os.getenv('ANYCROSS_CREATE_FILE_URL')  # e.g. 'https://anycross-sg.larksuite.com/open-apis/base/v1/app/create_file_from_content'
            #     base_id = os.getenv('LARK_BASE_ID')
            #     table_id = os.getenv('LARK_TABLE_ID')
            #     field_id = os.getenv('LARK_FIELD_ID')
            #     access_token = os.getenv('ANYCROSS_ACCESS_TOKEN')
            #     if anycross_url and base_id and table_id and field_id and access_token:
            #         anycross_resp = self.create_file_in_anycross_base(
            #             image_bytes=image_bytes,
            #             filename='qa_inspection.jpg',
            #             anycross_url=anycross_url,
            #             base_id=base_id,
            #             table_id=table_id,
            #             field_id=field_id,
            #             access_token=access_token
            #         )
            #         print(f"✅ Anycross file creation response: {anycross_resp}")
            #     else:
            #         print("⚠️ Anycross config missing, skipping file creation in Lark Base")
            
            # Send result_data directly as JSON to Anycross webhook
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
            anycross_url: Anycross API endpoint
            base_id: Lark Base ID
            table_id: Table ID in Lark Base
            field_id: Field ID for attachment
            access_token: Anycross/Lark API access token
            
        Returns:
            Response dict from Anycross API
        """
        try:
            files = {
                'file': (filename, image_bytes, 'image/jpeg')
            }
            data = {
                'base_id': base_id,
                'table_id': table_id,
                'field_id': field_id
            }
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            response = requests.post(anycross_url, files=files, data=data, headers=headers)
            print(f"🔍 Anycross create file response status: {response.status_code}")
            print(f"🔍 Anycross create file response: {response.text}")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ Anycross API error: {response.text}")
                return None
        except Exception as e:
            print(f"⚠️ Failed to create file in Anycross Base: {e}")
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
            # qa_folder_token = self.drive_folder_token or 'Q9YsfWZgvlWwuLdhWUdliwdEgMQ'
            parent_base_token = os.getenv('LARK_BASE_ID')
            print(f"🔍 parent_base_token: {parent_base_token}")
            
            # if not qa_folder_token:
            #     print("⚠️ No Drive folder token configured")
            #     return None
            
            upload_url = "https://open.larksuite.com/open-apis/drive/v1/medias/upload_all"
            files = {
                'file': ('qa_inspection.jpg', image_bytes, 'image/jpeg')
            }
            data = {
                'file_name': 'qa_inspection.jpg',
                'parent_type': 'bitable',
                'parent_node': parent_base_token,
                'size': str(len(image_bytes))
            }
            headers = {
                'Authorization': f'Bearer {tenant_access_token}'
            }
            
            print(f"🔍 Uploading to folder token: {parent_base_token}")
            response = requests.post(upload_url, files=files, data=data, headers=headers)
            
            print(f"🔍 Lark Base upload_all response status: {response.status_code}")
            print(f"🔍 Lark Base upload_all response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    file_token = result.get('data', {}).get('file_token')
                    print(f"✅ Image uploaded to Lark Drive, file_token: {file_token}")
                    return file_token
                else:
                    print(f"⚠️ Lark Base upload_all error: {result}")
            else:
                print(f"⚠️ Lark Base upload_all failed: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"⚠️ Failed to upload image to Lark Base: {e}")
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

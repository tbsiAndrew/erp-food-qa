"""
OneDrive Integration for uploading annotated detection images
Uses delegated authentication with refresh token for personal accounts
"""
import os
import requests
import base64
import time
import json
from datetime import datetime
from pathlib import Path

class OneDriveUploader:
    def __init__(self, tenant_id: str = None, client_id: str = None, client_secret: str = None, folder_path: str = "QA_Detection_Results"):
        """
        Initialize OneDrive uploader with auto token refresh using refresh token
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: Azure app client ID
            client_secret: Azure app client secret (optional for public clients)
            folder_path: Path in OneDrive to store images (default: QA_Detection_Results)
        """
        self.tenant_id = tenant_id or os.environ.get('ONEDRIVE_TENANT_ID', 'common')
        self.client_id = client_id or os.environ.get('ONEDRIVE_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('ONEDRIVE_CLIENT_SECRET')
        self.folder_path = folder_path
        self.graph_api_endpoint = "https://graph.microsoft.com/v1.0"
        self._access_token = None
        self._token_expires_at = 0
        self._refresh_token = None
        self._token_cache_file = Path("storage/.onedrive_token_cache.json")
        self._load_token_cache()
    
    def _load_token_cache(self):
        """Load cached tokens from file and set expiration to 6 hours from now if missing or expired."""
        try:
            if self._token_cache_file.exists():
                with open(self._token_cache_file, 'r') as f:
                    cache = json.load(f)
                    self._access_token = cache.get('access_token')
                    expires_at = cache.get('expires_at')
                    now = time.time()
                    # If expires_at is missing or in the past, set to 6 hours from now
                    if not expires_at or expires_at < now:
                        self._token_expires_at = now + 21600
                    else:
                        self._token_expires_at = expires_at
                    print("✅ Loaded OneDrive token cache")
        except Exception as e:
            print(f"⚠️ Failed to load token cache: {e}")
    
    def _save_token_cache(self):
        """Save tokens to cache file"""
        try:
            self._token_cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._token_cache_file, 'w') as f:
                json.dump({
                    'access_token': self._access_token,
                    'refresh_token': self._refresh_token,
                    'expires_at': self._token_expires_at
                }, f)
            print("✅ Saved OneDrive token cache")
        except Exception as e:
            print(f"⚠️ Failed to save token cache: {e}")
    
    def _get_access_token(self):
        """Get cached access token only, skip refresh. Set expiration to 6 hours after authentication."""
        now = time.time()
        # If token is valid (6 hours = 21600 seconds), use it
        if self._access_token and now < self._token_expires_at - 60:
            return self._access_token
        print("⚠️ OneDrive access token expired or not available. Run onedrive_auth_setup.py to authenticate.")
        return None
        
        # # Check if client_id is available
        # if not self.client_id:
        #     print("⚠️ OneDrive client ID not configured")
        #     return None
        
        # # Debug logging for credentials and token
        # print(f"[DEBUG] Attempting token refresh with:")
        # print(f"  tenant_id: {self.tenant_id}")
        # print(f"  client_id: {self.client_id}")
        # print(f"  client_secret: {'SET' if self.client_secret else 'NOT SET'}")
        # print(f"  refresh_token: {self._refresh_token[:8] + '...' if self._refresh_token else 'None'}")
        # print(f"  token_url: https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token")
        
        # # Try to refresh using refresh token
        # if self._refresh_token:
        #     try:
        #         token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        #         response = requests.post(
        #             token_url,
        #             data={
        #                 "client_id": self.client_id,
        #                 "refresh_token": self._refresh_token,
        #                 "grant_type": "refresh_token",
        #                 "scope": "https://graph.microsoft.com/Files.ReadWrite.All"
        #             },
        #             headers={"Content-Type": "application/x-www-form-urlencoded"}
        #         )
        #         if response.status_code == 200:
        #             data = response.json()
        #             self._access_token = data["access_token"]
        #             self._refresh_token = data.get("refresh_token", self._refresh_token)
        #             self._token_expires_at = now + int(data.get("expires_in", 3600))
        #             self._save_token_cache()
        #             print(f"✅ OneDrive access token refreshed, expires in {data.get('expires_in', 3600)}s")
        #             return self._access_token
        #         else:
        #             print(f"❌ Failed to refresh OneDrive token: {response.text}")
        #             self._refresh_token = None
        #     except Exception as e:
        #         print(f"❌ Error refreshing OneDrive token: {e}")
        
        # # If no refresh token or refresh failed, user needs to sign in
        # print("⚠️ OneDrive refresh token not available. Run onedrive_auth_setup.py to authenticate.")
        # return None
        
    def upload_image(self, image_data, filename: str = None):
        """
        Upload annotated image to OneDrive
        
        Args:
            image_data: Image bytes or base64 string
            filename: Custom filename (auto-generated if None)
            
        Returns:
            dict: Upload result with OneDrive file URL
        """
        # Get fresh access token
        access_token = self._get_access_token()
        if not access_token:
            print("⚠️ OneDrive access token not available")
            return {"success": False, "error": "No access token"}
        
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"detection_{timestamp}.jpg"
            # Convert base64 to bytes if needed
            if isinstance(image_data, str):
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data
            # Upload to OneDrive using /me/drive for personal accounts
            upload_url = f"{self.graph_api_endpoint}/me/drive/root:/{self.folder_path}/{filename}:/content"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "image/jpeg"
            }
            response = requests.put(upload_url, headers=headers, data=image_bytes)
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ Image uploaded to OneDrive: {result.get('webUrl', 'N/A')}")
                return {
                    "success": True,
                    "file_id": result.get('id'),
                    "file_name": result.get('name'),
                    "web_url": result.get('webUrl'),
                    "download_url": result.get('@microsoft.graph.downloadUrl')
                }
            else:
                print(f"❌ OneDrive upload failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            print(f"❌ OneDrive upload error: {e}")
            return {"success": False, "error": str(e)}
    
    def create_shared_link(self, file_id: str):
        """
        Create a shareable link for the uploaded file
        
        Args:
            file_id: OneDrive file ID
            
        Returns:
            dict: Shared link information
        """
        if not self.access_token:
            return {"success": False, "error": "No access token"}
        
        try:
            url = f"{self.graph_api_endpoint}/me/drive/items/{file_id}/createLink"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "type": "view",  # view or edit
                "scope": "anonymous"  # anonymous or organization
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "link": result.get('link', {}).get('webUrl')
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global OneDrive uploader instance
_onedrive_uploader = None

def get_onedrive_uploader():
    """Get or create OneDrive uploader instance"""
    from app.config import settings
    global _onedrive_uploader
    if _onedrive_uploader is None:
        _onedrive_uploader = OneDriveUploader(
            tenant_id=settings.ONEDRIVE_TENANT_ID,
            client_id=settings.ONEDRIVE_CLIENT_ID,
            client_secret=settings.ONEDRIVE_CLIENT_SECRET,
            folder_path=settings.ONEDRIVE_FOLDER_PATH
        )
    return _onedrive_uploader

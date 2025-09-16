import time
from typing import Dict, Optional

import requests

from config import config
from logging_config import setup_logger


class CloudflareImageHandler:
    """Cloudflare Images API handler specifically for the user processor Lambda"""
    
    def __init__(self):
        self.account_id = config.CLOUDFLARE_ACCOUNT_ID
        self.api_token = config.CLOUDFLARE_API_TOKEN
        self.logger = setup_logger(__name__)
        
    def upload_image(self, image_url: str, require_signed_urls: bool = True) -> Optional[Dict]:
        """Upload an image to Cloudflare Images via URL and return response dict like original"""
        if not image_url:
            return None
            
        try:
            # First download the image
            image_response = requests.get(image_url, timeout=30)
            if image_response.status_code != 200:
                self.logger.error(f"Failed to download image from URL: {image_url}")
                return None

            # Prepare the upload request
            api_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/images/v1"
            headers = {
                "Authorization": f"Bearer {self.api_token}"
            }
            
            # Prepare form data
            files = {
                'file': ('image.jpg', image_response.content),
                'requireSignedURLs': (None, str(require_signed_urls).lower())
            }
            
            # Make the upload request
            response = requests.post(api_url, headers=headers, files=files)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # Return in the same format as original CloudflareImageHandler
                    return {
                        "success": True,
                        "result": {
                            "id": result["result"]["id"],
                            "variants": result["result"].get("variants", []),
                            "requireSignedURLs": require_signed_urls
                        },
                        "errors": [],
                        "messages": []
                    }
                else:
                    self.logger.error(f"Cloudflare API error: {result.get('errors')}")
            else:
                self.logger.error(f"Failed to upload image. Status: {response.status_code}")
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error uploading image to Cloudflare: {str(e)}")
            return None

    def delete_image(self, image_url: str) -> bool:
        """Delete image from Cloudflare to prevent orphaned images"""
        if not image_url:
            return True
            
        try:
            # Extract image ID from URL
            image_id = image_url.split('/')[-2]
            api_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/images/v1/{image_id}"
            headers = {"Authorization": f"Bearer {self.api_token}"}

            response = requests.delete(api_url, headers=headers)
            if response.status_code == 200:
                self.logger.info(f"Successfully deleted image {image_id}")
                return True
            else:
                # Check for specific error codes
                response_json = response.json()
                errors = response_json.get('errors', [])
                
                # Handle slow connection error (5408) with retry
                if any(error.get('code') == 5408 for error in errors):
                    self.logger.warning("Cloudflare slow connection error detected, waiting 30 seconds...")
                    time.sleep(30)
                    retry_response = requests.delete(api_url, headers=headers)
                    if retry_response.status_code == 200:
                        self.logger.info(f"Successfully deleted image {image_id} after retry")
                        return True
                    else:
                        self.logger.error(f"Failed to delete image {image_id} after retry. Status: {retry_response.status_code}")
                        return False
                else:
                    self.logger.error(f"Failed to delete image {image_id}. Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error deleting image: {e}")
            return False

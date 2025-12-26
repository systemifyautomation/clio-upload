"""
Clio API Client for uploading files and folders to Clio.com
Supports OAuth authentication and EU endpoint (eu.app.clio.com)
"""

import os
import mimetypes
from typing import Optional, Dict, Any, List
import requests
from pathlib import Path


class ClioAPIClient:
    """Client for interacting with Clio API v4"""
    
    def __init__(self, access_token: str, region: str = "eu"):
        """
        Initialize Clio API client
        
        Args:
            access_token: OAuth access token for Clio API
            region: API region - "us" for app.clio.com or "eu" for eu.app.clio.com
        """
        self.access_token = access_token
        self.region = region
        
        if region == "eu":
            self.base_url = "https://eu.app.clio.com/api/v4"
        else:
            self.base_url = "https://app.clio.com/api/v4"
        
        self.headers = {
            "Authorization": f"Bearer {access_token}"
        }
    
    def create_folder(self, name: str, parent_id: Optional[int] = None, 
                     matter_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a folder in Clio
        
        Args:
            name: Name of the folder
            parent_id: Parent folder ID (optional)
            matter_id: Matter ID to associate the folder with (optional)
            
        Returns:
            Dictionary containing the created folder information
        """
        url = f"{self.base_url}/folders.json"
        
        data = {
            "data": {
                "name": name
            }
        }
        
        if parent_id:
            data["data"]["parent"] = {"id": parent_id}
        
        if matter_id:
            data["data"]["matter"] = {"id": matter_id}
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def upload_file(self, file_path: str, folder_id: Optional[int] = None,
                   matter_id: Optional[int] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a file to Clio using the 3-step process:
        1. Create document record and get upload URL
        2. Upload file to S3
        3. Mark document as fully uploaded
        
        Args:
            file_path: Path to the file to upload
            folder_id: Folder ID to upload to (optional)
            matter_id: Matter ID to associate the file with (optional)
            description: Description of the document (optional)
            
        Returns:
            Dictionary containing the uploaded document information
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
        
        print(f"\n=== STEP 1: Creating document record ===")
        
        # Step 1: Create document record
        url = f"{self.base_url}/documents.json"
        params = {"fields": "id,latest_document_version{uuid,put_url,put_headers}"}
        
        data = {
            "data": {
                "name": file_path_obj.name,
                "parent": {}
            }
        }
        
        # Set parent - either folder or matter
        if folder_id:
            data["data"]["parent"]["id"] = folder_id
            data["data"]["parent"]["type"] = "Folder"
        elif matter_id:
            data["data"]["parent"]["id"] = matter_id
            data["data"]["parent"]["type"] = "Matter"
        
        # Set matter association if provided
        if matter_id:
            data["data"]["matter"] = {"id": matter_id}
        
        # Set description if provided
        if description:
            data["data"]["description"] = description
        
        print(f"Request URL: {url}")
        print(f"Request data: {data}")
        
        response = requests.post(url, headers=self.headers, json=data, params=params)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        response.raise_for_status()
        
        result = response.json()
        document_id = result["data"]["id"]
        version_data = result["data"]["latest_document_version"]
        uuid = version_data["uuid"]
        put_url = version_data["put_url"]
        put_headers = {h["name"]: h["value"] for h in version_data["put_headers"]}
        
        print(f"\n=== STEP 2: Uploading file to S3 ===")
        print(f"Document ID: {document_id}")
        print(f"UUID: {uuid}")
        print(f"Upload URL: {put_url[:100]}...")
        print(f"Upload headers: {put_headers}")
        
        # Step 2: Upload file to S3
        with open(file_path, "rb") as f:
            file_content = f.read()
            upload_response = requests.put(put_url, data=file_content, headers=put_headers)
            print(f"Upload response status: {upload_response.status_code}")
            if upload_response.status_code not in [200, 201, 204]:
                print(f"Upload response body: {upload_response.text}")
            upload_response.raise_for_status()
        
        print(f"\n=== STEP 3: Marking document as fully uploaded ===")
        
        # Step 3: Mark document as fully uploaded
        update_url = f"{self.base_url}/documents/{document_id}.json"
        update_params = {"fields": "id,name,latest_document_version{fully_uploaded}"}
        update_data = {
            "data": {
                "uuid": uuid,
                "fully_uploaded": True
            }
        }
        
        print(f"Update URL: {update_url}")
        print(f"Update data: {update_data}")
        
        update_response = requests.patch(update_url, headers=self.headers, json=update_data, params=update_params)
        print(f"Update response status: {update_response.status_code}")
        print(f"Update response body: {update_response.text}")
        update_response.raise_for_status()
        
        print(f"\n=== Upload complete! ===\n")
        return update_response.json()
    
    def upload_folder(self, folder_path: str, parent_folder_id: Optional[int] = None,
                     matter_id: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Recursively upload a folder and all its contents to Clio
        
        Args:
            folder_path: Path to the folder to upload
            parent_folder_id: Parent folder ID in Clio (optional)
            matter_id: Matter ID to associate files with (optional)
            
        Returns:
            Dictionary containing lists of created folders and uploaded files
        """
        folder_path_obj = Path(folder_path)
        if not folder_path_obj.exists() or not folder_path_obj.is_dir():
            raise ValueError(f"Folder not found or not a directory: {folder_path}")
        
        results = {
            "folders": [],
            "files": []
        }
        
        # Create the root folder
        folder_name = folder_path_obj.name
        folder_result = self.create_folder(
            name=folder_name,
            parent_id=parent_folder_id,
            matter_id=matter_id
        )
        results["folders"].append(folder_result)
        
        # Get the created folder ID
        created_folder_id = folder_result["data"]["id"]
        
        # Upload all files and subdirectories
        for item in folder_path_obj.iterdir():
            if item.is_file():
                # Upload file
                try:
                    file_result = self.upload_file(
                        file_path=str(item),
                        folder_id=created_folder_id,
                        matter_id=matter_id
                    )
                    results["files"].append(file_result)
                except Exception as e:
                    print(f"Error uploading file {item}: {e}")
            
            elif item.is_dir():
                # Recursively upload subdirectory
                try:
                    sub_results = self.upload_folder(
                        folder_path=str(item),
                        parent_folder_id=created_folder_id,
                        matter_id=matter_id
                    )
                    results["folders"].extend(sub_results["folders"])
                    results["files"].extend(sub_results["files"])
                except Exception as e:
                    print(f"Error uploading folder {item}: {e}")
        
        return results
    
    def get_matters(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of matters from Clio
        
        Args:
            limit: Maximum number of matters to retrieve
            
        Returns:
            List of matter dictionaries
        """
        url = f"{self.base_url}/matters.json"
        params = {"limit": limit}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json().get("data", [])
    
    def get_folders(self, matter_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of folders from Clio
        
        Args:
            matter_id: Filter by matter ID (optional)
            limit: Maximum number of folders to retrieve
            
        Returns:
            List of folder dictionaries
        """
        url = f"{self.base_url}/folders.json"
        params = {"limit": limit}
        
        if matter_id:
            params["matter_id"] = matter_id
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json().get("data", [])

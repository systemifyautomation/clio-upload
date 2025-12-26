"""
Example usage of the Clio Upload API client
"""

from clio_client import ClioAPIClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the client
client = ClioAPIClient(
    access_token=os.getenv("CLIO_ACCESS_TOKEN"),
    region="eu"  # Use "eu" for eu.app.clio.com or "us" for app.clio.com
)

# Example 1: Get list of matters
print("Getting matters...")
matters = client.get_matters(limit=10)
print(f"Found {len(matters)} matters")
if matters:
    print(f"First matter: {matters[0].get('display_number')} - {matters[0].get('description')}")

# Example 2: Create a folder
print("\nCreating folder...")
folder = client.create_folder(
    name="Client Documents",
    matter_id=matters[0]["id"] if matters else None
)
print(f"Created folder: {folder['data']['name']} (ID: {folder['data']['id']})")

# Example 3: Upload a single file
print("\nUploading file...")
file_result = client.upload_file(
    file_path="/path/to/your/file.pdf",
    folder_id=folder['data']['id'],
    description="Important document"
)
print(f"Uploaded file: {file_result['data']['name']}")

# Example 4: Upload an entire folder recursively
print("\nUploading folder...")
folder_result = client.upload_folder(
    folder_path="/path/to/your/folder",
    matter_id=matters[0]["id"] if matters else None
)
print(f"Uploaded {len(folder_result['folders'])} folders and {len(folder_result['files'])} files")

# Example 5: Get folders
print("\nGetting folders...")
folders = client.get_folders(limit=10)
print(f"Found {len(folders)} folders")

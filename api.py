"""
Flask API for Clio file/folder upload
This API can be integrated with n8n for automation workflows
"""

import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from clio_client import ClioAPIClient
from pathlib import Path

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
CLIO_ACCESS_TOKEN = os.getenv("CLIO_ACCESS_TOKEN")
CLIO_REGION = os.getenv("CLIO_REGION", "eu")  # Default to EU endpoint


def get_clio_client(access_token: str = None, region: str = None) -> ClioAPIClient:
    """Get Clio API client with provided or default credentials"""
    token = access_token or CLIO_ACCESS_TOKEN
    reg = region or CLIO_REGION
    
    if not token:
        raise ValueError("No access token provided. Set CLIO_ACCESS_TOKEN environment variable or provide in request.")
    
    return ClioAPIClient(access_token=token, region=reg)


@app.route("/", methods=["GET"])
def home():
    """API information endpoint"""
    return jsonify({
        "name": "Clio Upload API",
        "version": "1.0.0",
        "description": "API for uploading files and folders to Clio.com",
        "endpoints": {
            "/upload/file": "Upload a single file",
            "/upload/folder": "Upload a folder recursively",
            "/folders/create": "Create a folder",
            "/matters": "Get list of matters",
            "/folders": "Get list of folders"
        }
    })


@app.route("/upload/file", methods=["POST"])
def upload_file():
    """
    Upload a single file to Clio
    
    Request body (JSON):
        - file_path: Path to the file to upload (required)
        - folder_id: Clio folder ID (optional)
        - matter_id: Clio matter ID (optional)
        - description: File description (optional)
        - access_token: Override default access token (optional)
        - region: Override default region (optional)
    
    Or multipart/form-data with:
        - file: The file to upload
        - folder_id, matter_id, description as form fields
    """
    try:
        # Handle JSON request
        if request.is_json:
            data = request.get_json()
            file_path = data.get("file_path")
            folder_id = data.get("folder_id")
            matter_id = data.get("matter_id")
            description = data.get("description")
            access_token = data.get("access_token")
            region = data.get("region")
            
            if not file_path:
                return jsonify({"error": "file_path is required"}), 400
            
            client = get_clio_client(access_token, region)
            result = client.upload_file(
                file_path=file_path,
                folder_id=folder_id,
                matter_id=matter_id,
                description=description
            )
            
            return jsonify({
                "success": True,
                "data": result
            })
        
        # Handle multipart/form-data
        elif "file" in request.files:
            uploaded_file = request.files["file"]
            folder_id = request.form.get("folder_id")
            matter_id = request.form.get("matter_id")
            description = request.form.get("description")
            access_token = request.form.get("access_token")
            region = request.form.get("region")
            
            if uploaded_file.filename == "":
                return jsonify({"error": "No file selected"}), 400
            
            # Save file temporarily
            temp_dir = Path("/tmp/clio_uploads")
            temp_dir.mkdir(exist_ok=True)
            temp_file_path = temp_dir / uploaded_file.filename
            uploaded_file.save(str(temp_file_path))
            
            try:
                client = get_clio_client(access_token, region)
                result = client.upload_file(
                    file_path=str(temp_file_path),
                    folder_id=int(folder_id) if folder_id else None,
                    matter_id=int(matter_id) if matter_id else None,
                    description=description
                )
                
                return jsonify({
                    "success": True,
                    "data": result
                })
            finally:
                # Clean up temp file
                if temp_file_path.exists():
                    temp_file_path.unlink()
        
        else:
            return jsonify({"error": "Invalid request. Provide JSON with file_path or multipart/form-data with file"}), 400
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/upload/folder", methods=["POST"])
def upload_folder():
    """
    Upload a folder recursively to Clio
    
    Request body (JSON):
        - folder_path: Path to the folder to upload (required)
        - parent_folder_id: Clio parent folder ID (optional)
        - matter_id: Clio matter ID (optional)
        - access_token: Override default access token (optional)
        - region: Override default region (optional)
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request body must be JSON"}), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400
        
        folder_path = data.get("folder_path")
        parent_folder_id = data.get("parent_folder_id")
        matter_id = data.get("matter_id")
        access_token = data.get("access_token")
        region = data.get("region")
        
        if not folder_path:
            return jsonify({"error": "folder_path is required"}), 400
        
        client = get_clio_client(access_token, region)
        result = client.upload_folder(
            folder_path=folder_path,
            parent_folder_id=parent_folder_id,
            matter_id=matter_id
        )
        
        return jsonify({
            "success": True,
            "data": result,
            "summary": {
                "folders_created": len(result["folders"]),
                "files_uploaded": len(result["files"])
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/folders/create", methods=["POST"])
def create_folder():
    """
    Create a folder in Clio
    
    Request body (JSON):
        - name: Folder name (required)
        - parent_id: Parent folder ID (optional)
        - matter_id: Matter ID (optional)
        - access_token: Override default access token (optional)
        - region: Override default region (optional)
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request body must be JSON"}), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400
        
        name = data.get("name")
        parent_id = data.get("parent_id")
        matter_id = data.get("matter_id")
        access_token = data.get("access_token")
        region = data.get("region")
        
        if not name:
            return jsonify({"error": "name is required"}), 400
        
        client = get_clio_client(access_token, region)
        result = client.create_folder(
            name=name,
            parent_id=parent_id,
            matter_id=matter_id
        )
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/matters", methods=["GET"])
def get_matters():
    """
    Get list of matters from Clio
    
    Query parameters:
        - limit: Maximum number of matters to retrieve (default: 50)
        - access_token: Override default access token (optional)
        - region: Override default region (optional)
    """
    try:
        limit = request.args.get("limit", 50, type=int)
        access_token = request.args.get("access_token")
        region = request.args.get("region")
        
        client = get_clio_client(access_token, region)
        result = client.get_matters(limit=limit)
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/folders", methods=["GET"])
def get_folders():
    """
    Get list of folders from Clio
    
    Query parameters:
        - matter_id: Filter by matter ID (optional)
        - limit: Maximum number of folders to retrieve (default: 50)
        - access_token: Override default access token (optional)
        - region: Override default region (optional)
    """
    try:
        matter_id = request.args.get("matter_id", type=int)
        limit = request.args.get("limit", 50, type=int)
        access_token = request.args.get("access_token")
        region = request.args.get("region")
        
        client = get_clio_client(access_token, region)
        result = client.get_folders(matter_id=matter_id, limit=limit)
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    app.run(host="0.0.0.0", port=port, debug=debug)

# Clio Upload API

This project is for Arbitrio and provides Python code to upload files and folders to Clio.com account using their API. The code works as a REST API itself and can be integrated with n8n to automate client intake processes.

**Endpoint**: Configured for EU endpoint (eu.app.clio.com) by default

## Features

- ✅ Upload single files to Clio
- ✅ Upload entire folders recursively (with subfolders)
- ✅ Create folders in Clio
- ✅ Associate files/folders with matters
- ✅ OAuth authentication support
- ✅ EU endpoint support (eu.app.clio.com)
- ✅ REST API for n8n integration
- ✅ Both file path and multipart upload support

## Installation

1. Clone the repository:
```bash
git clone https://github.com/systemifyautomation/clio-upload.git
cd clio-upload
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your Clio API access token
```

## Configuration

Create a `.env` file with the following variables:

```env
CLIO_ACCESS_TOKEN=your_access_token_here
CLIO_REGION=eu  # "eu" for eu.app.clio.com or "us" for app.clio.com
PORT=5000
DEBUG=False
```

### Getting a Clio Access Token

1. Go to your Clio Developer Portal: https://app.clio.com/settings/developer_applications
2. Create a new application or use an existing one
3. Follow the OAuth 2.0 flow to get an access token
4. Add the token to your `.env` file

## Usage

### Option 1: Python Client Library

Use the `ClioAPIClient` class directly in your Python code:

```python
from clio_client import ClioAPIClient

# Initialize client
client = ClioAPIClient(
    access_token="your_token",
    region="eu"
)

# Upload a file
result = client.upload_file(
    file_path="/path/to/file.pdf",
    folder_id=123,  # optional
    matter_id=456,  # optional
    description="Important document"
)

# Upload a folder recursively
result = client.upload_folder(
    folder_path="/path/to/folder",
    parent_folder_id=123,  # optional
    matter_id=456  # optional
)

# Create a folder
folder = client.create_folder(
    name="Client Documents",
    parent_id=123,  # optional
    matter_id=456   # optional
)
```

See `example.py` for more usage examples.

### Option 2: REST API Server

Start the Flask API server:

```bash
python api.py
```

The API will be available at `http://localhost:5000`

#### API Endpoints

**1. Upload a File**

```bash
# Using JSON with file path
curl -X POST http://localhost:5000/upload/file \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/file.pdf",
    "folder_id": 123,
    "matter_id": 456,
    "description": "Important document"
  }'

# Using multipart/form-data
curl -X POST http://localhost:5000/upload/file \
  -F "file=@/path/to/file.pdf" \
  -F "folder_id=123" \
  -F "matter_id=456"
```

**2. Upload a Folder**

```bash
curl -X POST http://localhost:5000/upload/folder \
  -H "Content-Type: application/json" \
  -d '{
    "folder_path": "/path/to/folder",
    "parent_folder_id": 123,
    "matter_id": 456
  }'
```

**3. Create a Folder**

```bash
curl -X POST http://localhost:5000/folders/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Client Documents",
    "parent_id": 123,
    "matter_id": 456
  }'
```

**4. Get Matters**

```bash
curl http://localhost:5000/matters?limit=50
```

**5. Get Folders**

```bash
curl http://localhost:5000/folders?matter_id=456&limit=50
```

### n8n Integration

To integrate with n8n:

1. Start the API server: `python api.py`
2. In n8n, use the HTTP Request node
3. Configure the node:
   - Method: POST
   - URL: `http://your-server:5000/upload/file` or `/upload/folder`
   - Authentication: None (token is in .env)
   - Body: JSON with required parameters

Example n8n workflow:
```json
{
  "method": "POST",
  "url": "http://localhost:5000/upload/file",
  "body": {
    "file_path": "{{$node.previousNode.json.filePath}}",
    "matter_id": "{{$node.previousNode.json.matterId}}",
    "description": "Client intake document"
  }
}
```

## API Response Format

Successful responses:
```json
{
  "success": true,
  "data": {
    // Clio API response data
  }
}
```

Error responses:
```json
{
  "success": false,
  "error": "Error message"
}
```

## Security Notes

- Never commit your `.env` file or access tokens to version control
- Use environment variables for sensitive configuration
- The access token should be kept secure and rotated regularly
- For production use, implement proper OAuth flow instead of hardcoded tokens

## Requirements

- Python 3.7+
- requests
- python-dotenv
- flask

## License

MIT License

## Support

For issues or questions, please open an issue on GitHub.

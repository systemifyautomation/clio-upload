# Clio Document Upload - Individual CURL Commands
# Copy and paste these commands one at a time, replacing the variables

## CONFIGURATION
```bash
# Set these variables first
ACCESS_TOKEN="3763-2HGkMJnF1PsHffdfuXLqAHq72eKT3rPtidv"
REGION="eu"
FILE_PATH="/path/to/your/file.pdf"
FILE_NAME="document.pdf"
MATTER_ID="13638307"
FOLDER_ID=""  # Optional - leave empty for matter root
DESCRIPTION="Uploaded via CURL"
```

---

## STEP 1: Create Document Record

This creates a document record in Clio and returns the S3 upload URL.

### For uploading to a Matter (no folder):

```bash
curl -X POST \
  "https://${REGION}.app.clio.com/api/v4/documents.json?fields=id,latest_document_version{uuid,put_url,put_headers}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "name": "'"${FILE_NAME}"'",
      "parent": {
        "id": '"${MATTER_ID}"',
        "type": "Matter"
      },
      "matter": {
        "id": '"${MATTER_ID}"'
      },
      "description": "'"${DESCRIPTION}"'"
    }
  }'
```

### For uploading to a Folder:

```bash
curl -X POST \
  "https://${REGION}.app.clio.com/api/v4/documents.json?fields=id,latest_document_version{uuid,put_url,put_headers}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "name": "'"${FILE_NAME}"'",
      "parent": {
        "id": '"${FOLDER_ID}"',
        "type": "Folder"
      },
      "matter": {
        "id": '"${MATTER_ID}"'
      },
      "description": "'"${DESCRIPTION}"'"
    }
  }'
```

**Expected Response:**
```json
{
  "data": {
    "id": 12345,
    "latest_document_version": {
      "uuid": "a51faa2c-859e-4c08-a996-2d0bb385df90",
      "put_url": "https://s3.amazonaws.com/...",
      "put_headers": [
        {
          "name": "Content-Type",
          "value": "application/pdf"
        },
        {
          "name": "x-amz-server-side-encryption",
          "value": "AES256"
        }
      ]
    }
  }
}
```

**Save these values:**
```bash
DOCUMENT_ID="12345"  # From response: data.id
UUID="a51faa2c-859e-4c08-a996-2d0bb385df90"  # From response: data.latest_document_version.uuid
PUT_URL="https://s3.amazonaws.com/..."  # From response: data.latest_document_version.put_url
CONTENT_TYPE="application/pdf"  # From response: data.latest_document_version.put_headers[0].value
SERVER_SIDE_ENCRYPTION="AES256"  # From response: data.latest_document_version.put_headers[1].value
```

---

## STEP 2: Upload File to S3

Upload the actual file content to the S3 URL from Step 1.

```bash
curl -X PUT \
  "${PUT_URL}" \
  -H "Content-Type: ${CONTENT_TYPE}" \
  -H "x-amz-server-side-encryption: ${SERVER_SIDE_ENCRYPTION}" \
  --data-binary "@${FILE_PATH}"
```

**Expected Response:**
- HTTP 200 or 204 (no body content)
- If there's an error, you'll get an XML response from S3

---

## STEP 3: Mark Document as Fully Uploaded

Notify Clio that the upload is complete.

```bash
curl -X PATCH \
  "https://${REGION}.app.clio.com/api/v4/documents/${DOCUMENT_ID}.json?fields=id,name,latest_document_version{fully_uploaded}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "uuid": "'"${UUID}"'",
      "fully_uploaded": true
    }
  }'
```

**Expected Response:**
```json
{
  "data": {
    "id": 12345,
    "name": "document.pdf",
    "latest_document_version": {
      "fully_uploaded": true
    }
  }
}
```

---

## Complete Example (All Steps)

Here's a complete example with hardcoded values for easy testing:

```bash
# STEP 1: Create Document Record
STEP1_RESPONSE=$(curl -s -X POST \
  "https://eu.app.clio.com/api/v4/documents.json?fields=id,latest_document_version{uuid,put_url,put_headers}" \
  -H "Authorization: Bearer 3763-2HGkMJnF1PsHffdfuXLqAHq72eKT3rPtidv" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "name": "test-document.pdf",
      "parent": {
        "id": 13638307,
        "type": "Matter"
      },
      "matter": {
        "id": 13638307
      },
      "description": "Test upload"
    }
  }')

# Extract values (requires jq)
DOCUMENT_ID=$(echo $STEP1_RESPONSE | jq -r '.data.id')
UUID=$(echo $STEP1_RESPONSE | jq -r '.data.latest_document_version.uuid')
PUT_URL=$(echo $STEP1_RESPONSE | jq -r '.data.latest_document_version.put_url')
CONTENT_TYPE=$(echo $STEP1_RESPONSE | jq -r '.data.latest_document_version.put_headers[] | select(.name == "Content-Type") | .value')
SERVER_SIDE_ENCRYPTION=$(echo $STEP1_RESPONSE | jq -r '.data.latest_document_version.put_headers[] | select(.name == "x-amz-server-side-encryption") | .value')

echo "Document ID: $DOCUMENT_ID"
echo "UUID: $UUID"

# STEP 2: Upload to S3
curl -X PUT \
  "$PUT_URL" \
  -H "Content-Type: $CONTENT_TYPE" \
  -H "x-amz-server-side-encryption: $SERVER_SIDE_ENCRYPTION" \
  --data-binary "@/path/to/your/file.pdf"

# STEP 3: Mark as uploaded
curl -X PATCH \
  "https://eu.app.clio.com/api/v4/documents/${DOCUMENT_ID}.json?fields=id,name,latest_document_version{fully_uploaded}" \
  -H "Authorization: Bearer 3763-2HGkMJnF1PsHffdfuXLqAHq72eKT3rPtidv" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "uuid": "'"${UUID}"'",
      "fully_uploaded": true
    }
  }'
```

---

## PowerShell Version

For Windows PowerShell (using curl.exe):

```powershell
# STEP 1: Create Document Record
$STEP1_RESPONSE = curl.exe -s -X POST `
  "https://eu.app.clio.com/api/v4/documents.json?fields=id,latest_document_version{uuid,put_url,put_headers}" `
  -H "Authorization: Bearer 3763-2HGkMJnF1PsHffdfuXLqAHq72eKT3rPtidv" `
  -H "Content-Type: application/json" `
  -d '{\"data\":{\"name\":\"test.pdf\",\"parent\":{\"id\":13638307,\"type\":\"Matter\"},\"matter\":{\"id\":13638307}}}'

# Parse response (convert from JSON)
$STEP1_DATA = $STEP1_RESPONSE | ConvertFrom-Json
$DOCUMENT_ID = $STEP1_DATA.data.id
$UUID = $STEP1_DATA.data.latest_document_version.uuid
$PUT_URL = $STEP1_DATA.data.latest_document_version.put_url

Write-Host "Document ID: $DOCUMENT_ID"
Write-Host "UUID: $UUID"

# STEP 2: Upload to S3
$CONTENT_TYPE = ($STEP1_DATA.data.latest_document_version.put_headers | Where-Object { $_.name -eq "Content-Type" }).value
$ENCRYPTION = ($STEP1_DATA.data.latest_document_version.put_headers | Where-Object { $_.name -eq "x-amz-server-side-encryption" }).value

curl.exe -X PUT $PUT_URL `
  -H "Content-Type: $CONTENT_TYPE" `
  -H "x-amz-server-side-encryption: $ENCRYPTION" `
  --data-binary "@C:\path\to\file.pdf"

# STEP 3: Mark as uploaded
curl.exe -X PATCH `
  "https://eu.app.clio.com/api/v4/documents/$DOCUMENT_ID.json?fields=id,name,latest_document_version{fully_uploaded}" `
  -H "Authorization: Bearer 3763-2HGkMJnF1PsHffdfuXLqAHq72eKT3rPtidv" `
  -H "Content-Type: application/json" `
  -d "{\"data\":{\"uuid\":\"$UUID\",\"fully_uploaded\":true}}"
```

---

## Troubleshooting

### Error: "Missing required parameter: parent"
Make sure you're including both the `parent` object with `id` and `type`.

### Error: "Missing required parameter: name"
Include the `name` field in the data object (the filename).

### S3 Upload fails (403 Forbidden)
- The signed URL has expired (they expire in 8 hours)
- Make sure you're including the exact headers from the response

### Error: "UploadNotFoundError" in Step 3
- The file wasn't successfully uploaded to S3 in Step 2
- Check the S3 upload response for errors

### How to get the access token
See the main README.md for OAuth setup instructions.

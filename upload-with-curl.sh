#!/bin/bash

# Clio Document Upload - CURL Script
# This script demonstrates the 3-step process for uploading files to Clio using CURL

# ========================================
# CONFIGURATION - UPDATE THESE VALUES
# ========================================

# Your Clio access token
ACCESS_TOKEN="3763-2HGkMJnF1PsHffdfuXLqAHq72eKT3rPtidv"

# Region: "eu" or "us"
REGION="eu"

# File to upload (absolute path)
FILE_PATH="/path/to/your/file.pdf"

# Matter ID (required)
MATTER_ID="13638307"

# Folder ID (optional - leave empty to upload to matter root)
FOLDER_ID=""

# Description (optional)
DESCRIPTION="Document uploaded via CURL"

# ========================================
# SCRIPT - DO NOT MODIFY BELOW THIS LINE
# ========================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Construct base URL
BASE_URL="https://${REGION}.app.clio.com/api/v4"

# Extract filename from path
FILE_NAME=$(basename "$FILE_PATH")

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    echo -e "${RED}Error: File not found: $FILE_PATH${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Clio Document Upload Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "File: ${YELLOW}$FILE_NAME${NC}"
echo -e "Matter ID: ${YELLOW}$MATTER_ID${NC}"
echo -e "Region: ${YELLOW}$REGION${NC}"
echo ""

# ========================================
# STEP 1: Create Document Record
# ========================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STEP 1: Creating Document Record${NC}"
echo -e "${BLUE}========================================${NC}"

# Build JSON payload
if [ -n "$FOLDER_ID" ]; then
    PARENT_ID="$FOLDER_ID"
    PARENT_TYPE="Folder"
else
    PARENT_ID="$MATTER_ID"
    PARENT_TYPE="Matter"
fi

# Build description field
if [ -n "$DESCRIPTION" ]; then
    DESC_FIELD=",\"description\":\"$DESCRIPTION\""
else
    DESC_FIELD=""
fi

# Create document record
STEP1_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/documents.json?fields=id,latest_document_version{uuid,put_url,put_headers}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"data\": {
      \"name\": \"${FILE_NAME}\",
      \"parent\": {
        \"id\": ${PARENT_ID},
        \"type\": \"${PARENT_TYPE}\"
      },
      \"matter\": {
        \"id\": ${MATTER_ID}
      }${DESC_FIELD}
    }
  }")

# Check for errors
if echo "$STEP1_RESPONSE" | grep -q "error"; then
    echo -e "${RED}Error in Step 1:${NC}"
    echo "$STEP1_RESPONSE" | jq '.'
    exit 1
fi

# Extract values from response
DOCUMENT_ID=$(echo "$STEP1_RESPONSE" | jq -r '.data.id')
UUID=$(echo "$STEP1_RESPONSE" | jq -r '.data.latest_document_version.uuid')
PUT_URL=$(echo "$STEP1_RESPONSE" | jq -r '.data.latest_document_version.put_url')

# Extract headers
CONTENT_TYPE=$(echo "$STEP1_RESPONSE" | jq -r '.data.latest_document_version.put_headers[] | select(.name == "Content-Type") | .value')
SERVER_SIDE_ENCRYPTION=$(echo "$STEP1_RESPONSE" | jq -r '.data.latest_document_version.put_headers[] | select(.name == "x-amz-server-side-encryption") | .value')

echo -e "${GREEN}✓ Document record created${NC}"
echo -e "Document ID: ${YELLOW}$DOCUMENT_ID${NC}"
echo -e "UUID: ${YELLOW}$UUID${NC}"
echo ""

# ========================================
# STEP 2: Upload File to S3
# ========================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STEP 2: Uploading File to S3${NC}"
echo -e "${BLUE}========================================${NC}"

# Upload file to S3
STEP2_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT \
  "$PUT_URL" \
  -H "Content-Type: $CONTENT_TYPE" \
  -H "x-amz-server-side-encryption: $SERVER_SIDE_ENCRYPTION" \
  --data-binary "@$FILE_PATH")

# Extract HTTP status code
HTTP_STATUS=$(echo "$STEP2_RESPONSE" | tail -n1)
STEP2_BODY=$(echo "$STEP2_RESPONSE" | sed '$d')

# Check upload status
if [ "$HTTP_STATUS" -eq 200 ] || [ "$HTTP_STATUS" -eq 204 ]; then
    echo -e "${GREEN}✓ File uploaded to S3 successfully${NC}"
    echo -e "HTTP Status: ${YELLOW}$HTTP_STATUS${NC}"
else
    echo -e "${RED}Error in Step 2:${NC}"
    echo -e "HTTP Status: ${RED}$HTTP_STATUS${NC}"
    echo "$STEP2_BODY"
    exit 1
fi

echo ""

# ========================================
# STEP 3: Mark Document as Fully Uploaded
# ========================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STEP 3: Marking Document as Uploaded${NC}"
echo -e "${BLUE}========================================${NC}"

# Mark document as fully uploaded
STEP3_RESPONSE=$(curl -s -X PATCH \
  "${BASE_URL}/documents/${DOCUMENT_ID}.json?fields=id,name,latest_document_version{fully_uploaded}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"data\": {
      \"uuid\": \"${UUID}\",
      \"fully_uploaded\": true
    }
  }")

# Check for errors
if echo "$STEP3_RESPONSE" | grep -q "error"; then
    echo -e "${RED}Error in Step 3:${NC}"
    echo "$STEP3_RESPONSE" | jq '.'
    exit 1
fi

# Extract final status
FULLY_UPLOADED=$(echo "$STEP3_RESPONSE" | jq -r '.data.latest_document_version.fully_uploaded')
FINAL_NAME=$(echo "$STEP3_RESPONSE" | jq -r '.data.name')

if [ "$FULLY_UPLOADED" = "true" ]; then
    echo -e "${GREEN}✓ Document marked as fully uploaded${NC}"
    echo -e "Document Name: ${YELLOW}$FINAL_NAME${NC}"
    echo -e "Document ID: ${YELLOW}$DOCUMENT_ID${NC}"
else
    echo -e "${RED}Warning: Document may not be fully uploaded${NC}"
    echo "$STEP3_RESPONSE" | jq '.'
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ UPLOAD COMPLETE!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "View document in Clio:"
echo -e "${BLUE}https://${REGION}.app.clio.com/nc/#/documents/${DOCUMENT_ID}${NC}"

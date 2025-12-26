# Clio Document Upload - PowerShell Script
# This script demonstrates the 3-step process for uploading files to Clio using CURL

# ========================================
# CONFIGURATION - UPDATE THESE VALUES
# ========================================

# Your Clio access token
$ACCESS_TOKEN = "3763-2HGkMJnF1PsHffdfuXLqAHq72eKT3rPtidv"

# Region: "eu" or "us"
$REGION = "eu"

# File to upload (absolute path)
$FILE_PATH = "C:\path\to\your\file.pdf"

# Matter ID (required)
$MATTER_ID = "13638307"

# Folder ID (optional - leave empty to upload to matter root)
$FOLDER_ID = ""

# Description (optional)
$DESCRIPTION = "Document uploaded via PowerShell/CURL"

# ========================================
# SCRIPT - DO NOT MODIFY BELOW THIS LINE
# ========================================

# Construct base URL
$BASE_URL = "https://$REGION.app.clio.com/api/v4"

# Extract filename from path
$FILE_NAME = Split-Path -Leaf $FILE_PATH

# Check if file exists
if (-not (Test-Path $FILE_PATH)) {
    Write-Host "Error: File not found: $FILE_PATH" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Clio Document Upload Script" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "File: $FILE_NAME" -ForegroundColor Yellow
Write-Host "Matter ID: $MATTER_ID" -ForegroundColor Yellow
Write-Host "Region: $REGION" -ForegroundColor Yellow
Write-Host ""

# ========================================
# STEP 1: Create Document Record
# ========================================

Write-Host "========================================" -ForegroundColor Blue
Write-Host "STEP 1: Creating Document Record" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue

# Build parent configuration
if ($FOLDER_ID) {
    $PARENT_ID = $FOLDER_ID
    $PARENT_TYPE = "Folder"
} else {
    $PARENT_ID = $MATTER_ID
    $PARENT_TYPE = "Matter"
}

# Build description field
$DESC_FIELD = ""
if ($DESCRIPTION) {
    $DESC_FIELD = ",`"description`":`"$DESCRIPTION`""
}

# Create JSON payload
$STEP1_BODY = @"
{
  "data": {
    "name": "$FILE_NAME",
    "parent": {
      "id": $PARENT_ID,
      "type": "$PARENT_TYPE"
    },
    "matter": {
      "id": $MATTER_ID
    }$DESC_FIELD
  }
}
"@

# Save to temp file for curl
$TEMP_JSON = "$env:TEMP\clio_step1.json"
$STEP1_BODY | Out-File -FilePath $TEMP_JSON -Encoding UTF8

# Execute curl command
$STEP1_RESPONSE = curl.exe -s -X POST `
  "$BASE_URL/documents.json?fields=id,latest_document_version{uuid,put_url,put_headers}" `
  -H "Authorization: Bearer $ACCESS_TOKEN" `
  -H "Content-Type: application/json" `
  -d "@$TEMP_JSON"

# Parse JSON response
$STEP1_DATA = $STEP1_RESPONSE | ConvertFrom-Json

# Check for errors
if ($STEP1_DATA.error) {
    Write-Host "Error in Step 1:" -ForegroundColor Red
    $STEP1_RESPONSE | ConvertTo-Json -Depth 10
    exit 1
}

# Extract values
$DOCUMENT_ID = $STEP1_DATA.data.id
$UUID = $STEP1_DATA.data.latest_document_version.uuid
$PUT_URL = $STEP1_DATA.data.latest_document_version.put_url

# Extract headers
$CONTENT_TYPE = ($STEP1_DATA.data.latest_document_version.put_headers | Where-Object { $_.name -eq "Content-Type" }).value
$SERVER_SIDE_ENCRYPTION = ($STEP1_DATA.data.latest_document_version.put_headers | Where-Object { $_.name -eq "x-amz-server-side-encryption" }).value

Write-Host "✓ Document record created" -ForegroundColor Green
Write-Host "Document ID: $DOCUMENT_ID" -ForegroundColor Yellow
Write-Host "UUID: $UUID" -ForegroundColor Yellow
Write-Host ""

# ========================================
# STEP 2: Upload File to S3
# ========================================

Write-Host "========================================" -ForegroundColor Blue
Write-Host "STEP 2: Uploading File to S3" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue

# Upload file to S3
$STEP2_OUTPUT = curl.exe -s -w "`n%{http_code}" -X PUT `
  $PUT_URL `
  -H "Content-Type: $CONTENT_TYPE" `
  -H "x-amz-server-side-encryption: $SERVER_SIDE_ENCRYPTION" `
  --data-binary "@$FILE_PATH"

# Extract HTTP status
$STEP2_LINES = $STEP2_OUTPUT -split "`n"
$HTTP_STATUS = $STEP2_LINES[-1]

# Check upload status
if ($HTTP_STATUS -eq "200" -or $HTTP_STATUS -eq "204") {
    Write-Host "✓ File uploaded to S3 successfully" -ForegroundColor Green
    Write-Host "HTTP Status: $HTTP_STATUS" -ForegroundColor Yellow
} else {
    Write-Host "Error in Step 2:" -ForegroundColor Red
    Write-Host "HTTP Status: $HTTP_STATUS" -ForegroundColor Red
    $STEP2_OUTPUT
    exit 1
}

Write-Host ""

# ========================================
# STEP 3: Mark Document as Fully Uploaded
# ========================================

Write-Host "========================================" -ForegroundColor Blue
Write-Host "STEP 3: Marking Document as Uploaded" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue

# Create JSON payload
$STEP3_BODY = @"
{
  "data": {
    "uuid": "$UUID",
    "fully_uploaded": true
  }
}
"@

# Save to temp file
$TEMP_JSON3 = "$env:TEMP\clio_step3.json"
$STEP3_BODY | Out-File -FilePath $TEMP_JSON3 -Encoding UTF8

# Execute curl command
$STEP3_RESPONSE = curl.exe -s -X PATCH `
  "$BASE_URL/documents/$DOCUMENT_ID.json?fields=id,name,latest_document_version{fully_uploaded}" `
  -H "Authorization: Bearer $ACCESS_TOKEN" `
  -H "Content-Type: application/json" `
  -d "@$TEMP_JSON3"

# Parse response
$STEP3_DATA = $STEP3_RESPONSE | ConvertFrom-Json

# Check for errors
if ($STEP3_DATA.error) {
    Write-Host "Error in Step 3:" -ForegroundColor Red
    $STEP3_RESPONSE | ConvertTo-Json -Depth 10
    exit 1
}

# Extract final status
$FULLY_UPLOADED = $STEP3_DATA.data.latest_document_version.fully_uploaded
$FINAL_NAME = $STEP3_DATA.data.name

if ($FULLY_UPLOADED -eq $true) {
    Write-Host "✓ Document marked as fully uploaded" -ForegroundColor Green
    Write-Host "Document Name: $FINAL_NAME" -ForegroundColor Yellow
    Write-Host "Document ID: $DOCUMENT_ID" -ForegroundColor Yellow
} else {
    Write-Host "Warning: Document may not be fully uploaded" -ForegroundColor Red
    $STEP3_RESPONSE | ConvertTo-Json -Depth 10
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ UPLOAD COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "View document in Clio:"
Write-Host "https://$REGION.app.clio.com/nc/#/documents/$DOCUMENT_ID" -ForegroundColor Blue

# Cleanup temp files
Remove-Item $TEMP_JSON -ErrorAction SilentlyContinue
Remove-Item $TEMP_JSON3 -ErrorAction SilentlyContinue

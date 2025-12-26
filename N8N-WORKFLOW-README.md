# n8n Workflow for Clio Document Upload

This n8n workflow implements the 3-step process for uploading files to Clio.com using their API v4.

## Workflow Version
- Compatible with n8n version 1.123.4+

## Setup Instructions

### 1. Import the Workflow

1. Open your n8n instance
2. Go to **Workflows** > **Import from File**
3. Select `clio-upload-workflow.json`
4. The workflow will be imported

### 2. Configure Clio Credentials

You'll need to set up Clio API credentials in n8n:

1. Go to **Credentials** in n8n
2. Click **Add Credential**
3. Search for "HTTP Request" or create a custom credential
4. For the workflow, update the **Set Clio Credentials** node with:
   - `region`: Either "eu" or "us" depending on your Clio instance
   - `accessToken`: Your Clio OAuth access token

Alternatively, you can:
- Create a Clio API credential type in n8n
- Store your access token in n8n environment variables
- Use n8n's built-in credential system

### 3. Configure Input Parameters

The workflow expects the following input parameters (set in the **Set Input Parameters** node):

```json
{
  "filePath": "/path/to/your/file.pdf",
  "fileName": "document.pdf",
  "matterId": 13638307,
  "description": "Optional description",
  "folderId": null
}
```

**Parameters:**
- `filePath` (required): Absolute path to the file on the n8n server
- `fileName` (required): Name to give the document in Clio
- `matterId` (required): The Clio matter ID to associate the document with
- `description` (optional): Description for the document
- `folderId` (optional): If provided, uploads to this folder instead of the matter root

## How the Workflow Works

The workflow implements Clio's 3-step upload process:

### Step 1: Create Document Record
- **Node**: "Step 1 - Create Document Record"
- **Action**: POST to `/api/v4/documents.json`
- **Purpose**: Creates a document record in Clio and receives:
  - Document ID
  - UUID for the upload
  - Signed S3 upload URL
  - Required headers for S3 upload

### Step 2: Upload to S3
- **Node**: "Step 2 - Upload to S3"
- **Action**: PUT to the S3 signed URL
- **Purpose**: Uploads the actual file content to Amazon S3
- The file is read from disk using the "Read Binary File" node

### Step 3: Mark as Uploaded
- **Node**: "Step 3 - Mark as Uploaded"
- **Action**: PATCH to `/api/v4/documents/{id}.json`
- **Purpose**: Notifies Clio that the upload is complete
- Clio verifies the file was uploaded successfully

## Running the Workflow

### Manual Execution

1. Click on the **Set Input Parameters** node
2. Update the JSON with your file details
3. Click **Execute Workflow**
4. Monitor the execution through each step

### Webhook Trigger (Optional)

You can replace the manual trigger with:
- **Webhook**: To receive file upload requests from external systems
- **Schedule**: To process files on a schedule
- **File Trigger**: To watch a folder and upload new files automatically

### Integration with Other Systems

The workflow can be extended to:
1. Receive files via HTTP POST
2. Download files from cloud storage (Dropbox, Google Drive, etc.)
3. Process multiple files in batch
4. Send notifications on success/failure

## Example: Webhook Integration

To make this work with webhooks:

1. Replace the "When clicking 'Test workflow'" node with a **Webhook** node
2. Configure the webhook to accept file uploads
3. Map the webhook data to the Set Input Parameters node

Example webhook payload:
```json
{
  "filePath": "/tmp/uploaded-file.pdf",
  "fileName": "client-document.pdf",
  "matterId": 13638307,
  "description": "Uploaded via API"
}
```

## Error Handling

The workflow will fail if:
- The file doesn't exist at the specified path
- Invalid matter ID or folder ID
- Network issues during S3 upload
- File too large (Clio has size limits)

Consider adding:
- **Error Trigger** nodes to handle failures
- **Retry** logic for network issues
- **Notifications** on failure (email, Slack, etc.)

## Environment Variables

For production use, store sensitive data in environment variables:

```bash
# In your n8n environment
CLIO_ACCESS_TOKEN=your-access-token-here
CLIO_REGION=eu
```

Then reference them in the workflow:
```
{{ $env.CLIO_ACCESS_TOKEN }}
{{ $env.CLIO_REGION }}
```

## Troubleshooting

### Upload fails at Step 2
- Ensure the file exists at the specified path
- Check that n8n has read permissions for the file
- Verify the file isn't corrupted

### Upload fails at Step 3
- The S3 upload may have timed out
- Check Clio's file size limits
- Retry the workflow

### Authentication errors
- Verify your access token is valid
- Check the region is correct (eu vs us)
- Ensure the token has document upload permissions

## Advanced: Batch Upload

To upload multiple files, add a **Split In Batches** node:

1. Feed in an array of file objects
2. Process each file through the workflow
3. Collect results at the end

## Notes

- File size limits depend on your Clio plan
- For files >100MB, consider using multipart upload
- The workflow runs synchronously - large files may take time
- Consider adding progress notifications for long uploads

## API Documentation

For more details on Clio's API:
- [Clio API Documentation](https://docs.developers.clio.com/api-reference/#tag/Documents)
- [Document Upload Process](https://docs.developers.clio.com/api-reference/#tag/Documents/Uploading-a-new-document)

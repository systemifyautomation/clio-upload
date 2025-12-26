"""
Basic tests for the Clio Upload API
These tests verify the structure and basic functionality without making actual API calls
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from clio_client import ClioAPIClient


class TestClioAPIClient(unittest.TestCase):
    """Test the ClioAPIClient class"""
    
    def setUp(self):
        """Set up test client"""
        self.client = ClioAPIClient(access_token="test_token", region="eu")
    
    def test_client_initialization_eu(self):
        """Test client initialization with EU region"""
        client = ClioAPIClient(access_token="test_token", region="eu")
        self.assertEqual(client.base_url, "https://eu.app.clio.com/api/v4")
        self.assertEqual(client.access_token, "test_token")
        self.assertEqual(client.region, "eu")
    
    def test_client_initialization_us(self):
        """Test client initialization with US region"""
        client = ClioAPIClient(access_token="test_token", region="us")
        self.assertEqual(client.base_url, "https://app.clio.com/api/v4")
        self.assertEqual(client.access_token, "test_token")
        self.assertEqual(client.region, "us")
    
    def test_authorization_header(self):
        """Test that authorization header is set correctly"""
        self.assertIn("Authorization", self.client.headers)
        self.assertEqual(self.client.headers["Authorization"], "Bearer test_token")
    
    @patch('clio_client.requests.post')
    def test_create_folder(self, mock_post):
        """Test folder creation"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": 123,
                "name": "Test Folder"
            }
        }
        mock_post.return_value = mock_response
        
        result = self.client.create_folder(name="Test Folder", matter_id=456)
        
        self.assertEqual(result["data"]["id"], 123)
        self.assertEqual(result["data"]["name"], "Test Folder")
        mock_post.assert_called_once()
    
    @patch('clio_client.requests.post')
    def test_upload_file(self, mock_post):
        """Test file upload"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_file = f.name
        
        try:
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": {
                    "id": 789,
                    "name": "test.txt"
                }
            }
            mock_post.return_value = mock_response
            
            result = self.client.upload_file(
                file_path=temp_file,
                folder_id=123,
                description="Test file"
            )
            
            self.assertEqual(result["data"]["id"], 789)
            mock_post.assert_called_once()
        finally:
            os.unlink(temp_file)
    
    def test_upload_file_not_found(self):
        """Test file upload with non-existent file"""
        with self.assertRaises(FileNotFoundError):
            self.client.upload_file(file_path="/nonexistent/file.txt")
    
    @patch('clio_client.requests.post')
    def test_upload_folder(self, mock_post):
        """Test folder upload"""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test structure
            test_dir = Path(temp_dir) / "test_folder"
            test_dir.mkdir()
            (test_dir / "file1.txt").write_text("content1")
            (test_dir / "file2.txt").write_text("content2")
            
            subdir = test_dir / "subfolder"
            subdir.mkdir()
            (subdir / "file3.txt").write_text("content3")
            
            # Mock responses
            mock_response = Mock()
            mock_response.json.side_effect = [
                {"data": {"id": 100, "name": "test_folder"}},  # folder creation
                {"data": {"id": 201, "name": "file1.txt"}},    # file upload
                {"data": {"id": 202, "name": "file2.txt"}},    # file upload
                {"data": {"id": 101, "name": "subfolder"}},    # subfolder creation
                {"data": {"id": 203, "name": "file3.txt"}},    # file upload
            ]
            mock_post.return_value = mock_response
            
            result = self.client.upload_folder(folder_path=str(test_dir))
            
            # Check that folders and files were created
            self.assertIn("folders", result)
            self.assertIn("files", result)
    
    def test_upload_folder_not_found(self):
        """Test folder upload with non-existent folder"""
        with self.assertRaises(ValueError):
            self.client.upload_folder(folder_path="/nonexistent/folder")
    
    @patch('clio_client.requests.get')
    def test_get_matters(self, mock_get):
        """Test getting matters"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"id": 1, "display_number": "M001"},
                {"id": 2, "display_number": "M002"}
            ]
        }
        mock_get.return_value = mock_response
        
        result = self.client.get_matters(limit=10)
        
        self.assertEqual(len(result), 2)
        mock_get.assert_called_once()
    
    @patch('clio_client.requests.get')
    def test_get_folders(self, mock_get):
        """Test getting folders"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"id": 1, "name": "Folder 1"},
                {"id": 2, "name": "Folder 2"}
            ]
        }
        mock_get.return_value = mock_response
        
        result = self.client.get_folders(matter_id=123, limit=10)
        
        self.assertEqual(len(result), 2)
        mock_get.assert_called_once()


class TestFlaskAPI(unittest.TestCase):
    """Test the Flask API"""
    
    def setUp(self):
        """Set up test Flask app"""
        from api import app
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_home_endpoint(self):
        """Test the home endpoint"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("name", data)
        self.assertIn("endpoints", data)
    
    def test_upload_file_no_data(self):
        """Test upload file endpoint with no data"""
        response = self.client.post('/upload/file')
        self.assertEqual(response.status_code, 400)
    
    def test_upload_folder_no_data(self):
        """Test upload folder endpoint with no data"""
        response = self.client.post('/upload/folder')
        self.assertEqual(response.status_code, 400)
    
    def test_create_folder_no_data(self):
        """Test create folder endpoint with no data"""
        response = self.client.post('/folders/create')
        self.assertEqual(response.status_code, 400)
    
    @patch.dict(os.environ, {'CLIO_ACCESS_TOKEN': 'test_token'})
    @patch('api.get_clio_client')
    def test_get_matters(self, mock_get_client):
        """Test get matters endpoint"""
        mock_client = Mock()
        mock_client.get_matters.return_value = [
            {"id": 1, "display_number": "M001"}
        ]
        mock_get_client.return_value = mock_client
        
        response = self.client.get('/matters?limit=10')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
    
    @patch.dict(os.environ, {'CLIO_ACCESS_TOKEN': 'test_token'})
    @patch('api.get_clio_client')
    def test_get_folders(self, mock_get_client):
        """Test get folders endpoint"""
        mock_client = Mock()
        mock_client.get_folders.return_value = [
            {"id": 1, "name": "Folder 1"}
        ]
        mock_get_client.return_value = mock_client
        
        response = self.client.get('/folders?limit=10')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])


if __name__ == '__main__':
    unittest.main()

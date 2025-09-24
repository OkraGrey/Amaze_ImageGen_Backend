import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from backend.config.settings import GOOGLE_CLIENT_SECRET_FILE, GOOGLE_TOKEN_FILE

# This scope allows the app to access only the files it has created or opened.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_drive_service():
    """
    Authenticates with the Google Drive API and returns a service object.
    """
    creds = None
    if os.path.exists(GOOGLE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(GOOGLE_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)

def get_or_create_folder(service, folder_name, parent_id=None):
    """
    Checks if a folder exists in Google Drive, and creates it if it doesn't.
    """
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = response.get('files', [])

    if files:
        return files[0].get('id')
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')

def upload_file_content(service, content, filename, folder_id, mimetype='image/png'):
    """
    Uploads file content to a specific folder in Google Drive.
    """
    file_metadata = {
        "name": filename,
        "parents": [folder_id]
    }

    media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mimetype, resumable=True)
    file = service.files().create(
        body=file_metadata, 
        media_body=media, 
        fields="id"
    ).execute()
    
    return file.get("id")

def download_file(service, file_id, destination_path):
    """
    Downloads a file from Google Drive.
    """
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    with open(destination_path, "wb") as f:
        f.write(fh.getbuffer())

def make_file_public(service, file_id):
    """
    Makes a file public and returns its web view link.
    """
    service.permissions().create(fileId=file_id, body={'type': 'anyone', 'role': 'reader'}).execute()
    file = service.files().get(fileId=file_id, fields='webContentLink').execute()
    return file.get('webContentLink')

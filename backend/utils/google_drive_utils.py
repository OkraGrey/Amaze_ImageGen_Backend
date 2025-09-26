import os
import io
import json

import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from backend.config.settings import GOOGLE_CLIENT_SECRET_FILE, GOOGLE_TOKEN_FILE
from googleapiclient.errors import HttpError
from backend.utils.logger import app_logger

# This scope allows the app to access only the files it has created or opened.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_drive_service():
    """
    Authenticates with the Google Drive API and returns a service object.
    Uses Workload Identity Federation if available (for Vercel),
    otherwise falls back to the local OAuth 2.0 flow.
    """
    # Vercel (production) authentication using Workload Identity Federation
    if os.getenv("VERCEL") == "1":
        # Vercel provides the OIDC token in this environment variable
        oidc_token = os.getenv("VERCEL_OIDC_TOKEN")
        if not oidc_token:
            raise ValueError("VERCEL_OIDC_TOKEN environment variable not found.")

        # Write the token to a temporary file, as the Google Auth library expects a file path
        token_path = "/tmp/vercel_oidc_token.txt"
        with open(token_path, "w") as f:
            f.write(oidc_token)
            
        # These environment variables must be set in your Vercel project settings
        project_number = os.getenv("GCP_PROJECT_NUMBER")
        pool_id = os.getenv("GCP_WORKLOAD_IDENTITY_POOL_ID")
        provider_id = os.getenv("GCP_WORKLOAD_IDENTITY_PROVIDER_ID")
        service_account_email = os.getenv("GCP_SERVICE_ACCOUNT_EMAIL")

        # Construct the credential configuration file content
        gcp_creds_config = {
            "type": "external_account",
            "audience": f"//iam.googleapis.com/projects/{project_number}/locations/global/workloadIdentityPools/{pool_id}/providers/{provider_id}",
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
            "token_url": "https://sts.googleapis.com/v1/token",
            "service_account_impersonation_url": f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{service_account_email}:generateAccessToken",
            "credential_source": {
                "file": token_path,
                "format": {"type": "text"}
            }
        }
        
        # Write the configuration to a temporary file
        config_path = "/tmp/gcp_creds.json"
        with open(config_path, "w") as f:
            json.dump(gcp_creds_config, f)

        # Point the Google Auth library to our temporary config file
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config_path
        
        # The auth library now automatically handles the token exchange
        creds, _ = google.auth.default(scopes=SCOPES)
        return build("drive", "v3", credentials=creds)

    # Local development authentication (fallback)
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

def download_file_content(service, file_id: str) -> bytes:
    """Downloads a file's content as bytes."""
    try:
        request = service.files().get_media(fileId=file_id)
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            app_logger.info(f"Download {int(status.progress() * 100)}%.")
        return file_content.getvalue()
    except HttpError as error:
        app_logger.error(f"An error occurred: {error}")
        return None

def make_file_public(service, file_id: str) -> str:
    """Makes a file public and returns its web view link."""
    try:
        service.permissions().create(fileId=file_id, body={'type': 'anyone', 'role': 'reader'}).execute()
        file = service.files().get(fileId=file_id, fields='webContentLink').execute()
        return file.get('webContentLink')
    except HttpError as error:
        app_logger.error(f"An error occurred: {error}")
        return None

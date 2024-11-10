
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
from PIL import Image

class GoogleDriveUtilities:
    def __init__(self):
        pass  

    def connect_google_drive(self):
        # TODO: Implement Google Drive upload logic
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        creds = Credentials.from_service_account_file(
            'client_secrets.json', scopes=SCOPES
        )
        # If there are no (valid) credentials available, let the user log in.

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return build('drive', 'v3', credentials=creds) 
    
    def google_drive_upload(self, image: Image) -> str:
        """Upload image to Google Drive and return image_id"""
        try:
            drive_service = self.connect_google_drive()
            file_metadata = {
                'name': image.filename,
            }
            media = MediaIoBaseUpload(BytesIO(image.read()), mimetype=image.content_type)
            file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return {"message": "Image uploaded successfully", "file_id": file.get('id')}
        except HttpError as error:
            print(f"An error occurred: {error}")
            return {"message": "An error occurred", "error": str(error)}
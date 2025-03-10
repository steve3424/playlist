from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'service_account.json'
PARENT_FOLDER_ID = "176Y2wVsiE2QWGS6Q_olrLu_Ir1Kzywr0"

def authenticate():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return creds

def upload_photo(file_path):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    fileName = os.path.basename("C://Users//eddie//OneDrive//Desktop//Programming//Python//8Days a week.JPG")

    file_metadata = {
        'name' : fileName,
        'parents' : [PARENT_FOLDER_ID]
    }

    file = service.files().create(
        body=file_metadata,
        media_body=file_path
    ).execute()

folderLocation = input(print("Please enter the file location you would like to upload"))

songsToUpload = []

for songFile in os.listdir(folderLocation):
    songsToUpload.append(songFile)

for song in songsToUpload:
    upload_photo(song)
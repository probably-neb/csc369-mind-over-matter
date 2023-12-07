DEFAULT_GDRIVE_URL = "https://drive.google.com/drive/folders/1O2u80vRUtE7VDIFb0azd0WJ1a0INOhMM"

from gdrive import download

download.download_folder(DEFAULT_GDRIVE_URL, None)

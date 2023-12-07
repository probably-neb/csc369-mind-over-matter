"""
Downloads files from Google Drive given the url to a folder.
"""

# TODO: Copy code from gdrive repo https://github.com/wkentaro/gdown/blob/main/gdown/download_folder.py and use private _get_directory_structure function for parallel downloads

def _parse_id_from_url(url: str):
    """
    The file id is the key to downloading any file from Google Drive.
    """
    if "/file/d/" in url:
        return url.split("/file/d/")[1].split("/")[0]
    elif "folders" in url:
        return url.split("/folders/")[1].split("/")[0]
    else:
        raise ValueError("Invalid URL - Could not parse file id")


def download_folder(url: str, out_dir: str):
    import gdown
    gdown.download_folder(url, quiet=False)


# for testing
if __name__ == "__main__":
    DEFAULT_GDRIVE_URL = "https://drive.google.com/drive/folders/1O2u80vRUtE7VDIFb0azd0WJ1a0INOhMM"
    from pathlib import Path
    out_dir = Path("./data/gdrive")
    if not out_dir.exists():
        print("Creating directory for Google Drive database at ./gdrive")
        out_dir.mkdir()
    download_folder(DEFAULT_GDRIVE_URL, out_dir)

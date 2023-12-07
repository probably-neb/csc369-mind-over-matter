"""
Downloads files from Google Drive given the url to a folder.
"""

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

# TODO: Copy code from gdrive repo https://github.com/wkentaro/gdown/blob/main/gdown/download_folder.py and use private _get_directory_structure function for parallel downloads

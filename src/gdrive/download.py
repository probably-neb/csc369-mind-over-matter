from __future__ import annotations
"""
Downloads files from Google Drive given the url to a folder.
"""

from pathlib import Path
import gdown
from sys import stderr
import fitz # pyMuPDF

def download_file(id: str, output: str, quiet=False):
    gdown.download(id=id, output=output, quiet=quiet)

def download_folder(url: str, out_dir: str, quiet=False):
    out_dir = Path(out_dir)
    created = []
    files = list_files_in_folder(url, quiet=quiet)
    for (filename, id) in files:
        out_path = str(out_dir / filename)
        download_file(id, out_path, quiet=quiet)
        created.append(out_path)
    return created


def list_files_in_folder(url: str, quiet=False, proxy=None, use_cookies=True, remaining_ok=False, verify=True) -> [(str, str)]:
    """
    uses gdown internal functions to get the list of files in a folder
    """

    # abusing pythons lack of private methods
    from gdown.download import _get_session
    from gdown.download_folder import _download_and_parse_google_drive_link

    # copied from gdown.download_folder
    sess = _get_session(proxy=proxy, use_cookies=proxy)

    if not quiet:
        print("Retrieving folder contents", file=stderr)
    return_code, gdrive_file = _download_and_parse_google_drive_link(
        sess,
        url,
        quiet=quiet,
        remaining_ok=remaining_ok,
        verify=verify,
    )

    if not return_code:
        return return_code
    file_ids = []
    for file in gdrive_file.children:
        if file.is_folder() or len(file.children) > 0:
            # TODO: recursive download?
            continue
        if not quiet:
            print(file.name, file=stderr)
        file_ids.append((file.name, file.id))
    return file_ids


# for testing
if __name__ == "__main__":
    DEFAULT_GDRIVE_URL = "https://drive.google.com/drive/folders/1O2u80vRUtE7VDIFb0azd0WJ1a0INOhMM"
    out_dir = Path("./data/gdrive")
    if not out_dir.exists():
        print("Creating directory for Google Drive database at ./gdrive")
        out_dir.mkdir()
    download_folder(DEFAULT_GDRIVE_URL, out_dir, quiet=False)

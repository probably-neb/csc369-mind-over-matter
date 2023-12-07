import requests
from io import BytesIO
import zipfile
from pathlib import Path

# Replace these with your FTP server details
ftp_server = 'ftp.ncbi.nlm.nih.gov'
zip_file_name = 'taxdmp.zip'
ftp_file_path = f'/pub/taxonomy/{zip_file_name}'


# TODO: add args to overwrite defaults
def download_latest_ncbi_db(out_dir: str):
    # the repo gives an ftp link but it's also hosted at an https endpoint
    # that doesn't require login or working with ftp...
    remote_path = f"https://{ftp_server}{ftp_file_path}"
    response = requests.get(remote_path)

    response.raise_for_status()

    # TODO: handle overwrites

    zip_path = Path(out_dir) / zip_file_name

    # save zip file just in case
    with open(zip_path, 'wb') as local_file:
        local_file.write(response.content)

    # Unzip the downloaded zip
    zip_content = BytesIO(response.content)

    with zipfile.ZipFile(zip_content, 'r') as zip_ref:
        zip_ref.extractall(out_dir)

# for testing
if __name__ == "__main__":
    out_dir = Path("./data/ncbi")
    if not out_dir.exists():
        print("Creating directory for NCBI database at ./ncbi")
        out_dir.mkdir()
    download_latest_ncbi_db("./ncbi")

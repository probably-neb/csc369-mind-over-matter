import requests
from io import BytesIO
import zipfile
from pathlib import Path
from sys import stderr
import sqlite3

# Replace these with your FTP server details
FTP_SERVER = 'ftp.ncbi.nlm.nih.gov'
ZIP_FILE_NAME = 'taxdmp.zip'
FTP_FILE_PATH = f'/pub/taxonomy/{ZIP_FILE_NAME}'

SQLITE_DB = "ncbi.sqlite"


# TODO: add args to overwrite defaults
def download_latest_ncbi_db(out_dir: str, quiet=False):
    # the repo gives an ftp link but it's also hosted at an https endpoint
    # that doesn't require login or working with ftp...
    remote_path = f"https://{FTP_SERVER}{FTP_FILE_PATH}"
    response = requests.get(remote_path)

    response.raise_for_status()

    # TODO: handle overwrites

    out_path = Path(out_dir)
    zip_path = out_path / ZIP_FILE_NAME

    # save zip file just in case
    with open(zip_path, 'wb') as local_file:
        local_file.write(response.content)

    # Unzip the downloaded zip
    zip_content = BytesIO(response.content)

    with zipfile.ZipFile(zip_content, 'r') as zip_ref:
        created = [str(out_path / filename) for filename in zip_ref.namelist()]
        if not quiet:
            print("Extracting files", file=stderr)
            print("\n".join(created), file=stderr)
        zip_ref.extractall(out_path)
    return created

def process_names_dmp(names_dmp: str):
    if not names_dmp.exists():
        raise FileNotFoundError(f"names.dmp not found at {names_dmp}")
    
    names = {}
    synonyms = {}

    #process the names.dmp
    for line in open(names_dmp, 'r'):
        fields = line.strip().split("\t")
        notion = fields[6]
        taxid = fields[0]
        name = fields[2]

        if notion == "scientific name":
            if taxid not in names:
                names[taxid] = name
        elif notion== "synonym" or notion == "equivalent name":
            if taxid not in synonyms:
                synonyms[taxid] = []
            if name not in synonyms[taxid]:
                synonyms[taxid].append(name)
            
    return (names, synonyms)

def process_nodes_dmp(nodes_dmp: str):

    if not nodes_dmp.exists():
        raise FileNotFoundError(f"names.dmp not found at {names_dmp}")
    # parents and ranks
    pr = {}

    for line in open(nodes_dmp, 'r'):
        fields = line.strip().split("\t")
        
        taxid = fields[0]
        parent = fields[2]
        rank = fields[4]
        
        pr[taxid] = [parent, rank]
    return pr


def create_sqlite_db(out_dir: str, files: [str]):

    folder = Path(out_dir)
    db_path = folder / SQLITE_DB
    if db_path.exists():
        # remove old db
        db_path.unlink()
    conn = sqlite3.connect(db_path)

    names_dmp = folder / "names.dmp"
    names, synonyms = process_names_dmp(names_dmp)

    nodes_dmp = folder / "nodes.dmp"
    parents_and_ranks = process_nodes_dmp(nodes_dmp)

    cursor = conn.cursor()
    cursor.execute('''PRAGMA journal_mode = OFF''')
    cursor.execute("CREATE TABLE tree (taxid integer, name text, parent integer, rank text);")


    taxid_values = []
    for taxid,name in names.items():
        parent,rank = parents_and_ranks.get(taxid, ["0", ""])
        name = name.replace("'", "''")
        value = f"('{taxid}', '{name}', '{parent}', '{rank}')"
        taxid_values.append(value)

    command = f"INSERT INTO tree VALUES {', '.join(taxid_values)};"
    cursor.execute(command)

    ###indexing

    command = "CREATE UNIQUE INDEX taxid_on_tree ON tree(taxid);"
    cursor.execute(command)

    command = "CREATE INDEX name_on_tree ON tree(name);"
    cursor.execute(command)

    command = "CREATE INDEX parent_on_tree ON tree(parent);"
    cursor.execute(command)


    cursor.execute('''PRAGMA journal_mode = OFF''')
    cursor.execute("CREATE TABLE synonym (id integer, taxid integer, name text);")

    synonym_values = []
    for index, synonym in enumerate(synonyms.items()):
        taxid, taxons = synonym
        taxid = str(taxid)
        values = []
        indexes = range(index, index + len(taxons))
        for i, taxon in zip(indexes, taxons):
            taxon = taxon.replace("'", "''")
            value = f"('{id}', '{taxid}', '{taxon}')"
            values.append(value)
        synonym_values.extend(values)
    command = "INSERT INTO synonym VALUES {};"

    # write in chunks of 100
    for i in range(0,len(synonym_values),100):
        cmd = command.format(", ".join(synonym_values[i:i+100]))
        cursor.execute(cmd)


    command = "CREATE INDEX name_on_synonym ON synonym(name);"
    cursor.execute(command)

    command = "CREATE INDEX taxid_on_synonym ON synonym(taxid);"
    cursor.execute(command)

    conn.commit()
    conn.close()


def download(out_dir: str):
    files = download_latest_ncbi_db(out_dir)
    db = create_sqlite_db(out_dir, files)
    return db

# for testing
if __name__ == "__main__":
    out_dir = Path("./data/ncbi")
    if not out_dir.exists():
        print(f"Creating directory for NCBI database at {out_dir}")
        out_dir.mkdir()
    download(out_dir)

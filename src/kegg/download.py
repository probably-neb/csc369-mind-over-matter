from __future__ import annotations
import sys, re, os
import requests
from threading import Thread
import queue
import json

DATABASES = [
    "pathway",
    "brite",
    "module",
    "ko",
    "vg",
    "vp",
    "ag",
    "genome",
    "compound",
    "glycan",
    "reaction",
    "rclass",
    "enzyme",
    "network",
    "variant",
    "disease",
    "drug",
    "dgroup",
    "disease_ja",
    "drug_ja",
    "dgroup_ja",
    "compound_ja",
    "genes",
    "ligand",
    "kegg",
# TODO: handle these?
# <org>
# <outside_db>
]

RX_PREFIX_CATCH = re.compile(r'(\w+):\w+')
KO_LIST_URL = "https://rest.kegg.jp/list/"
MODULE_URL_PREFIX = "https://rest.kegg.jp/get/"

def _download_database(database: str, output_folder: str, quiet=False):
    ko_list_url = KO_LIST_URL + database


    def work(package):
            if not quiet:
                print(MODULE_URL_PREFIX + package)
            response = requests.get(MODULE_URL_PREFIX + package)
            # TODO: retry on failure
            response.raise_for_status()
            detail = response.text

            output_file = os.path.join(output_folder, package.replace(":", "_"))
            with open(output_file, 'a+') as output:
                output.write(detail)

    exists = set()

    # skips files that already exist
    for (head, dirs, files) in os.walk(output_folder):
        for file in files:
            exists.add(file)

    ko_list = requests.get(ko_list_url).text
    if not quiet:
        print(ko_list)

    for line in ko_list.split("\n"):
        fields = line.strip().split("\t")
        if len(fields) == 2:
            kegg = fields[0]
            name = fields[1]
            if kegg.replace(":", "_") not in exists:
                if not quiet:
                    print("Downloading", kegg, name)
                work(kegg)


def download_databses(databases: str | [str] | None, out_dir: str):
    """
    Download a database from KEGG.
    :param database: The database to download, or a list of databases to download. If None, download all databases.
    """
    if isinstance(databases, str):
        databases = [databases]
    elif databases is None:
        databases = DATABASES
    ok = all(db in DATABASES for db in databases)
    if not ok:
        raise ValueError("Invalid database(s) specified. Valid databases are: " + ", ".join(DATABASES))

    for db in databases:
        # TODO: parallelize
        _download_database(db, out_dir)


if __name__ == "__main__":
    from pathlib import Path
    out_dir = Path("./data/kegg")
    if not out_dir.exists():
        out_dir.mkdir()
    download_databses(None, out_dir)


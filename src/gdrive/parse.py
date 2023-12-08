import fitz # pyMuPDF
import re

PAGE_NUM_RGX = re.compile(r"\n\d+\n")

def pdf_to_text(pdf_path: str):
    with fitz.open(pdf_path) as pdf:
        pages = [page.get_text() for page in pdf]
    return "\n".join(pages)


def clean_text(txt: str):
    # just remove page numbers for now...
    return PAGE_NUM_RGX.sub("\n", txt)
    # possible additions:
    # - replace abbreviations (HD -> Huntington's disease)
    # - remove single letter words


def parse_dir(path: str):
    txt_files = []
    for pdf in path.glob("*.pdf"):
        pdf = str(pdf) # convert from pathlib.Path
        txt_content = pdf_to_text(pdf)
        txt_content = clean_text(txt_content)
    
        # TODO: 
        # - clean up txt_content
        #   * files from neo4j_example had all content on one line, this may be the play
        #   * also need to remove excess stuff like licenses, authors, etc.
        # - figure out output format, right now it just dumps to a file but
        #   it probably has to be stored in ray or something

        txt_path = pdf.replace(".pdf", ".txt")
        with open(txt_path, "w") as txt_file:
            # NOTE: no data processing here
            txt_file.write(txt_content)
        txt_files.append(txt_path)

    return txt_files

# for testing
if __name__ == "__main__":
    from pathlib import Path
    out_dir = Path("./data/gdrive")
    if not out_dir.exists():
        print(f"{out_dir} does not exist! can't convert non-existant pdfs!")
        exit(1)

    txt_files = parse_dir(out_dir)
    print(f"Converted {len(txt_files)} pdfs to txt files")
    print("\n".join(txt_files))

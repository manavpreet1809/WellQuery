import os

def write_bytes(path: str, content: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True) # make parent dir
    with open(path, "wb") as f: # open file in binary mode
        f.write(content) # write content to file

def write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True) # make parent dir
    with open(path, "w", encoding="utf-8") as f: # open file in text mode
        f.write(content) # write content to file
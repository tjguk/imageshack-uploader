import os, sys
import csv
import hashlib

def get_signature(filepath):
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

IN_FILEPATH = r"F:\Dad\Photos\uploaded.csv"
OUT_FILEPATH = r"F:\Dad\Photos\uploaded.updated.csv"
with open(IN_FILEPATH, newline="") as f:
    with open(OUT_FILEPATH, "w", newline="") as g:
        reader = csv.reader(f)
        writer = csv.writer(g)

        for (filepath, album, tags, signature) in reader:
            print(filepath)
            if not signature:
                signature = get_signature(filepath)
            writer.writerow([filepath, album, tags, signature])

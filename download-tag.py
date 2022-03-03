import os, sys
import datetime
import glob
from pprint import pprint
import re

import requests

import imageshack

base_url = "https://api.imageshack.com/v2/user/tjguk/tags/"

def main(tag_name=None):
    tjguk = imageshack.ImageShackUser("tjguk")
    tags = tjguk.tags()
    image_ids = tags[tag_name]
    pprint(image_ids)

    dirpath = "imageshack-tag-%s" % tag_name
    os.makedirs(dirpath, exist_ok=True)
    connection = imageshack.ImageShack()
    for image_id in image_ids:
        image_info = connection.image(image_id)
        filename = image_info['original_filename']
        print("Found image", filename)
        filepath = os.path.join(dirpath, filename)
        with open(filepath, "wb") as f:
            f.write(image_info['image_bytes'])
        print("Saved to", filepath)

if __name__ == '__main__':
    main(*sys.argv[1:])

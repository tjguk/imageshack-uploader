import os, sys
import collections
import csv
import datetime
import glob
import hashlib
from pprint import pprint
import re
import time

from PIL import Image, UnidentifiedImageError
import exifread

import imageshack

def normalised(text):
    characters_to_remove = ["'"]
    for c in characters_to_remove:
        text = text.replace(c, "")
    text = " ".join(text.split("_"))
    return text.title()

def extract_datetime(filepath):
    with open(filepath, "rb") as f:
        tags = exifread.process_file(f, details=False, stop_tag="DateTimeOriginal")
        date_time_original = tags.get("EXIF DateTimeOriginal", "")
        try:
            if date_time_original:
                return datetime.datetime.strptime(date_time_original.values, "%Y:%m:%d %H:%M:%S")
            else:
                return None
        except ValueError:
            return None

def extract_dimensions(filepath):
    try:
        image = Image.open(filepath)
    except UnidentifiedImageError:
        return (0, 0)
    else:
        return image.size

def read_uploaded_images(csv_filepath):
    print("Reading uploaded images from", csv_filepath)
    if not os.path.exists(csv_filepath):
        return list()
    with open(csv_filepath, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_uploaded_images(csv_filepath, images):
    print("Writing uploaded images to", csv_filepath)
    if not images:
        return
    headers = list(images[0].keys())
    with open(csv_filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows([image[h] for h in headers] for image in images)

def get_signature(filepath):
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def upload(root_filepath, already_uploaded, signatures):
    image_shack = imageshack.ImageShack()
    user = imageshack.ImageShackUser()
    albums = user.albums()

    print("About to walk", root_filepath)
    for dirpath, dirnames, filenames in os.walk(root_filepath):
        #
        # Crude way of skipping certain folders
        #
        if any(i.startswith("=") for i in dirpath.split(os.sep)):
            print("Skipping", dirpath)
            continue
        else:
            print(">", dirpath)
            album_name = normalised(os.path.basename(dirpath))

        filepaths = [os.path.join(dirpath, filename).lower() for filename in filenames if filename.lower().endswith(".jpg")]
        for filepath in filepaths:
            print(filepath, "...", end=" ")

            #
            # Don't upload if already uploaded by path name
            #
            if filepath in already_uploaded:
                print("Already uploaded; skipping")
                continue

            #
            # Don't upload if already uploaded by signature
            #
            signature = get_signature(filepath)
            if signature in signatures:
                print("Already uploaded as", signatures[signature])
                continue

            #
            # Don't upload if it appears to be a thumbnail
            #
            width, height = extract_dimensions(filepath)
            if width < 300:
                print("Probably a thumbnail; skipping")
                continue

            filename, ext = os.path.splitext(os.path.basename(filepath))
            name = normalised(filename)
            timestamp = extract_datetime(filepath)
            if timestamp:
                tags = [timestamp.strftime("%Y")]
            else:
                tags = []

            for retry in range(3):
                try:
                    response = image_shack.upload(filepath, name, album_name, tags)
                except imageshack.ImageShackError as err:
                    response = err.response
                    pprint(response.json())
                except imageshack.ImageShackConnectionError as err:
                    print("Connection error; retrying after a delay...", end = " ")
                    time.sleep(5.0)
                    continue
                else:
                    yield dict(filepath=filepath, album=album_name, tags=",".join(tags), signature=signature)
                    print("uploaded")
                break

def main(root_filepath=r"F:\Dad\Photos", uploaded_filepath=None):
    csv_filepath = uploaded_filepath or os.path.join(root_filepath, "uploaded.csv")
    images = read_uploaded_images(csv_filepath)

    #
    # Build a list of signatures
    #
    signatures = collections.defaultdict(set)
    for image in images:
        sig = image['signature'].strip()
        if sig:
            signatures[sig].add(image['filepath'])

    try:
        for image_info in upload(root_filepath, already_uploaded = set(image['filepath'].lower() for image in images), signatures=signatures):
            images.append(image_info)
            signatures[image_info['signature']].add(image_info['filepath'])

    except KeyboardInterrupt:
        print("Closing gracefully...")
    finally:
        write_uploaded_images(csv_filepath, images)

if __name__ == '__main__':
    main(*sys.argv[1:])

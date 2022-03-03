import os, sys
import datetime
import glob
from pprint import pprint
import re

import requests

from creds import *

BASE_URL = "https://api.imageshack.com/v2/"

class ImageShackError(Exception):
    def __init__(self, response):
        self.response = response

class ImageShackConnectionError(Exception): pass

class ImageShack:

    def __init__(self, username=USERNAME, auth_token=AUTH_TOKEN, api_key=API_KEY):
        self.username = username
        self.auth_token = auth_token
        self.api_key = api_key
        self.base_url = BASE_URL

    def get(self, relative_url, **kwargs):
        url = self.base_url + relative_url
        params = {"api_key" : self.api_key, "auth_token" : self.auth_token} ##, "public" : False}
        params.update(kwargs)
        try:
            response = requests.get(url, params=params)
        except requests.exceptions.ConnectionError:
            raise ImageShackConnectionError()
        if not response.json()['success']:
            raise ImageShackError(response)
        return response

    def post(self, relative_url, **kwargs):
        url = self.base_url + relative_url
        params = {"auth_token" : self.auth_token, "api_key" : self.api_key}
        files = dict(("File %s" % i, f) for (i, f) in enumerate(kwargs.pop("files", []), 1))
        params.update(kwargs)
        try:
            response = requests.post(url, data=params, files=files)
        except requests.exceptions.ConnectionError:
            raise ImageShackConnectionError()
        if not response.json()['success']:
            raise ImageShackError(response)
        return response

    def create_album(self, album_name):
        return self.post("albums", title=album_name)

    def upload(self, filepath, name, album_name, tags):
        with open(filepath, "rb") as f:
            return self.post(
                "images",
                files=[f],
                album=album_name,
                title=name,
                tags=",".join(tags),
                public=False
            )

    def image(self, image_id):
        response = self.get("images/%s" % image_id)
        info = response.json()['result']
        image_url = "http://" + info['direct_link']
        filename = info['original_filename']
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        info['image_bytes'] = bytes(image_response.content)
        return info

class ImageShackUser(ImageShack):

    def __init__(self, username=USERNAME, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = username
        self.base_url += "/user/" + self.username + "/"

    def albums(self):
        response = self.get("albums", show_private=True)
        albums = response.json()['result']['albums']
        return dict((a['id'], a['title']) for a in albums)

    def tags(self):
        response = self.get("tags", limit=1000000, offset=0, image_limit=50)
        tags = response.json()['result']['tags']
        tag_info = {}
        for tag, info in tags.items():
            images = info['images']
            tag_info[tag] = [image['id'] for image in images]
        return tag_info

    def tag_images(self, tag_name):
        response = self.get("tags/%s" % tag_name, limit=1000000, offset=0)
        return response.json()['result']

if __name__ == '__main__':
    #
    # By way of a sanity check, attempt to connect to ImageShack
    #
    shack = ImageShack()
    print("Connected to %s with username %s" % (shack.base_url, shack.username))

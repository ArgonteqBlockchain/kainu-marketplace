import base64
import json
import os
import uuid

from rest_framework.exceptions import APIException

from src.games.exceptions import LengthMismatch
from src.store.services.ipfs import send_to_ipfs


def base64_to_ipfs(data):
    filename = str(uuid.uuid4())
    img_extensions = [
        "jpeg",
        "jpg",
        "png",
        "svg+xml",
    ]
    try:
        extension_found = False
        for ext in img_extensions:
            pattern = f"data:image/{ext};base64,"
            if data.find(pattern) >= 0:
                data = data.replace(pattern, "")
                if ext == "svg+xml":
                    ext = "svg"
                filename = filename + "." + ext
                extension_found = True
                break
        if not extension_found:
            raise Exception()

        file_path = f"{os.path.dirname(os.path.dirname(os.path.dirname(__file__)))}/static/media/{filename}"
        with open(file_path, "wb") as out_file:
            out_file.write(base64.b64decode(data))
        file = open(file_path, "rb")
        ipfs_hash = send_to_ipfs(file)
        os.remove(file_path)
        return ipfs_hash
    except Exception:
        raise APIException(detail="invalid picture")


def base64_to_json(data):
    try:
        data = data.replace("data:application/json;base64", "")
        decoded = json.loads(base64.b64decode(data))
        return decoded
    except Exception:
        raise APIException(detail="invalid json")


def get_photos_ipfs_list(game, photos, field):
    current_photos = getattr(game, field) or []
    # check that lengths match
    if field == "photos_ipfs" and not len(current_photos) == (
        photos.count(True)
        + photos.count(False)
        + photos.count("true")
        + photos.count("false")
    ):
        raise LengthMismatch
    res_list = []
    # leave image if True, delete if False, add if base64
    for index, photo in enumerate(photos):
        if photo in ["true", True]:
            res_list.append(current_photos[index])
        elif photo in ["false", False]:
            continue
        else:
            res_list.append(base64_to_ipfs(photo))
    return res_list

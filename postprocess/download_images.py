import json
import os
import urllib
from PIL import Image
from multiprocessing import Pool

dialogues_file = '/Users/harmdevries/Documents/multimodal_dialogue/data/guesswhat_postprocessed.jsonl'
out_dir = '/Users/harmdevries/guesswhat_images/'


def is_corrupted(file):
    try:
        im = Image.open(file).convert('RGB')
    except Exception:
        print 'Corrupted {}'.format(file)
        return True
    return False


def download(url, path):
    try:
        urllib.urlretrieve(url, path)
        return True
    except Exception:
        return False


def download_image(picture_id):
    img_file = '{}.jpg'.format(picture_id)
    image_url = 'https://msvocds.blob.core.windows.net/imgs/{}'.format(img_file)
    out_file = os.path.join(out_dir, img_file)
    if not os.path.isfile(out_file) or is_corrupted(out_file):
        for i in range(3):
            if download(image_url, out_file):
                break
            print(image_url)

total = 0
duplicates = 0
picture_ids = []

with open(dialogues_file) as f:
    for line in f:
        total += 1
        dialogue = json.loads(line)
        if dialogue['picture_id'] not in picture_ids:
            picture_ids.append(dialogue['picture_id'])

print len(picture_ids)
print total
pool = Pool()
pool.map(download_image, picture_ids)

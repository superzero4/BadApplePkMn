import math
from concurrent import futures
from PIL import Image
import numpy as np
from pathlib import Path
import os


class BACard:
    def __init__(self, a):
        self.card_id = Path(a).stem
        self.card_pixels = np.asarray(Image.open(a))
        self.card_image = Image.open('full cards/' + self.card_id + '.png').resize((120, 165))

    def compare(self, i):
        pixels = []
        for y in range(2):
            for x in range(2):
                temp_avg = 0
                for rgb in range(3):
                    if rgb == 0: mod = 0.3
                    if rgb == 1: mod = 0.59
                    if rgb == 2: mod = 0.11
                    temp_avg += math.pow((int(self.card_pixels[y][x][rgb]) - int(i[y][x][rgb])) * mod, 2)
                pixels.append(temp_avg)
        return pixels[0] + pixels[1] + pixels[2] + pixels[3]


class Frame:
    def __init__(self, a):
        self.full_frame = a

    def getarray(self, x, y):
        assert x * 2 <= len(self.full_frame[1]) and x >= 0
        assert y * 2 <= len(self.full_frame) and y >= 0
        return self.full_frame[y * 2:y * 2 + 2, x * 2:x * 2 + 2]


def find(x, y, cardpool, frame, black, white, skip):
    distance = 881023
    curcard = None
    if skip:
        if (frame.getarray(x, y) == [[[255, 255, 255], [255, 255, 255]], [[255, 255, 255], [255, 255, 255]]]).all():
            return white.pop(0)
        if (frame.getarray(x, y) == [[[0, 0, 0], [0, 0, 0]], [[0, 0, 0], [0, 0, 0]]]).all():
            return black.pop(0)
    for card in cardpool:
        compare = card.compare(frame.getarray(x, y))
        if distance > compare:
            distance = compare
            curcard = card
    return curcard


def run(url, cards, black_cards, white_cards, height, width):
    image = Image.open(url).resize((width * 2, height * 2)).convert("RGB")
    frame = Frame(np.asarray(image))
    curframe = []
    cardpool = cards.copy()
    black = black_cards.copy()
    white = white_cards.copy()
    for y in range(height):
        curframe.append([])
        for x in range(width):
            curcard = find(x, y, cardpool, frame, black, white, True)
            if curcard in cardpool:
                cardpool.remove(curcard)
            if curcard in black:
                black.remove(curcard)
            if curcard in white:
                white.remove(curcard)
            image = np.asarray(curcard.card_image.convert("RGBA"))
            curframe[y].append(image)
    yframe = []
    for y in range(height):
        yframe.append(curframe[y][0])
        for x in range(width - 1):
            yframe[y] = (np.concatenate((yframe[y], curframe[y][x + 1]), axis=1))
    out = yframe[0]
    for y in range(height - 1):
        out = (np.concatenate((out, yframe[y + 1]), axis=0))
    imgs_comb = Image.fromarray(out)
    print("saving " + Path(url).stem)
    imgs_comb.save('render/' + Path(url).stem + '.png')


if __name__ == "__main__":
    height = 14
    width = round(height * (8.8 / (.75 * 6.3))) 
    cards = []
    print("loading cards")
    for card in os.listdir('pokemon cards'):
        cards.append(BACard('pokemon cards/' + card))
    temparray = cards.copy()
    black_cards = []
    white_cards = []
    temp_frame = Frame(np.asarray(Image.open('black.bmp')))
    print("sorting black cards")
    for i in range(height * width):
        temp_card = find(0, 0, temparray, temp_frame, [], [], False)
        black_cards.append(temp_card)
        temparray.remove(temp_card)
    temp_frame = Frame(np.asarray(Image.open('white.bmp')))
    print("sorting white cards")
    for i in range(height * width):
        temp_card = find(0, 0, temparray, temp_frame, [], [], False)
        white_cards.append(temp_card)
        temparray.remove(temp_card)
    frames = os.listdir('frames')
    print("beginning render")
    with futures.ProcessPoolExecutor(max_workers=12) as executor:
        jobs = {}
        files_left = len(frames)
        files_iter = iter(frames)

        while files_left:
            for this_file in files_iter:
                job = executor.submit(run, ("frames/" + this_file), cards, black_cards, white_cards, height, width)
                jobs[job] = this_file
                if len(jobs) > 24:
                    break

            for job in futures.as_completed(jobs):
                files_left -= 1
                del jobs[job]
                break

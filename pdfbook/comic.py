import os.path
import re

from wand.image import Image
import sys
import zipfile
import rarfile
from yaml import load, Loader
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import paginator

MAX_BOOK_SIZE = 128
global config


def full_path(base_file):
    return os.path.join(os.path.dirname(config['configfile']), base_file)


if len(sys.argv) <= 1:
    Tk().withdraw()
    configfile = askopenfilename()
else:
    configfile = sys.argv[1]
config = load(open(configfile, 'r'), Loader)
config['configfile'] = configfile
n_up = config['n_up']
pages_per_signature = config['pages_per_signature']
input_filenames = [full_path(x) for x in config['files']]
output_filename = re.sub("\\.pdf", "", config['output_filename'])

output = Image()
books_count = 1
cbz = None
for input_filename in input_filenames:
    pages = Image()
    split = None
    if zipfile.is_zipfile(input_filename):
        cbz = zipfile.ZipFile(input_filename)
    elif rarfile.is_rarfile(input_filename):
        cbz = rarfile.RarFile(input_filename)
    else:
        print(f"Can't read {input_filename}")
        exit(1)
    for name in cbz.namelist():
        # print(f"filename: {name}", end=None, flush=False)
        if re.search(".*\\.(jpg|png)", name) is None:
            continue
        page_blob = cbz.read(name)
        page = Image(blob=page_blob)
        page.resolution = (96.0, 96.0)
        # print(f"({page.width} x {page.height})")
        if page.width > page.height:
            print(f"over-wide page. splitting.")
            page1 = page[0:int(page.width/2), 0:page.height]
            page2 = page[int(page.width/2):page.width, 0:page.height]
            if split is not None and split != len(pages.sequence) % 2:
                print(f"split book is imbalanced on file {name} from {input_filename}. You gotta deal with it.")
                exit(1)
            split = len(pages.sequence) % 2
            pages.sequence.append(page1)
            pages.sequence.append(page2)
        else:
            pages.sequence.append(page)
    if split is not None and split == 1:
        print(f"Adding blank page to balance split.")
        output.sequence.append(Image(height=pages.sequence[0].height,
                                     width=pages.sequence[0].width,
                                     resolution=pages.sequence[0].resolution))
    print(f"Adding {len(pages.sequence)} pages.")
    output.sequence.extend(pages.sequence)
    pages.close()
    while len(output.sequence) >= MAX_BOOK_SIZE:
        # if we have too many pages, take the remainder and put them in the beginning of
        # the next book.
        next_book = Image()
        next_book.sequence.extend(output.sequence[MAX_BOOK_SIZE:])
        output.sequence = output.sequence[:MAX_BOOK_SIZE]
        print(f"writing out book {output_filename}_{books_count:03d}.pdf")
        print(f"Saving {len(next_book.sequence)} pages for next book")
        paginator.write_paginated_images(output, n_up,
                                         pages_per_signature,
                                         full_path(f"{output_filename}_{books_count:03d}.pdf"))
        books_count += 1
        output.close()
        output = next_book
if books_count > 1:
    print(f"writing out book {output_filename}_{books_count:03d}.pdf")
    paginator.write_paginated_images(output, n_up,
                                     pages_per_signature,
                                     full_path(f"{output_filename}_{books_count:03d}.pdf"))
else:
    paginator.write_paginated_images(output, n_up, pages_per_signature, full_path(f"{output_filename}.pdf"))
output.close()
cbz.close()

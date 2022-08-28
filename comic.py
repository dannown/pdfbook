import os.path
import re

from wand.image import Image
import sys
import zipfile
import rarfile
from yaml import load
from yaml import Loader, Dumper

import paginator

MAX_BOOK_SIZE = 128


def full_path(basefile):
    return os.path.join(os.path.dirname(sys.argv[1]), basefile)


filename = sys.argv[1]
config = load(open(filename, 'r'), Loader)
n_up = config['n_up']
pages_per_signature = config['pages_per_signature']
input_filenames = [full_path(x) for x in config['files']]
output_filename = re.sub("\\.pdf", "", config['output_filename'])

output = Image()
books_count = 1
for input_filename in input_filenames:
    if zipfile.is_zipfile(input_filename):
        cbz = zipfile.ZipFile(input_filename)
    elif rarfile.is_rarfile(input_filename):
        cbz = rarfile.RarFile(input_filename)
    for name in cbz.namelist():
        print(f"filename: {name}", end=None, flush=False)
        if re.search(".*\\.(jpg|png)", name) is None:
            continue
        bytes = cbz.read(name)
        page = Image(blob=bytes)
        page.resolution = (96.0, 96.0)
        print(f"({page.width} x {page.height})")
        if page.width > page.height:
            print(f"over-wide page. splitting")
            page1 = page[0:int(page.width/2), 0:page.height]
            page2 = page[int(page.width/2):page.width, 0:page.height]
            if len(output.sequence) % 2 != 1:
                print("split page is out of sequence. adding blank.")
                output.sequence.append(Image(height=page1.height, width=page1.width, resolution=page1.resolution))
            output.sequence.append(page1)
            output.sequence.append(page2)
        else:
            output.sequence.append(page)
        if len(output.sequence) >= MAX_BOOK_SIZE:
            # if we have too many pages, take the remainder and put them in the beginning of
            # the next book.
            next_book = Image()
            next_book.sequence.extend(output.sequence[MAX_BOOK_SIZE:])
            output.sequence = output.sequence[:MAX_BOOK_SIZE]
            print(f"writing out book {output_filename}_{books_count:03d}.pdf")
            paginator.write_paginated_images(output, n_up, pages_per_signature, full_path(f"{output_filename}_{books_count:03d}.pdf"))
            books_count += 1
            output.close()
            output = next_book
if books_count > 1:
    print(f"writing out book {output_filename}_{books_count:03d}.pdf")
    paginator.write_paginated_images(output, n_up, pages_per_signature, full_path(f"{output_filename}_{books_count:03d}.pdf"))
else:
    paginator.write_paginated_images(output, n_up, pages_per_signature, full_path(f"{output_filename}.pdf"))
output.close()
cbz.close()

import re

from wand.image import Image
import sys
import zipfile
import paginator

MAX_BOOK_SIZE = 128

n_up = int(sys.argv[1])
pages_per_signature = int(sys.argv[2])
input_filename = sys.argv[3]
output_filename = re.sub("\\.pdf", "", sys.argv[4])

if not zipfile.is_zipfile(input_filename):
    exit(1)
cbz = zipfile.ZipFile(input_filename)
books_count = 1
output = Image()
for name in cbz.namelist():
    print(f"filename: {name}", end=None, flush=False)
    if re.search(".*\\.(jpg|png)", name) is None:
        continue
    page = Image(file=cbz.open(name))
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
        paginator.write_paginated_images(output, n_up, pages_per_signature, f"{output_filename}_{books_count:03d}.pdf")
        books_count += 1
        output.close()
        output = next_book
if books_count > 1:
    print(f"writing out book {output_filename}_{books_count:03d}.pdf")
    paginator.write_paginated_images(output, n_up, pages_per_signature, f"{output_filename}_{books_count:03d}.pdf")
else:
    paginator.write_paginated_images(output, n_up, pages_per_signature, f"{output_filename}.pdf")
output.close()
cbz.close()

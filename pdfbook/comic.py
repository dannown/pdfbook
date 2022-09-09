import re

from wand.image import Image
from wand.resource import limits as wand_limits
import sys
import zipfile
import rarfile
from tkinter import Tk
from tkinter.filedialog import askopenfilename

from paginator import Paginator
from config import Config

wand_limits['memory'] = 1024 * 1024 * 1024 * 10  # ten gibibytes
if len(sys.argv) <= 1:
    Tk().withdraw()
    configfile = askopenfilename()
else:
    configfile = sys.argv[1]
config = Config(configfile)
pdf_output = Image()
books_count = 1
cbz = None
paginator = Paginator(num_up=config.config_dict['n_up'], pages_per_signature=config.config_dict['pages_per_signature'])

for file_config in config.files():
    file_pages = Image()
    if zipfile.is_zipfile(file_config.file_name()):
        cbz = zipfile.ZipFile(file_config.file_name())
    elif rarfile.is_rarfile(file_config.file_name()):
        cbz = rarfile.RarFile(file_config.file_name())
    else:
        print(f"Can't read {file_config.file_name()}")
        exit(1)

    # get optional blank page
    paginator.blank = Image(blob=cbz.read(file_config.blank())) if file_config.blank() is not None else None

    name_list = cbz.namelist().copy()
    name_list.sort()
    for name in name_list:
        if re.search(".*\\.(jpg|png)", name) is None:
            continue
        if file_config.should_skip(name):
            print(f"Skipping page {name}")
            continue
        page_blob = cbz.read(name)
        page = Image(blob=page_blob)
        if page.width > page.height:
            print(f"over-wide page. splitting {name}.")
            page1 = page[0:int(page.width/2), 0:page.height]
            page2 = page[int(page.width/2):page.width, 0:page.height]
            if (len(file_pages.sequence) + len(pdf_output.sequence)) % 2 != 1:
                print(f"split book is imbalanced on file {name} from {file_config.file_name()}. "
                      f"You gotta deal with it.")
                exit(1)
            file_pages.sequence.append(page1)
            file_pages.sequence.append(page2)
        else:
            file_pages.sequence.append(page)
        if file_config.insert_after(name):
            if paginator.blank is not None:
                file_pages.sequence.append(paginator.blank)
            else:
                file_pages.sequence.append(Image(height=file_pages.sequence[0].height,
                                                 width=file_pages.sequence[0].width,
                                                 resolution=file_pages.sequence[0].resolution))

    print(f"Adding {len(file_pages.sequence)} pages.")
    pdf_output.sequence.extend(file_pages.sequence)
    file_pages.close()
    while len(pdf_output.sequence) >= file_config.max_book_size():
        # if we have too many pages, take the remainder and put them in the beginning of
        # the next book.
        next_book = Image()
        next_book.sequence.extend(pdf_output.sequence[file_config.max_book_size():])
        pdf_output.sequence = pdf_output.sequence[:file_config.max_book_size()]
        output_file_name = file_config.output_file_name(f"{books_count:03d}")
        if file_config.should_print(f"{books_count:03d}"):
            print(f"writing out book {output_file_name}")
            print(f"Saving {len(next_book.sequence)} pages for next book")
            paginator.write_paginated_images(pdf_output, output_file_name)
        else:
            print(f"skipping book {output_file_name}")
        books_count += 1
        pdf_output.close()
        pdf_output = next_book

if books_count > 1:
    if file_config.should_print(f"{books_count:03d}"):
        print(f"writing out book {config.config_dict['output_filename']}_{books_count:03d}.pdf")
        paginator.write_paginated_images(pdf_output,
                                         config.full_path(f"{config.config_dict['output_filename']}_{books_count:03d}.pdf"))
else:
    paginator.write_paginated_images(pdf_output,
                                     config.full_path(f"{config.config_dict['output_filename']}.pdf"))
pdf_output.close()
cbz.close()

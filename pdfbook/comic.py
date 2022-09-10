import re

from PIL import Image
import sys
import zipfile
import rarfile
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from io import BytesIO

from paginator import Paginator
from config import Config

if len(sys.argv) <= 1:
    Tk().withdraw()
    configfile = askopenfilename()
else:
    configfile = sys.argv[1]
config = Config(configfile)
pdf_output = []
books_count = 1
cbz = None
paginator = Paginator(num_up=config.config_dict['n_up'], pages_per_signature=config.config_dict['pages_per_signature'])

for file_config in config.files():
    file_pages = []
    if zipfile.is_zipfile(file_config.file_name()):
        cbz = zipfile.ZipFile(file_config.file_name())
    elif rarfile.is_rarfile(file_config.file_name()):
        cbz = rarfile.RarFile(file_config.file_name())
    else:
        print(f"Can't read {file_config.file_name()}")
        exit(1)

    # get optional blank page
    paginator.blank = Image.open(BytesIO(cbz.read(file_config.blank()))) if file_config.blank() is not None else None

    name_list = cbz.namelist().copy()
    name_list.sort()
    for name in name_list:
        if file_config.print_all_file_names():
            print(f"file: {name}")
        if re.search(".*\\.(jpg|png)", name) is None:
            continue
        if file_config.should_skip(name):
            print(f"Skipping page {name}")
            continue
        page_blob = cbz.read(name)
        page = Image.open(BytesIO(page_blob))
        # insert a page before. if this page is too wide, insert a half-width.
        if file_config.insert_before(name):
            if paginator.blank is None:
                if page.width > page.height:
                    paginator.blank = Image.new("RGB", (int(page.width / 2), page.height), file_config.blank_color())
                else:
                    paginator.blank = Image.new("RGB", (page.width, page.height), file_config.blank_color())
            file_pages.append(paginator.blank)

        if page.width > page.height:
            print(f"over-wide page. splitting {name}.")
            page1 = page.crop((0, 0, int(page.width / 2), page.height))
            page2 = page.crop((int(page.width / 2), 0, page.width, page.height))
            if (len(file_pages) + len(pdf_output)) % 2 != 1:
                print(f"split book is imbalanced on file {name} from {file_config.file_name()}. "
                      f"You gotta deal with it.")
                exit(1)
            file_pages.append(page1)
            file_pages.append(page2)
        else:
            file_pages.append(page)
        if file_config.insert_after(name):
            if paginator.blank is not None:
                file_pages.append(paginator.blank)
            else:
                file_pages.append(Image.new("RGB", (file_pages[0].width, file_pages[0].height), "white"))

    print(f"Adding {len(file_pages)} pages.")
    pdf_output.extend(file_pages)
    while len(pdf_output) >= file_config.max_book_size():
        # if we have too many pages, take the remainder and put them in the beginning of
        # the next book.
        next_book = []
        next_book.extend(pdf_output[file_config.max_book_size():])
        pdf_output = pdf_output[:file_config.max_book_size()]
        output_file_name = file_config.output_file_name(f"{books_count:03d}")
        if file_config.should_print(f"{books_count:03d}"):
            print(f"writing out book {output_file_name}")
            print(f"Saving {len(next_book)} pages for next book")
            paginator.write_paginated_images(pdf_output, output_file_name)
        else:
            print(f"skipping book {output_file_name}")
        books_count += 1
        pdf_output = next_book

if books_count > 1:
    if config.should_print(f"{books_count:03d}"):
        print(f"writing out book {config.config_dict['output_filename']}_{books_count:03d}.pdf")
        paginator.write_paginated_images(pdf_output,
                                         config.full_path(
                                             f"{config.config_dict['output_filename']}_{books_count:03d}.pdf"))
else:
    paginator.write_paginated_images(pdf_output,
                                     config.full_path(f"{config.config_dict['output_filename']}.pdf"))
cbz.close()

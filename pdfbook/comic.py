import os.path
import re

from wand.image import Image
from wand.resource import limits as wand_limits
import sys
import zipfile
import rarfile
from yaml import load, Loader
from tkinter import Tk
from tkinter.filedialog import askopenfilename

from paginator import Paginator

MAX_BOOK_SIZE = 128
global config


def full_path(base_file):
    return os.path.join(os.path.dirname(config['configfile']), base_file)


def should_skip(file_name):
    if 'skip' in config['file_config'] and \
            re.search(config['file_config']["skip"], os.path.basename(file_name)) is not None:
        return True
    if 'skip' in config and re.search(config["skip"], os.path.basename(file_name)) is not None:
        return True


def insert_after(file_name):
    if 'insert_after' in config['file_config'] and \
            re.search(config['file_config']['insert_after'], os.path.basename(file_name)) is not None:
        return True
    if 'insert_after' in config and re.search(config['insert_after'], os.path.basename(file_name)) is not None:
        return True


wand_limits['memory'] = 1024 * 1024 * 1024 * 10  # ten gibibyte
if len(sys.argv) <= 1:
    Tk().withdraw()
    configfile = askopenfilename()
else:
    configfile = sys.argv[1]
config = load(open(configfile, 'r'), Loader)
config['max_book_size'] = config['max_book_size'] if 'max_book_size' in config else MAX_BOOK_SIZE
config['configfile'] = configfile
if 'output_filename' in config:
    config['output_filename'] = re.sub("\\.pdf", "", config['output_filename'])
elif 'name' in config:
    config['output_filename'] = config['name']
if 'skip' in config:
    if isinstance(config['skip'], list):
        config['skip'] = '|'.join(config['skip'])
    print(f"skipping {config['skip']}")
if 'insert_after' in config:
    if isinstance(config['insert_after'], list):
        joined = '|'.join(config['insert_after'])
        config['insert_after'] = joined
config['file_config'] = None


def setup_file_config(file_config):
    if isinstance(file_config, str):
        config['file_config'] = {'name': file_config}
    else:
        if 'skip' in file_config:
            if isinstance(file_config['skip'], str):
                file_config['skip'] = '|'.join([file_config['skip'], config['skip']])
            else:
                file_config['skip'].append(config['skip'])
                file_config['skip'] = '|'.join(file_config['skip'])
        if 'insert_after' in file_config:
            if isinstance(file_config['insert_after'], str):
                if 'insert_after' in config:
                    file_config['insert_after'] = '|'.join([file_config['insert_after'], config['insert_after']])
            else:
                file_config['insert_after'].append(config['insert_after'])
                file_config['insert_after'] = '|'.join(file_config['insert_after'])
        config['file_config'] = file_config


output = Image()
books_count = 1
cbz = None
paginator = Paginator(num_up=config['n_up'],
                      pages_per_signature=config['pages_per_signature'])
for file in config['files']:
    setup_file_config(file)
    input_filename = full_path(config['file_config']['name'])
    pages = Image()
    split = None
    if zipfile.is_zipfile(input_filename):
        cbz = zipfile.ZipFile(input_filename)
    elif rarfile.is_rarfile(input_filename):
        cbz = rarfile.RarFile(input_filename)
    else:
        print(f"Can't read {input_filename}")
        exit(1)
    if 'blank' in config['file_config']:
        config['file_config']['blank'] = Image(blob=cbz.read(config['file_config']['blank']))
    paginator.blank = config['file_config']['blank'] if 'blank' in config['file_config'] else None
    name_list = cbz.namelist().copy()
    name_list.sort()
    for name in name_list:
        if re.search(".*\\.(jpg|png)", name) is None:
            continue
        if should_skip(name):
            print(f"Skipping page {name}")
            continue
        page_blob = cbz.read(name)
        page = Image(blob=page_blob)
        page.resolution = (96.0, 96.0)
        # print(f"({page.width} x {page.height})")
        if page.width > page.height:
            print(f"over-wide page. splitting {name}.")
            page1 = page[0:int(page.width/2), 0:page.height]
            page2 = page[int(page.width/2):page.width, 0:page.height]
            print(f"{len(pages.sequence)} in this book, and {len(output.sequence)} in the section so far.")
            tmp_split = (len(pages.sequence) + len(output.sequence)) % 2
            if split is not None and split != tmp_split:
                print(f"split book is imbalanced on file {name} from {input_filename}. You gotta deal with it.")
                exit(1)
            split = tmp_split
            pages.sequence.append(page1)
            pages.sequence.append(page2)
        else:
            pages.sequence.append(page)
        if insert_after(name):
            if 'blank' in config['file_config']:
                pages.sequence.append(config['file_config']['blank'])
            else:
                pages.sequence.append(Image(height=pages.sequence[0].height,
                                            width=pages.sequence[0].width,
                                            resolution=pages.sequence[0].resolution))

    if split is not None and split == 0:
        print(f"Adding blank page to balance split.")
        if 'blank' in config['file_config']:
            output.sequence.append(config['file_config']['blank'])
        else:
            output.sequence.append(Image(height=pages.sequence[0].height,
                                         width=pages.sequence[0].width,
                                         resolution=pages.sequence[0].resolution))
    print(f"Adding {len(pages.sequence)} pages.")
    output.sequence.extend(pages.sequence)
    pages.close()
    while len(output.sequence) >= config['max_book_size']:
        # if we have too many pages, take the remainder and put them in the beginning of
        # the next book.
        next_book = Image()
        next_book.sequence.extend(output.sequence[config['max_book_size']:])
        output.sequence = output.sequence[:config['max_book_size']]
        if 'only_print' not in config or re.search(config['only_print'], f"{books_count:03d}"):
            print(f"writing out book {config['output_filename']}_{books_count:03d}.pdf")
            print(f"Saving {len(next_book.sequence)} pages for next book")
            paginator.write_paginated_images(output,
                                             full_path(f"{config['output_filename']}_{books_count:03d}.pdf"))
        else:
            print(f"skipping book {config['output_filename']}_{books_count:03d}.pdf")
        books_count += 1
        output.close()
        output = next_book
if books_count > 1:
    print(f"writing out book {config['output_filename']}_{books_count:03d}.pdf")
    paginator.write_paginated_images(output,
                                     full_path(f"{config['output_filename']}_{books_count:03d}.pdf"))
else:
    paginator.write_paginated_images(output,
                                     full_path(f"{config['output_filename']}.pdf"))
output.close()
cbz.close()

from __future__ import annotations
from yaml import load, Loader
import re
import os

MAX_BOOK_SIZE = 128


class Config:
    def file_name(self):
        return self.full_path(self.config['name'])

    def output_file_name(self, book_number):
        return self.full_path(f"{self.config['output_filename']}_{book_number}.pdf")

    def blank(self):
        return self.config['blank'] if 'blank' in self.config else None

    def insert_after(self, file_name):
        if 'insert_after' in self.config and \
                re.search(self.config['insert_after'], os.path.basename(file_name)) is not None:
            return True

    def should_skip(self, file_name):
        if 'skip' in self.config and re.search(self.config["skip"], os.path.basename(file_name)) is not None:
            return True

    def full_path(self, base_file):
        return os.path.join(os.path.dirname(self.config['configfile']), base_file)

    def max_book_size(self):
        return self.config['max_book_size']

    def should_print(self, book_number):
        return 'only_print' not in self.config or re.search(self.config['only_print'], book_number)

    def __init__(self, filename: str):
        self.config = load(open(filename, 'r'), Loader)
        self.config['max_book_size'] = self.config['max_book_size'] if 'max_book_size' in self.config else MAX_BOOK_SIZE
        self.config['configfile'] = filename
        if 'output_filename' in self.config:
            self.config['output_filename'] = re.sub("\\.pdf", "", self.config['output_filename'])
        elif 'name' in self.config:
            self.config['output_filename'] = self.config['name']
        if 'skip' in self.config:
            if isinstance(self.config['skip'], list):
                self.config['skip'] = '|'.join(self.config['skip'])
            print(f"skipping {self.config['skip']}")
        if 'insert_after' in self.config:
            if isinstance(self.config['insert_after'], list):
                joined = '|'.join(self.config['insert_after'])
                self.config['insert_after'] = joined
        self.config['file_config'] = None

    def files(self) -> list[Config]:
        files = []
        for file_config in self.config['files']:
            file = self.config.copy()
            if isinstance(file_config, str):
                file['name'] = file_config
            else:
                if 'skip' in file_config:
                    if isinstance(file_config['skip'], str):
                        file['skip'] = '|'.join([file_config['skip'], file['skip']])
                    else:
                        file_config['skip'].append(file['skip'])
                        file['skip'] = '|'.join(file_config['skip'])
                if 'insert_after' in file_config:
                    if isinstance(file_config['insert_after'], str):
                        if 'insert_after' in file:
                            file['insert_after'] = '|'.join(
                                [file_config['insert_after'], file['insert_after']])
                    else:
                        file_config['insert_after'].append(self.config['insert_after'])
                        file['insert_after'] = '|'.join(file_config['insert_after'])
            files.append(file)
        return files

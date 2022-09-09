from __future__ import annotations
from yaml import load, Loader
import re
import os
import copy

MAX_BOOK_SIZE = 64


class Config:
    def __init__(self, filename: str = ""):
        if filename == "":
            self.config_dict = {}
        else:
            self.config_dict = load(open(filename, 'r'), Loader)
            self.config_dict['max_book_size'] = \
                self.config_dict['max_book_size'] if 'max_book_size' in self.config_dict else MAX_BOOK_SIZE
            self.config_dict['configfile'] = filename
            if 'output_filename' in self.config_dict:
                self.config_dict['output_filename'] = re.sub("\\.pdf", "", self.config_dict['output_filename'])
            elif 'name' in self.config_dict:
                self.config_dict['output_filename'] = self.config_dict['name']
            if 'skip' in self.config_dict:
                if isinstance(self.config_dict['skip'], list):
                    self.config_dict['skip'] = '|'.join(self.config_dict['skip'])
                print(f"skipping {self.config_dict['skip']}")
            if 'insert_after' in self.config_dict:
                if isinstance(self.config_dict['insert_after'], list):
                    joined = '|'.join(self.config_dict['insert_after'])
                    self.config_dict['insert_after'] = joined
            self.config_dict['file_config'] = None

    def __copy__(self):
        new_config = Config()
        new_config.config_dict = self.config_dict.copy()
        return new_config

    def file_name(self):
        return self.full_path(self.config_dict['name'])

    def output_file_name(self, book_number):
        return self.full_path(f"{self.config_dict['output_filename']}_{book_number}.pdf")

    def blank(self):
        return self.config_dict['blank'] if 'blank' in self.config_dict else None

    def insert_after(self, file_name):
        if 'insert_after' in self.config_dict and \
                re.search(self.config_dict['insert_after'], os.path.basename(file_name)) is not None:
            return True

    def should_skip(self, file_name):
        if 'skip' in self.config_dict and re.search(self.config_dict["skip"], os.path.basename(file_name)) is not None:
            return True

    def full_path(self, base_file):
        return os.path.join(os.path.dirname(self.config_dict['configfile']), base_file)

    def max_book_size(self):
        return self.config_dict['max_book_size']

    def should_print(self, book_number):
        return 'only_print' not in self.config_dict or re.search(self.config_dict['only_print'], book_number)

    def files(self) -> list[Config]:
        files = []
        for file_dict in self.config_dict['files']:
            file = copy.copy(self)
            if isinstance(file_dict, str):
                file.config_dict['name'] = file_dict
            else:
                file.config_dict = {**file.config_dict, **file_dict}
                if 'skip' in file_dict:
                    if isinstance(file_dict['skip'], str):
                        file.config_dict['skip'] = '|'.join([file_dict['skip'], file.config_dict['skip']])
                    else:
                        file_dict['skip'].append(file.config_dict['skip'])
                        file.config_dict['skip'] = '|'.join(file_dict['skip'])
                if 'insert_after' in file_dict:
                    if isinstance(file_dict['insert_after'], str):
                        if 'insert_after' in file.config_dict:
                            file.config_dict['insert_after'] = '|'.join(
                                [file_dict['insert_after'], file.config_dict['insert_after']])
                    else:
                        file_dict['insert_after'].append(self.config_dict['insert_after'])
                        file.config_dict['insert_after'] = '|'.join(file_dict['insert_after'])
            files.append(file)
        return files

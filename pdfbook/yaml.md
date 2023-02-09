# yaml file contents

`max_book_size`
: Maximum size in pages per pdf file.  

`name:` _\<filename>_
: Files will be named `filename.pdf` or `filename_NNN.pdf`. `NNN` is the book number. `output_filename` is an alias.

`skip:` _regex_ or _list_
: Specify which image filenames to skip. Regex should be okay.

`insert_after:` _regex_ or _list_
: Insert a blank page after every page matching a pattern in the list. You can also use `insert_before`.

`blank_color`
: The color to use for the blank pages to be inserted.

`only_print: ` _regex_
: Only matching book numbers will have pdf files generated. This can save time if only one pdf file needs adjustment.

`n_up`
: How many pages per printed side. Should usually be 2 or 4.

`pages_per_signature`
: How many pages to put, ideally, in the signature. A signature may contain fewer pages if that reduces the number of
blanks in the end.

`dpi`
: The resolution in dots per inch for the pdf file.

`files`
: This can be a list of filenames to be joined into the set of pdf files. Can also include per-file configuration.

# The `files` entry

For each entry in the list called `files`, the general configuration is copied. If the list entry is a string, 
the key `name` is used for the file's name, otherwise if the entry is a dictionary, the general configuration is 
overwritten with the values in this dictionary. This allows simple definitions like:

```yaml
files:
  - first_comic.cbr
  - second_comic.cbr
  - third_comic.cbr
```

but it also allows more control as in

```yaml
files:
  - first_comic.cbr
  - name: second_comic.cbr
    blank_color: Gray
  - name: third_comic.cbr
    skip: junk
```

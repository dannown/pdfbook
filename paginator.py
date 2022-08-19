from wand.image import Image


def signature_page_order(num_up, pages_per_signature):
    if num_up == 4:
        return [5, 12, 4, 13,
                11, 6, 14, 3,
                7, 10, 2, 15,
                9, 8, 16, 1]
    if num_up == 2:
        if pages_per_signature == 12:
            return [12, 1, 2, 11,
                    10, 3, 4, 9,
                    8, 5, 6, 7]
        if pages_per_signature == 8:
            return [8, 1, 2, 7,
                    6, 3, 4, 5]
        if pages_per_signature == 16:
            return [16, 1, 2, 15,
                    14, 3, 4, 13,
                    12, 5, 6, 11,
                    10, 7, 8, 9]


def should_rotate_page(page_num, num_up, pages_per_signature):
    return num_up == 4 and pages_per_signature == 16 and page_num in [5, 12, 11, 6, 7, 10, 9, 8]


def write_paginated_images(image: Image, n_up: int, pages_per_signature: int, filename: str):
    if len(image.sequence) % pages_per_signature != 0:
        n = pages_per_signature - len(image.sequence) % pages_per_signature
        p = image.sequence[0]
        print(f"adding {n} blank pages to end")
        for x in range(n):
            image.sequence.append(Image(height=p.height, width=p.width, resolution=p.resolution))
    paginated_image = Image()
    num_signatures = int(len(image.sequence) / pages_per_signature)
    for n in range(num_signatures):
        for i in signature_page_order(n_up, pages_per_signature):
            big_i = pages_per_signature * n + i - 1
            page = image.sequence[big_i]
            if should_rotate_page(i, n_up, pages_per_signature):
                page.rotate(180)
            paginated_image.sequence.append(page)
    paginated_image.save(filename=filename)

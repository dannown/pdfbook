from wand.drawing import Drawing
from wand.image import Image


class Paginator:
    def __init__(self, num_up: int, pages_per_signature: int, blank: Image = None):
        self.num_up = num_up
        self.pages_per_signature = pages_per_signature
        self.blank = blank
        self.manual_layout = True
        self.paper_width = 21.0
        self.paper_height = 29.7
        self.dpi = 600.0
        self.top_margin = 5  # in mm!

    def signature_page_order(self):
        if self.num_up == 4:
            if self.pages_per_signature == 16:
                return [5, 12, 4, 13,
                        11, 6, 14, 3,
                        7, 10, 2, 15,
                        9, 8, 16, 1]
            if self.pages_per_signature == 8:
                return [3, 6, 2, 7,
                        5, 4, 8, 1]
        if self.num_up == 2:
            if self.pages_per_signature == 12:
                return [12, 1, 2, 11,
                        10, 3, 4, 9,
                        8, 5, 6, 7]
            if self.pages_per_signature == 4:
                return [4, 1, 2, 3]
            if self.pages_per_signature == 8:
                return [8, 1, 2, 7,
                        6, 3, 4, 5]
            if self.pages_per_signature == 16:
                return [16, 1, 2, 15,
                        14, 3, 4, 13,
                        12, 5, 6, 11,
                        10, 7, 8, 9]

    def should_rotate_page(self, page_num):
        if self.num_up == 4:
            if self.pages_per_signature == 16:
                return page_num in [5, 12, 11, 6, 7, 10, 9, 8]
            if self.pages_per_signature == 8:
                return page_num in [3, 6, 5, 4]
        return False

    def write_paginated_images(self, image: Image, filename: str):
        print(f"writing out {len(image.sequence)} pages.")
        if len(image.sequence) % self.pages_per_signature != 0:
            n = self.pages_per_signature - len(image.sequence) % self.pages_per_signature
            p = image.sequence[0]
            n %= self.num_up * 2
            print(f"adding {n} blank pages to end. There are now "
                  f"{(len(image.sequence) + n) % self.pages_per_signature} pages in the last signature.")
            for x in range(n):
                if self.blank is not None:
                    image.sequence.append(self.blank)
                else:
                    image.sequence.append(Image(height=p.height, width=p.width, resolution=p.resolution))
        paginated_image = Image()
        offset = 0
        tmp_pps = self.pages_per_signature
        while offset < len(image.sequence):
            if len(image.sequence) - offset < self.pages_per_signature:
                self.pages_per_signature = len(image.sequence) - offset
            for i in self.signature_page_order():
                big_i = offset + i - 1
                page = image.sequence[big_i]
                if self.should_rotate_page(i):
                    page.rotate(180)
                # print(f"adding page {big_i}")
                paginated_image.sequence.append(page)
            offset += self.pages_per_signature
        self.pages_per_signature = tmp_pps
        self.save_images(paginated_image, filename)
        paginated_image.close()

    def save_images(self, image: Image, filename: str):
        layout = Image()
        if self.manual_layout and self.num_up == 4:
            for i in range(int(len(image.sequence) / self.num_up)):
                with Drawing() as draw:
                    side = Image(resolution=self.dpi,
                                 height=int(self.paper_height/2.54*self.dpi),
                                 width=int(self.paper_width/2.54*self.dpi))
                    pages = image.sequence[i*self.num_up:(i+1)*self.num_up]
                    # we want 5mm on top, on bottom, then repeat.
                    top_margin = int(self.top_margin / 25.4 * self.dpi)
                    page_height = int((side.height - top_margin*4)/2)
                    page_width = int(page_height * pages[0].width / pages[0].height)
                    left_margin = int((side.width - 2 * page_width)/2)
                    print(f"laying out pages {i*self.num_up + 1} to {(i+1)*self.num_up}")
                    draw.composite(operator='over',
                                   left=left_margin,
                                   top=top_margin,
                                   width=page_width,
                                   height=page_height,
                                   image=pages[0])
                    draw.composite(operator='over',
                                   left=left_margin+page_width,
                                   top=top_margin,
                                   width=page_width,
                                   height=page_height,
                                   image=pages[1])
                    draw.composite(operator='over',
                                   left=left_margin,
                                   top=top_margin*3+page_height,
                                   width=page_width,
                                   height=page_height,
                                   image=pages[2])
                    draw.composite(operator='over',
                                   left=left_margin+page_width,
                                   top=top_margin*3+page_height,
                                   width=page_width,
                                   height=page_height,
                                   image=pages[3])
                    draw(side)
                    side.save(filename=f"/tmp/{i*self.num_up + 1:03d}-{(i+1)*self.num_up:03d}.pdf")
                    layout.sequence.append(side)
        else:
            layout = image
        layout.compression = "jpeg"
        layout.save(filename=filename)

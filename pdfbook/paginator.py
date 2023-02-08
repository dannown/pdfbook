from PIL import Image, ImageDraw, ImageFont
import os


class Paginator:
    def __init__(self, num_up: int, pages_per_signature: int, blank: Image = None, dpi: int = None):
        self.sheet_in_reg = 0
        self.num_up = num_up
        self.pages_per_signature = pages_per_signature
        self.blank = blank
        self.blank_color = "white"
        self.paper_width = 210
        self.paper_height = 297
        self.dpi = 300.0 if dpi is None else dpi
        self.number_offset = (10.0, 3.0)  # in mm
        self.top_margin = 5  # in mm!
        self.include_last_page_marker = True
        self.register_count = 0
        self.font = ImageFont.truetype(
            os.path.join(os.path.dirname(__file__), "resources/anwb-uu.woff.ttf"), 30)
        self.clipped_signatures = {}
        self.clipped_sheets = []

    def mm_to_pixels(self, mm):
        return int(mm / 25.4 * self.dpi)

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

    def write_paginated_images(self, images: list, filename: str):
        print(f"writing out {len(images)} pages.")
        if len(images) % self.pages_per_signature != 0:
            n = self.pages_per_signature - len(images) % self.pages_per_signature
            p = images[0]
            n %= self.num_up * 2
            print(f"adding {n} blank pages to end. There are now "
                  f"{(len(images) + n) % self.pages_per_signature} pages in the last signature.")
            for x in range(n):
                if self.blank is not None:
                    images.append(self.blank)
                else:
                    images.append(Image.new("RGB", (p.width, p.height), self.blank_color))
        paginated_images = []
        offset = 0
        tmp_pps = self.pages_per_signature
        while offset < len(images):
            if len(images) - offset < self.pages_per_signature:
                self.pages_per_signature = len(images) - offset
            for i in self.signature_page_order():
                big_i = offset + i - 1
                page: Image = images[big_i]
                if self.should_rotate_page(i):
                    page = page.rotate(180)
                # print(f"adding page {big_i}")
                paginated_images.append(page)
            offset += self.pages_per_signature
        self.pages_per_signature = tmp_pps
        self.save_images(paginated_images, filename)

    def save_images(self, images: list, filename: str):
        layout = []

        print(f"laying out {len(images)} pages. ", end='')
        num_sheets = int(len(images) / self.num_up)
        num_sheets_per_sig = int(self.pages_per_signature / self.num_up)
        side_a = None
        clipped = False
        for i in range(num_sheets):
            side = Image.new("RGB",
                             (self.mm_to_pixels(self.paper_width), self.mm_to_pixels(self.paper_height)),
                             self.blank_color)
            pages = images[i * self.num_up:(i + 1) * self.num_up]
            if self.num_up == 2:
                # pages[0].height is actually the width of the sheet.
                # pages[0].width is actually half the height of the
                left_margin = self.mm_to_pixels(self.top_margin)
                page_height = int(side.width - left_margin * 2)
                page_width = int(page_height * pages[0].width / pages[0].height)
                top_margin = int((side.height - 2 * page_width) / 2)
                if top_margin < 0:
                    clipped = True
                    sir = self.sheet_in_reg if (i + 1) % 2 == 0 else self.sheet_in_reg + 1
                    rc = self.register_count + 1
                    clipped_sheets = self.clipped_signatures.pop(rc, set())
                    clipped_sheets.add(sir)
                    self.clipped_signatures[rc] = clipped_sheets

                    top_margin = left_margin
                    page_width = int((side.height - top_margin * 2) / 2)
                    page_height = int(page_width * pages[0].height / pages[0].width)
                    left_margin = int((side.width - page_height) / 2)
                print(".", end='')
                page0 = pages[0].resize((page_width, page_height)).rotate(270, expand=True)
                page1 = pages[1].resize((page_width, page_height)).rotate(270, expand=True)
                side.paste(page0,
                           (left_margin,
                            top_margin,
                            left_margin + page_height,
                            top_margin + page_width))
                side.paste(page1,
                           (left_margin,
                            top_margin + page_width,
                            left_margin + page_height,
                            top_margin + 2 * page_width))
            else:  # self.num_up == 4:
                # we want `top_margin` (5mm) on top, on bottom, then repeat.
                top_margin = self.mm_to_pixels(self.top_margin)
                page_height = int((side.height - top_margin * 4) / 2)
                page_width = int(page_height * pages[0].width / pages[0].height)
                left_margin = int((side.width - 2 * page_width) / 2)
                print(".", end='')
                page0 = pages[0].resize((page_width, page_height))
                page1 = pages[1].resize((page_width, page_height))
                page2 = pages[2].resize((page_width, page_height))
                page3 = pages[3].resize((page_width, page_height))
                side.paste(page0,
                           (left_margin,
                            top_margin,
                            left_margin + page_width,
                            top_margin + page_height))
                side.paste(page1,
                           (left_margin + page_width,
                            top_margin,
                            left_margin + 2 * page_width,
                            top_margin + page_height))
                side.paste(page2,
                           (left_margin,
                            top_margin * 3 + page_height,
                            left_margin + page_width,
                            top_margin * 3 + 2 * page_height))
                side.paste(page3,
                           (left_margin + page_width,
                            top_margin * 3 + page_height,
                            left_margin + 2 * page_width,
                            top_margin * 3 + 2 * page_height))
            dx = self.mm_to_pixels(self.number_offset[0])
            dy = self.mm_to_pixels(self.number_offset[1])
            if (i + 1) % num_sheets_per_sig == 0 or i + 1 == num_sheets:
                # last sheet for the signature
                self.register_count += 1
                self.sheet_in_reg = 0
                draw = ImageDraw.Draw(side)
                draw.text((side.width - dx,
                           side.height - dy), f"{self.register_count:03d}",
                          font=self.font,
                          fill="black")
            elif (i + 1) % 2 == 0:
                # every other sheet (so once per folio)
                draw = ImageDraw.Draw(side)
                draw.text((side.width - dx,
                           side.height - dy), f"{self.register_count + 1:03d}",
                          font=self.font,
                          fill="grey")
            else:
                self.sheet_in_reg += 1
                draw = ImageDraw.Draw(side)
                draw.text((side.width - dx,
                           side.height - dy), f"{self.sheet_in_reg:02d}",
                          font=self.font,
                          fill="lightgrey")
            if (i + 1) % 2 == 0:
                if clipped:
                    self.clipped_sheets.append(side_a)
                    self.clipped_sheets.append(side)
                    side_a = None
                    clipped = False
            else:
                side_a = side
            layout.append(side)
        fp = open(filename, "wb")
        layout[0].save(fp, save_all=True, append_images=layout[1:])
        fp.close()
        print(" Done.")

    def save_clipped_pages(self, filename):
        if len(self.clipped_sheets) == 0:
            return
        print(f"Saving {len(self.clipped_sheets)} clipped pages")
        fp = open(filename, "wb")
        self.clipped_sheets[0].save(fp, save_all=True, append_images=self.clipped_sheets[1:])
        fp.close()

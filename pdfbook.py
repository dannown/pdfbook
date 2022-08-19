from PyPDF2 import PdfReader, PdfWriter, Transformation
import sys

def rotate_page(page, page_num, num_up, sheets_per_section):
    if num_up == 4 and sheets_per_section == 2:
        if page_num in [5, 12, 11, 6, 7, 10, 9, 8]:
            page.rotate(180)


def section_page_order(num_up, sheets_per_section):
    if num_up == 4:
        return [5, 12, 4, 13,
                11, 6, 14, 3,
                7, 10, 2, 15,
                9, 8, 16, 1]
    if num_up == 2:
        if sheets_per_section == 3:
            return [12, 1, 2, 11,
                    10, 3, 4, 9,
                    8, 5, 6, 7]
        if sheets_per_section == 2:
            return [8, 1, 2, 7,
                    6, 3, 4, 5]
        if sheets_per_section == 4:
            return [16, 1, 2, 15,
                    14, 3, 4, 13,
                    12, 5, 6, 11,
                    10, 7, 8, 9]


if len(sys.argv) != 5:
    print(f"got {len(sys.argv)} arguments, wanted 5.\n{sys.argv[0]} [#up] [#sheets per section] [input pdf] [output pdf]")
    exit(1)

num_up = int(sys.argv[1])
sheets_per_section = int(sys.argv[2])
input_name = sys.argv[3]
output_name = sys.argv[4]
in_pdf = PdfReader(input_name)
old_pdf = PdfWriter()
for page in in_pdf.pages:
    old_pdf.add_page(page)
num_pages_to_add = 0
pages_per_section = 2 * sheets_per_section * num_up
num_pages_to_add = (pages_per_section - len(old_pdf.pages) % pages_per_section) % pages_per_section  # is there a nicer way to do this?
if num_pages_to_add > 0:
    print("adding %d pages to the end." % num_pages_to_add)
    for i in range(num_pages_to_add):
        old_pdf.add_blank_page()

num_sections = int(len(old_pdf.pages) / pages_per_section)

new_pdf = PdfWriter()
for section_num in range(num_sections):
    for page_num in section_page_order(num_up, sheets_per_section):
        page = old_pdf.pages[page_num + section_num * pages_per_section - 1]
        rotate_page(page, page_num, num_up, sheets_per_section)
        new_pdf.addPage(page)
# shrunk_pdf = PdfWriter()
# width = new_pdf.pages[-1].mediabox.width
# height = new_pdf.pages[-1].mediabox.height
# print("shrinking pages")
# for folio_num in range(int(len(new_pdf.pages) / 4)):
#     print("folio %d/%d" % (folio_num, int(len(new_pdf.pages) / 4)))
#     page = shrunk_pdf.add_blank_page(width=width, height=height)
#     p1 = new_pdf.pages[folio_num * 4]
#     p2 = new_pdf.pages[folio_num * 4 + 1]
#     p3 = new_pdf.pages[folio_num * 4 + 2]
#     p4 = new_pdf.pages[folio_num * 4 + 3]
#     p1.add_transformation(Transformation().scale(0.5).translate(0, height/2))
#     p2.add_transformation(Transformation().scale(0.5).translate(width/2, height/2))
#     p3.add_transformation(Transformation().scale(0.5).translate(0, 0))
#     p4.add_transformation(Transformation().scale(0.5).translate(width/2, 0))
#     page.merge_page(p1)
#     page.merge_page(p2)
#     page.merge_page(p3)
#     page.merge_page(p4)
with open(output_name, "wb") as fp:
    new_pdf.write(fp)
# with open("shrunk.pdf", "wb") as fp:
#     shrunk_pdf.write(fp)

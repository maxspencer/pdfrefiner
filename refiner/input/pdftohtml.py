import subprocess
import re
import tempfile
import bs4
import sys

from refiner.input.model import InputDocument, InputPage, Font, Text


def parse(string, replacements=[]):
    for r in replacements:
        string = re.sub(r[0], r[1], string)

    soup = bs4.BeautifulSoup(string)
    document = InputDocument()

    fontspec_elements = soup.find_all('fontspec')
    for e in fontspec_elements:
        font = Font(e['id'], e['family'], e['size'], e['color'])
        document.fonts[font.id] = font

    page_elements = soup.find_all('page')
    for e in page_elements:
        page = InputPage(int(e['number']), int(e['width']), int(e['height']))
        document.pages.append(page)

        for te in e.find_all('text'):
            string = ''.join(te.strings)
            text = Text(
                string,
                page,
                int(te['left']),
                int(te['top']),
                int(te['width']),
                int(te['height']),
                font=document.fonts.get(te['font'], None)
            )
            page.texts.append(text)

    return document


def parse_file(path):
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.xml') as xml_file:
        args = ['pdftohtml', '-xml', path, xml_file.name]
        subprocess.check_call(args)
        xml = xml_file.read()
    return parse(xml)


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        d = parse(f.read())
    for t in d.pages[3].texts:
        print((str(t.box), str(t)))

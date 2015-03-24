import subprocess
import os
import sys
import re
import collections
import pdfparse
from bs4 import BeautifulSoup

replacements = [
    ('\t', ' '),
    (r'[ ]{2,}', ' '),
    ('•', '*'),
]

class Para(object):
    def __init__(self, elem):
        self.elems = list()
        self.add(elem)
        self.font = elem['font']
    
    def add(self, elem):
        self.elems.append(elem)
        # self.page = ?
        self.left = int(elem['left'])
        self.bottom = int(elem['top']) + int(elem['height'])

    def __str__(self):
        return ''.join([e.string for e in self.elems]).strip()

def find_columns(elems, smallest = 0.25):
    left = right = None
    votes = collections.Counter()
    for e in elems:
        l = int(e['left'])
        r = int(e['left']) + int(e['width'])
        votes[l] += 1
        if left is None or l < left:
            left = l
        if right is None or r > right:
            right = r
            
    print(left)
    print(right)
    print(votes.most_common())

    width = right - left
    cols = list()
    c = left
    votes2 = collections.Counter()
    for i in sorted(votes.keys()):
        if i > (c + (smallest * width)):
            c = i
        votes2[c] += votes[i]
    return votes2

def col_rounder(cols):
    def f(x):
        scols = sorted(cols)
        i = 0
        while i < len(scols) - 1:
            if x >= scols[i+1]:
                i += 1
            else:
                break;
        return i
    return f

def md_page(path, page_num):
    print(path)
    print(page_num)
    xml_path = os.path.basename(path) + '_' + str(page_num) + '.xml'
    print(xml_path)
    subprocess.call(['pdftohtml', '-xml', '-f', str(page_num), '-l', str(page_num), path, xml_path])
    
    with open(xml_path, 'r') as f:
        xml = f.read()

    for r in replacements:
        xml = re.sub(r[0], r[1], xml)

    soup = BeautifulSoup(xml)

    text_elements = soup.find_all('text')

    texts = []
    for e in text_elements:
        box = pdfparse.Box(
            int(e['left']), int(e['top']), int(e['width']), int(e['height']))
        text = pdfparse.Text(e.string, box, int(page_num), font=e['font'])
        texts.append(text)

    page_box = pdfparse.Box(0, 217, right=892, bottom=1121)
    texts = pdfparse.crop_texts(texts, page_box)

    cols = pdfparse.columns(texts)

    groups = pdfparse.group_lines(texts, cols)
    groups = pdfparse.join_over_columns(groups, cols)
    paragraphs = [pdfparse.Paragraph.from_text_group(g) for g in groups]
    for p in paragraphs:
        print(p)
        print()
        pass

    '''
    # Find the column positions (will have to do this per-page
    # eventually (somehow allowing for paragraphs that break across
    # pages).

    cols = list(find_columns(texts).keys())
    print(cols)
    cr = col_rounder(cols)

    # Break into paragraphs
    s_texts = sorted(texts, key=lambda t: (cr(int(t['left'])), int(t['top'])))

    cur = Para(s_texts[0])
    ps = [cur]
    for text in s_texts[1:]:
        if cr(int(text['left'])) == cr(cur.left) and int(text['top']) < (cur.bottom + 5):
            cur.add(text)
        else:
            cur = Para(text)
            ps.append(cur)

    # Headings

    fontspecs = soup.find_all('fontspec')
    sizes = dict()
    for spec in fontspecs:
        try:
            sizes[spec['size']].append(spec['id'])
        except KeyError:
            sizes[spec['size']] = [spec['id']]
    levels = dict()
    i = 1
    for size in sorted(sizes.keys(), reverse=True):
        for id_ in sizes[size]:
            levels[id_] = i
        i += 1
    print(sizes)
    print(levels)
    
    # Print

    for p in ps:
        s = str(p)
        if not s.endswith('.'):
            # It's a heading
            print('#' * levels[p.font] + ' ' + s)
        else:
            print(s)
        print()
    '''

if __name__ == '__main__':
    md_page(sys.argv[1], int(sys.argv[2]))

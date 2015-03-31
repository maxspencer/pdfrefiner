import collections
import functools
import re
import subprocess
import sys
import tempfile

from bs4 import BeautifulSoup


class Box(object):
    def __init__(self, left, top, width = 0, height = 0, right = None, bottom = None):
        self.left = left
        self.top = top

        if right is not None:
            self.right = right
        else:
            self.right = left + width

        if bottom is not None:
            self.bottom = bottom
        else:
            self.bottom = top + height

    def __str__(self):
        return '{}x{} box at ({}, {})'.format(
            self.width, self.height, self.left, self.top)

    @property
    def width(self):
        return self.right - self.left

    @width.setter
    def width(self, value):
        self.right = self.left + value

    @property
    def height(self):
        return self.bottom - self.top
    
    @height.setter
    def height(self, value):
        self.bottom = self.top + value

    def contains(self, other):
        return (
            other.left >= self.left and
            other.top >= self.top and
            other.right <= self.right and
            other.bottom <= self.bottom
        )

    def scale(self, factor):
        f = float(factor)
        b = Box(
            f * self.left, f * self.top,
            right=(f * self.right), bottom=(f * self.bottom)
        )
        print(b)
        return b


def bounding_box(boxes):
    # Check there's at least one box
    if len(boxes) < 1:
        return None

    left = boxes[0].left
    top = boxes[0].top
    right = boxes[0].right
    bottom = boxes[0].bottom
    
    for box in boxes[1:]:
        left = min(left, box.left)
        top = min(top, box.top)
        right = max(right, box.right)
        bottom = max(bottom, box.bottom)

    return Box(left, top, right=right, bottom=bottom)
        

class Text(object):
    def __init__(self, string, box, page, font = None):
        self.string = string
        self.box = box
        self.page = page
        self.font = font

    def __str__(self):
        return str(self.string)
    
    @property
    def left(self):
        return self.box.left

    @property
    def top(self):
        return self.box.top

    @property
    def right(self):
        return self.box.right

    @property
    def bottom(self):
        return self.box.bottom

    @property
    def width(self):
        return self.box.width

    @width.setter
    def width(self, value):
        self.box.width = value

    @property
    def height(self):
        return self.box.height

    @height.setter
    def height(self, value):
        self.box.height = value


class TextGroup(object):
    def __init__(self, texts, font = None):
        self.texts = list(texts)

        if font is not None:
            self.font = font
        elif len(texts) > 0:
            self.font = self.texts[0].font
        else:
            self.font = None

    def __str__(self):
        return '\n'.join([str(t) for t in self.texts])

    def __len__(self):
        return len(self.texts)

    @property
    def first(self):
        return self.texts[0]

    @property
    def last(self):
        return self.texts[-1]

    def join(self, group):
        return TextGroup(self.texts + group.texts, self.font or group.texts)

    @property
    def string(self):
        '''Return a single string containing all the strings in this group.'''
        if len(self.texts) < 1:
            return ''
        else:
            return '\n'.join([t.string for t in self.texts])


def crop_texts(texts, box):
    return [t for t in texts if box.contains(t.box)]


def column_votes(texts, smallest = 0.25, min_votes = 1):
    votes = collections.Counter()

    # Want to assume there's at least one element
    if len(texts) == 0:
        return votes

    # Initialise left and right variables which will be used to
    # determine the text width
    left = texts[0].left
    right = texts[0].right

    for t in texts:
        # Increment appropriate counter
        votes[t.left] += 1

        # May update left or right
        if t.left < left:
            left = t.left
        if t.right > right:
            right = t.right

    # Determine the minimum allowed width of a column
    if smallest > 0:
        min_width = (right - left) * smallest
    else:
        min_width = 0

    # poss_cols is a sorted (asc) list of x coords which got one or more vote
    poss_cols = sorted(votes.keys())

    # current is the x coord of the left of the column for which votes are
    # currently being accumulated. The algorithm greedily starts new columns at
    # the leftmost (lowest x) point which is more than min_width from the
    # previous column start and which has more than min_votes.

    # current is initialised with the x coord of the leftmost column with more
    # than min_votes votes. i just tracks where we start the next loop from
    i = 1
    for x in poss_cols:
        if votes[x] >= min_votes:
        # Votes for columns further to the left (but without
        # min_votes votes) are discarded
            current = x
            break
        else:
            del votes[x]
            i += 1

    # In the case where current is not initialised because there are no columns
    # with min_votes votes, poss_cols[i:] will be [] and this loop has no
    # iterations.
    for x in poss_cols[i:]:
        if x > (current + min_width) and votes[x] >= min_votes:
            current = x
        else:
            del votes[x]
            
    return votes


def columns(texts, smallest = 0.25, min_votes = 1):
    return sorted(column_votes(texts, smallest, min_votes).keys())


def round_to_column(x, cols):
    scols = sorted(cols)

    # i is the column index we are going to return. The loop increments it if
    # the given x coord is greater than the next column coord.
    i = 0
    while i < len(scols) - 1:
        if x >= scols[i+1]:
            i += 1
        else:
            break;
    return i


class ColumnMap(object):
    def __init__(self, existing = None):
        if existing:
            try:
                self.dict = dict(existing.dict)
            except AttributeError:
                self.dict = dict(existing)
        else:
            self.dict = dict()

    def insert(self, page, columns):
        self.dict[page] = columns

    def get_column(self, page, x):
        return round_to_column(x, self.dict[page])


def group_lines(texts, column_map, max_line_sep = 5):
    if len(texts) == 0:
        return []

    col = column_map.get_column

    # Sort the texts by page, then by column (rounded) from left to right, then
    # from top to bottom. Then any ties are broken using the raw (as opposed to
    # column-rounded) left coord.
    texts = sorted(
        texts,
        key=lambda t: (t.page, col(t.page, t.left), t.top, t.left)
    )
    groups = []

    current = [texts[0]]
    for t in texts[1:]:
        if (t.page == current[-1].page
            and col(t.page, t.left) == col(current[-1].page, current[-1].left)
            and t.top < current[-1].bottom + max_line_sep):
            current.append(t)
        else:
            groups.append(TextGroup(current))
            current = [t]

    groups.append(TextGroup(current))

    return groups


def join_over_columns(groups, column_map):
    if len(groups) < 1:
        return []

    col = column_map.get_column

    joined = []
    current = groups[0]

    for g in groups[1:]:
        cl = current.last
        gf = g.first
        is_diff_col = (
            cl.page != gf.page or
            col(cl.page, cl.left) != col(gf.page, gf.left)
        )
        if (is_diff_col
            and cl.font == gf.font
            and not re.match(r'^.*[:\.]\s*$', cl.string)):
            # next group (g) is in a different column, has the same font and
            # current doesn't end with a full stop or colon then join g to
            # current...
            current = current.join(g)
        else:
            # Otherwise current is finished, g is the new current
            joined.append(current)
            current = g

    # Append the final group
    joined.append(current)

    return joined


class Paragraph(object):
    def __init__(self, string, position):
        self.string = string
        self.position = position

    def __str__(self):
        return '{}: {}'.format(str(self.position), self.string)


class Heading(object):
    def __init__(self, string, position, parent):
        self.string = string
        self.position = position
        self.parent = parent
        
        # TODO: ensure parent is before self

    def __str__(self):
        return '{}: {} {}'.format(
            str(self.position),
            '#' * self.level,
            self.string
        )

    @property
    def level(self):
        if self.parent is not None:
            return self.parent.level + 1
        else:
            return 1


class Page(object):
    def __init__(self, number, width, height, crop = None):
        self.number = number
        self.width = width
        self.height = height
        self.crop = crop

    def __str__(self):
        return '<Page: {}, {}x{}>'.format(self.number, self.width, self.height)


class Document(object):
    def __init__(self):
        self.pages = list()
        self.contents = list()

    def __str__(self):
        return '\n\n'.join([str(c) for c in self.contents])

    @property
    def page_count(self):
        return len(self.pages)


replacements = [
    ('\t', ' '),
    (r'[ ]{2,}', ' '),
    ('•', '*'),
]


class _HeadingTracker(object):
    def __init__(self):
        self._last_headings = {0: None}

    def get_parent(self, size_rank):
        ranks = self._last_headings.keys()
        prec_rank = max([rank for rank in ranks if rank < size_rank])
        return self._last_headings[prec_rank]

    def new_heading(self, size_rank, heading):
        self._last_headings[size_rank] = heading
        ranks_to_clear = [
            rank for rank in self._last_headings.keys() if rank > size_rank
        ]
        for rank in ranks_to_clear:
            del self._last_headings[rank]


def parse_file(path, first_page = None, last_page = None, crop = None, zoom = 1.0):
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.xml') as xml_file:
        args = ['pdftohtml', '-xml', '-zoom', str(zoom)]
        if first_page:
            args += ['-f', str(int(first_page))]
        if last_page:
            args += ['-l', str(int(last_page))]
        args += [path, xml_file.name]
        subprocess.check_call(args)
        xml = xml_file.read()

    for r in replacements:
        xml = re.sub(r[0], r[1], xml)
    
    soup = BeautifulSoup(xml)
    page_elements = soup.find_all('page')

    # May later have different crops for different pages in some kind of dict
    page_crops = collections.defaultdict(lambda: crop)

    # The result:
    document = Document()

    if not page_elements:
        # Empty! :(
        return document
    
    texts = list()
    col_map = ColumnMap()

    for page_element in page_elements:
        page_num = int(page_element['number'])
        page_crop = page_crops[page_num]

        # Add page to document
        document.pages.append(
            Page(
                page_num,
                int(page_element['width']),
                int(page_element['height']),
                page_crop
            )
        )

        page_texts = list()

        for text_element in page_element.find_all('text'):
            box = Box(
                int(text_element['left']),
                int(text_element['top']),
                int(text_element['width']),
                int(text_element['height'])
            )
            string = ''.join(text_element.strings)
            text = Text(
                string, box, page_num, font=text_element['font']
            )
            page_texts.append(text)

        # Crop this page individually
        if page_crop:
            if zoom != 1.0:
                page_crop = page_crop.scale(zoom)
            page_texts = crop_texts(page_texts, page_crop)

        # Add to column map and total list of texts
        col_map.insert(page_num, columns(page_texts))
        texts += page_texts

    # Use fonts to make the heading level map
    fontspec_elements = soup.find_all('fontspec')
    sizes = dict()
    for spec in fontspec_elements:
        try:
            sizes[spec['size']].append(spec['id'])
        except KeyError:
            sizes[spec['size']] = [spec['id']]
    levels = dict()
    i = 1
    for size in sorted(sizes.keys(), reverse=True):
        for font in sizes[size]:
            levels[font] = i
        i += 1

    # Group texts 
    groups = join_over_columns(group_lines(texts, col_map), col_map)

    # Turn into model objects
    heading_tracker = _HeadingTracker()
    for group in groups:
        if '.' in group.string:
            string = ' '.join([t.string.strip() for t in group.texts])
            position = (group.first.page, group.first.left, group.first.top)
            item = Paragraph(string, position)
        else:
            string = ' '.join([t.string.strip() for t in group.texts])
            position = (group.first.page, group.first.left, group.first.top)

            # Sort out heading level and parent
            size_rank = levels[group.first.font]
            parent = heading_tracker.get_parent(size_rank)
            item = Heading(string, position, parent)
            heading_tracker.new_heading(size_rank, item)

        document.contents.append(item)

    return document


if __name__ == '__main__':
    doc = parse_file(
        sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), 
        Box(50, 75, right=550, bottom=780), sys.argv[4])
        #None, sys.argv[4])
    for p in doc.pages:
        print(p)
    print(doc)

import re

from refiner.output.model import OutputDocument, OutputPage, Content, Paragraph, Heading
from refiner.columns import ColumnMap, columns, DEFAULT_SMALLEST_COL, DEFAULT_MIN_COL_VOTES
from refiner.geometry import Box


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


DEFAULT_MAX_LINE_SEP = 1.0
DEFAULT_MIN_H_SEP = 0.5

def group_lines(texts, column_map, max_line_sep = DEFAULT_MAX_LINE_SEP, min_h_sep = DEFAULT_MIN_H_SEP):
    if len(texts) == 0:
        return []

    col = column_map.get_column

    # New preliminary phase: Determine the correct column for each text. Just
    # using the column map directly can lead to problems when a page contains
    # some lines which span multiple columms and these lines are broken after
    # parsing, for example if they contain multiple font styles.
    prelim = sorted(
        texts,
        key=lambda t: (t.page.number, t.top, t.left)
    )
    prev = prelim[0]
    prev.col = col(prev)
    for t in prelim[1:]:
        if (
                t.page == prev.page and
                t.top == prev.top and
                t.left < prev.right + (min_h_sep * t.height)
        ):
            t.col = prev.col
        else:
            t.col = col(t)
        prev = t

    # Sort the texts by page, then by column (rounded) from left to right, then
    # from top to bottom. Then any ties are broken using the raw (as opposed to
    # column-rounded) left coord.
    texts = sorted(
        texts,
        key=lambda t: (t.page.number, t.col, t.top, t.left)
    )
    groups = []

    current = [texts[0]]
    for t in texts[1:]:
        sep = current[-1].height * max_line_sep
        if (t.page == current[-1].page
            and t.col == current[-1].col
            and t.top < current[-1].bottom + sep
            and t.font.size == current[-1].font.size):
            #and not t.string.startswith('*')): # To stop lists getting grouped
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
            col(cl) != col(gf)
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


def is_heading(group, prev_group = None, next_group = None):
    if '.' in group.string or '•' in group.string:
        # Then it's a sentence with a full stop or a bullet point and not a
        # heading
        return False

    if prev_group and next_group:
        if (
                group.first.font == prev_group.last.font and
                group.last.font == next_group.first.font
        ):
            # Same font as previous and next groups, so probably not a heading
            return False

    if group.string.count(' ') > 14:
        # More than 10 words
        return False

    return True
        


def is_subheading(a, b):
    '''Returns True when a is a subheading of b (probably).'''
    return a.first.font.size < b.first.font.size


def refine(
        input,
        first = None, last = None,
        ignore = [],
        roi = None, width = None,
        max_line_sep = DEFAULT_MAX_LINE_SEP,
        smallest_col = DEFAULT_SMALLEST_COL,
        min_col_votes = DEFAULT_MIN_COL_VOTES,
        min_h_sep = DEFAULT_MIN_H_SEP
):
    output_document = OutputDocument()
    
    roi_texts = list()
    column_map = ColumnMap()

    if first is not None:
        first = max(first - 1, 0)
    else:
        first = 0

    if last is None:
        last = len(input.pages)

    for input_page in input.pages[first:last]:
        # Is this page ignored?
        ignore_page = input_page.number in ignore

        # Determine the roi for this page
        if roi is not None:
            page_roi = Box(
                input_page.width * roi[0],
                input_page.height * roi[1],
                right=input_page.width * roi[2],
                bottom=input_page.height * roi[3],
            )
        else:
            page_roi = None

        # Create an OutputPage instance and add it to the OutputDocument
        if width is not None:
            # If width parameter is specified need to do some scaling
            scale = width / input_page.width

            if page_roi:
                scaled_page_roi = page_roi.scale(scale)
            else:
                scaled_page_roi = None

            output_page = OutputPage(
                output_document,
                input_page.number,
                width,
                (input_page.height * scale),
                scale=scale,
                roi=scaled_page_roi,
                ignored=ignore_page
            )
        else:
            output_page = OutputPage(
                output_document,
                input_page.number,
                input_page.width,
                input_page.height,
                roi=page_roi,
                ignored=ignore_page
            )
        output_document.pages[output_page.number] = output_page

        if not ignore_page:
            # Find the texts within the roi
            if page_roi:
                page_texts = [
                    t for t in input_page.texts if page_roi.contains(t)
                ]
            else:
                page_texts = input_page.texts

            # Find columns and insert into column map
            column_map.insert(
                input_page,
                columns(page_texts, smallest_col, min_col_votes)
            )

            # Add page texts to the total roi_texts list
            roi_texts += page_texts

    # Group texts into paragraphs
    groups = group_lines(roi_texts, column_map, max_line_sep)
    groups = join_over_columns(groups, column_map)

    # For keeping track of the heading hierarchy - contains a list of
    # (TextGroup, Heading) two-tuples.
    current_headings = list()

    # Turn the text groups into output model Content instances
    for i in range(len(groups)):
        group = groups[i]

        # Get the input page number and then the OutputPage instance
        page_number = group.first.page.number
        output_page = output_document.pages[page_number]
        # left, top and string are calculated in the same way for headings and
        # normal paragraphs:
        left = group.first.left
        top = group.first.top
        if output_page.scale != 1.0:
            left *= output_page.scale
            top *= output_page.scale
        string = ' '.join([t.string.strip() for t in group.texts])
        string = re.sub(r'[ \t]+', ' ', string)

        # Can use previous and next text groups to help determine whether this
        # group is a heading
        if i > 0:
            prev_group = groups[i-1]
        else:
            prev_group = None
        try:
            next_group = groups[i+1]
        except IndexError:
            next_group = None

        if (is_heading(group, prev_group, next_group)):
            # Determine the parent heading
            parent = None
            while len(current_headings) > 0:
                if is_subheading(group, current_headings[-1][0]):
                    # New lowest-level heading
                    parent = current_headings[-1][1]
                    break
                else:
                    # Bigger heading, remove current lowest-level heading
                    del current_headings[-1]

            content = Heading(output_page, left, top, string, parent)
            current_headings.append((group, content))
        else:
            content = Paragraph(output_page, left, top, string)
        
        # Append to content list of output page
        output_page.contents.append(content)

    return output_document


if __name__ == '__main__':
    from refiner.input.pdftohtml import parse
    import sys
    with open(sys.argv[1], 'r') as f:
        input_doc = parse(f.read(), [(r'�', '.')])
    output_doc = refine(input_doc, width=int(sys.argv[2]), roi=(0.0, 0.08, 0.952, 0.94), max_line_sep=0.2, min_col_votes=2)
    print(str(len(output_doc.pages)) + ' output pages')
    for p in output_doc.page_list:
        print(p)
        for c in p.contents:
            print(c)
        print()
    
        
        

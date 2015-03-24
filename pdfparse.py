import collections
import functools
import re


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
        

def column_rounder(cols):
    return functools.partial(round_to_column, cols=cols)


def group_lines(texts, cols, max_line_sep = 5):
    if len(texts) == 0:
        return []

    cr = column_rounder(cols)

    # Sort the texts by column (rounded) from left to right, and then from top
    # to bottom
    texts = sorted(texts, key=lambda t: (cr(t.left), t.top))
    groups = []

    current_group = [texts[0]]
    current_col = cr(texts[0].left)
    for t in texts[1:]:
        if (cr(t.left) == current_col
            and t.top < current_group[-1].bottom + max_line_sep):
            current_group.append(t)
        else:
            groups.append(TextGroup(current_group))
            current_group = [t]
            current_col = cr(t.left)

    groups.append(TextGroup(current_group))

    return groups


def join_over_columns(groups, cols):
    if len(groups) < 1:
        return []

    col = column_rounder(cols)

    joined = []
    current = groups[0]

    for g in groups[1:]:
        print('current.last=' + str(current.last) + ', g.first=' + str(g.first))
        is_diff_col = (
            current.last.page != g.first.page or
            col(current.last.left) != col(g.first.left)
        )
        print('is_diff_col=' + str(is_diff_col))
        if is_diff_col and not re.match(r'^.*[:\.]\s*$', current.last.string):
            # next group (g) is in a different column and current doesn't end
            # with a full stop or colon then join g to current...
            current = current.join(g)
            print('joined')
        else:
            # Otherwise current is finished, g is the new current
            joined.append(current)
            current = g
            print('not joined')

    # Append the final group
    joined.append(current)

    return joined


class Paragraph(object):
    def __init__(self, string, first_line, font = None):
        self.string = string
        self.first_line = first_line
        self.font = font

    def __str__(self):
        return '({}, {}): {}'.format(
            self.first_line.left, self.first_line.top, self.string)

    @classmethod
    def from_text_group(cls, text_group):
        if len(text_group) < 1:
            return ''

        s = text_group.first.string.strip()

        for t in text_group.texts[1:]:
            s += ' ' + t.string.strip()

        return Paragraph(s, text_group.first, text_group.font)
            



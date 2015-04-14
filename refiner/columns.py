import collections


DEFAULT_SMALLEST_COL = 0.25
DEFAULT_MIN_COL_VOTES = 1

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
    def __init__(self):
        self.dict = dict()

    def insert(self, page, columns):
        self.dict[page] = columns

    def get_column(self, box):
        return round_to_column(box.left, self.dict[box.page])

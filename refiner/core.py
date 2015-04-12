class Box(object):
    def __init__(self, left, top, width = 0, height = 0, right = None, bottom = None):
        self.left = left
        self.top = top

        if right is not None:
            self.width = right - left
        else:
            self.width = width

        if bottom is not None:
            self.height = bottom - top
        else:
            self.height = height

    def __str__(self):
        return '{}x{} box at ({}, {})'.format(
            self.width, self.height, self.left, self.top)

    def __eq__(self, other):
        return (
            self.left == other.left and
            self.top == other.top and
            self.width == other.width and
            self.height == other.height
        )

    @property
    def right(self):
        return self.left + self.width

    @right.setter
    def right(self, value):
        self.width = value - self.left

    @property
    def bottom(self):
        return self.top + self.height

    @bottom.setter
    def bottom(self, value):
        self.height = value - self.top

    def contains(self, other):
        return (
            other.left >= self.left and
            other.top >= self.top and
            other.right <= self.right and
            other.bottom <= self.bottom
        )

    def scale(self, factor):
        b = Box(
            factor * self.left, factor * self.top,
            right=(factor * self.right), bottom=(factor * self.bottom)
        )
        return b

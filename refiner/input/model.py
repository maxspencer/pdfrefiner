import itertools

from refiner.geometry import Box


class Text(object):
    def __init__(self, string, page, left, top, width = 0, height = 0, right = None, bottom = None, font = None):
        self.string = string
        self.box = Box(
            left, top,
            width=width, height=height,
            page=page,
            right=right, bottom=bottom
        )
        self.font = font

    def __str__(self):
        return str(self.string)

    @property
    def page(self):
        return self.box.page
    
    @property
    def left(self):
        return self.box.left

    @property
    def top(self):
        return self.box.top

    @property
    def width(self):
        return self.box.width

    @property
    def height(self):
        return self.box.height

    @property
    def right(self):
        return self.box.right

    @property
    def bottom(self):
        return self.box.bottom


class Font(object):
    def __init__(self, id, family, size, color):
        '''Create a new Font instance.

        size may be an int or float, or the string representation of either of
        these.

        '''
        self.id = id
        self.family = family
        self.color = color
        
        if type(size) == int or type(size) == float:
            self.size = size
        elif type(size) == str:
            try:
                self.size = int(size)
            except ValueError:
                try:
                    self.size = float(size)
                except ValueError:
                    raise ValueError('Could not parse size as int or float')
        else:
            raise TypeError('size must be an int, float or str')
        
    def __str__(self):
        return '<Font {}>'.format(self.id)


class InputPage(object):
    def __init__(self, number, width, height):
        '''Create a new Page instance.'''
        self.number = int(number)
        self.width = width
        self.height = height
        self.texts = list()

    def __str__(self):
        return '<Page {}>'.format(self.number)

class InputDocument(object):
    def __init__(self):
        '''Create a new Document instance.'''
        self.pages = list()
        self.fonts = dict()
        

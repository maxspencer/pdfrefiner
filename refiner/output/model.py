from refiner.geometry import Box


class OutputDocument(object):
    def __init__(self):
        self.pages = dict()

    @property
    def page_list(self):
        return [self.pages[n] for n in sorted(self.pages.keys())]


class OutputPage(object):
    def __init__(
            self, document, number, width, height,
            scale = 1.0, roi = None, ignored = False
    ):
        self.document = document
        self.number = number
        self.width = width
        self.height = height
        self.scale = scale
        self.roi = roi
        self.ignored = ignored
        self.contents = list()

    def __str__(self):
        return '<OutputPage {}>'.format(self.number)


class Content(object):
    def __init__(self, page, left, top, string):
        self.page = page
        self.left = left
        self.top = top
        self.string = string

    def __str__(self):
        return '({}, {}, {}): {}'.format(
            self.page.number,
            self.left,
            self.top,
            self.string
        )


class Paragraph(Content):
    pass


class Heading(Content):
    def __init__(self, page, left, top, string, parent):
        super(Heading, self).__init__(page, left, top, string)
        self.parent = parent

    def __str__(self):
        return '({}, {}, {}): {} {}'.format(
            self.page.number,
            self.left,
            self.top,
            '#' * self.level,
            self.string
        )

    @property
    def level(self):
        if self.parent is not None:
            return self.parent.level + 1
        else:
            return 1

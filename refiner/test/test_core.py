import unittest
from .. import core


class BoxTestCase(unittest.TestCase):
    def test_width_height_constructor(self):
        box = core.Box(10, 10, width=10, height=10)
        self.assertEqual(box.left, 10, 'incorrect left')
        self.assertEqual(box.top, 10, 'incorrect top')
        self.assertEqual(box.right, 20, 'incorrect right')
        self.assertEqual(box.bottom, 20, 'incorrect bottom')
        self.assertEqual(box.width, 10, 'incorrect width')
        self.assertEqual(box.height, 10, 'incorrect height')

    def test_right_bottom_constructor(self):
        box = core.Box(10, 10, right=20, bottom=20)
        self.assertEqual(box.left, 10, 'incorrect left')
        self.assertEqual(box.top, 10, 'incorrect top')
        self.assertEqual(box.right, 20, 'incorrect right')
        self.assertEqual(box.bottom, 20, 'incorrect bottom')
        self.assertEqual(box.width, 10, 'incorrect width')
        self.assertEqual(box.height, 10, 'incorrect height')

    def test_constructors_equiv(self):
        width = 123
        height = 456
        box1 = core.Box(0, 0, width=width, height=height)
        box2 = core.Box(0, 0, right=width, bottom=height)
        self.assertEqual(box1, box2, 'boxes differ')

    def test_default_constructor(self):
        box = core.Box(12, 34, 56, 78, 9)
        self.assertEqual(box.left, 12, 'incorrect left')
        self.assertEqual(box.top, 34, 'incorrect top')
        self.assertEqual(box.width, 56, 'incorrect width')
        self.assertEqual(box.height, 78, 'incorrect height')
        self.assertEqual(box.page, 9, 'incorrect page')

    def test_eq(self):
        box = core.Box(10, 10, 10, 10, page=1)
        self.assertNotEqual(box, core.Box(11, 10, 10, 10, 1), 'left neq')
        self.assertNotEqual(box, core.Box(10, 11, 10, 10, 1), 'top neq')
        self.assertNotEqual(box, core.Box(10, 10, 11, 10, 1), 'width neq')
        self.assertNotEqual(box, core.Box(10, 10, 10, 11, 1), 'height neq')
        self.assertNotEqual(box, core.Box(10, 10, 10, 10, 2), 'page neq')
        self.assertNotEqual(box, core.Box(10, 10, 10, 10), 'page neq (None)')
        self.assertEqual(box, core.Box(10, 10, 10, 10, 1), 'should be equal')
        self.assertEqual(
            core.Box(1, 2, 3, 4, page=None),
            core.Box(1, 2, 3, 4, page=None),
            'should be equal'
        )

    def test_set_width(self):
        box = core.Box(10, 10, 10, 10)
        box.width = 20
        self.assertEqual(box.right, 30, 'incorrect right')
        self.assertEqual(box, core.Box(10, 10, 20, 10), 'width set error')

    def test_set_right(self):
        box = core.Box(10, 10, 10, 10)
        box.right = 30
        self.assertEqual(box.width, 20, 'incorrect width')
        self.assertEqual(box, core.Box(10, 10, 20, 10), 'set right error')

    def test_set_height(self):
        box = core.Box(10, 10, 10, 10)
        box.height = 20
        self.assertEqual(box.bottom, 30, 'incorrect bottom')
        self.assertEqual(box, core.Box(10, 10, 10, 20), 'set height error')

    def test_set_bottom(self):
        box = core.Box(10, 10, 10, 10)
        box.bottom = 30
        self.assertEqual(box.height, 20, 'incorrect height')
        self.assertEqual(box, core.Box(10, 10, 10, 20), 'set bottom error')

    def test_contains_no_page(self):
        cont = core.Box(0, 0, 100, 100)
        self.assertFalse(cont.contains(core.Box(-10, -10, 120, 120)))
        self.assertFalse(cont.contains(core.Box(110, 0, 100, 100)))
        self.assertFalse(cont.contains(core.Box(0, 110, 100, 100)))
        self.assertFalse(cont.contains(core.Box(-50, 25, 100, 50)))
        self.assertFalse(cont.contains(core.Box(25, -50, 50, 100)))
        self.assertFalse(cont.contains(core.Box(50, 25, 100, 50)))
        self.assertFalse(cont.contains(core.Box(25, 50, 50, 100)))
        self.assertTrue(cont.contains(cont))
        self.assertTrue(cont.contains(core.Box(0, 0, 100, 100)))
        self.assertTrue(cont.contains(core.Box(0, 25, 50, 50)))
        self.assertTrue(cont.contains(core.Box(25, 0, 50, 50)))
        self.assertTrue(cont.contains(core.Box(50, 25, 50, 50)))
        self.assertTrue(cont.contains(core.Box(25, 50, 50, 50)))
        self.assertTrue(cont.contains(core.Box(10, 10, 80, 80)))

    def test_contains_with_pages(self):
        cont = core.Box(0, 0, 100, 100, page=1)
        self.assertFalse(cont.contains(core.Box(0, 0, 100, 100, page=2)))
        self.assertFalse(cont.contains(core.Box(0, 0, 100, 100, page=None)))
        self.assertTrue(cont.contains(cont))
        self.assertTrue(cont.contains(core.Box(0, 0, 100, 100, page=1)))
        self.assertTrue(cont.contains(core.Box(10, 10, 80, 80, page=1)))
        nopage = core.Box(0, 0, 100, 100, page=None)
        self.assertTrue(nopage.contains(core.Box(0, 0, 100, 100, page=2)))
        self.assertTrue(nopage.contains(core.Box(0, 0, 100, 100, page=None)))
        self.assertTrue(nopage.contains(nopage))
        self.assertTrue(nopage.contains(core.Box(0, 0, 100, 100, page=1)))
        self.assertTrue(nopage.contains(core.Box(10, 10, 80, 80, page=1)))

    def test_scale(self):
        box = core.Box(10, 10, 10, 10)
        doubleBox = box.scale(2)
        self.assertEqual(doubleBox.left, 20, '(2x) incorrect left')
        self.assertEqual(doubleBox.top, 20, '(2x) incorrect top')
        self.assertEqual(doubleBox.width, 20, '(2x) incorrect width')
        self.assertEqual(doubleBox.height, 20, '(2x) incorrect height')
        self.assertEqual(doubleBox.right, 40, '(2x) incorrect right')
        self.assertEqual(doubleBox.bottom, 40, '(2x) incorrect bottom')
        halfBox = box.scale(0.5)
        self.assertEqual(halfBox.left, 5, '(0.5x) incorrect left')
        self.assertEqual(halfBox.top, 5, '(0.5x) incorrect top')
        self.assertEqual(halfBox.width, 5, '(0.5x) incorrect width')
        self.assertEqual(halfBox.height, 5, '(0.5x) incorrect height')
        self.assertEqual(halfBox.right, 10, '(0.5x) incorrect right')
        self.assertEqual(halfBox.bottom, 10, '(0.5x) incorrect bottom')
        fracBox = box.scale(1.01)
        self.assertEqual(fracBox.left, 10.1, '(1.01x) incorrect left')
        self.assertEqual(fracBox.top, 10.1, '(1.01x) incorrect top')
        self.assertEqual(fracBox.width, 10.1, '(1.01x) incorrect width')
        self.assertEqual(fracBox.height, 10.1, '(1.01x) incorrect height')
        self.assertEqual(fracBox.right, 20.2, '(1.01x) incorrect right')
        self.assertEqual(fracBox.bottom, 20.2, '(1.01x) incorrect bottom')

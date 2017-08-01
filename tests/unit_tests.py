import unittest


def func(x):
    return x


class TestTest(unittest.TestCase):
    # add a failing test
    def test(self):
        self.assertEqual(func(1), 2)


if __name__ == '__main__':
    unittest.main()

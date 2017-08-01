import unittest


def func(x):
    return x


class TestTest(unittest.TestCase):
    def test(self):
        self.assertEqual(func(1), 1)


if __name__ == '__main__':
    unittest.main()

import unittest

from tarjan import tarjan


class TarjanTestCase(unittest.TestCase):
    def test_manual(self):
        vertices = set(range(1, 12))
        next_dict = {
            1: [4, 2, 3],
            2: [1],
            3: [5, 6, 7],
            4: [],
            5: [],
            6: [7],
            7: [],
            8: [9],
            9: [10],
            10: [8],
            11: [11],
        }
        components = list(tarjan(vertices, next_dict.get))
        self.assertItemsEqual(
            components,
            [
                {1, 2},
                {3},
                {4},
                {5},
                {6},
                {7},
                {8, 9, 10},
                {11},
            ]
        )


if __name__ == '__main__':
    unittest.main()

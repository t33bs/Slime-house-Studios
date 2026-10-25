import unittest
from studio.coordinates import screen_to_pixel


class CanvasCoordinateTests(unittest.TestCase):
    def test_click_stays_in_pixel_until_next_boundary(self):
        self.assertEqual(screen_to_pixel(103.99, 203.99, 100, 200, 4), (0, 0))
        self.assertEqual(screen_to_pixel(104, 204, 100, 200, 4), (1, 1))

    def test_zoomed_in_left_half_does_not_select_previous_or_next(self):
        self.assertEqual(screen_to_pixel(106, 206, 100, 200, 8), (0, 0))
        self.assertEqual(screen_to_pixel(108, 208, 100, 200, 8), (1, 1))

    def test_negative_coordinates_remain_outside_canvas(self):
        self.assertEqual(screen_to_pixel(99.99, 199.99, 100, 200, 8), (-1, -1))

    def test_fractional_zoom_and_offset(self):
        self.assertEqual(screen_to_pixel(14.4, 26.4, 11.25, 23.25, 1.5), (2, 2))

    def test_invalid_zoom_rejected(self):
        for zoom in (0, -1, float('nan')):
            with self.assertRaises(ValueError):
                screen_to_pixel(0, 0, 0, 0, zoom)

if __name__ == '__main__':
    unittest.main()

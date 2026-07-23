import unittest
import numpy as np
from PIL import Image, ImageDraw

from analyzer import analyze_semantics, composite


class Analyzer02ATest(unittest.TestCase):
    def test_detects_flat_anime_regions(self):
        image = Image.new("RGBA", (240, 320), (0, 0, 0, 0))
        d = ImageDraw.Draw(image)
        d.ellipse((35, 10, 205, 120), fill=(250, 250, 248, 255))       # cofia
        d.ellipse((45, 45, 195, 235), fill=(235, 145, 180, 255))      # cabello
        d.ellipse((80, 100, 165, 210), fill=(244, 232, 218, 255))     # rostro
        d.ellipse((95, 130, 115, 155), fill=(20, 30, 50, 255))        # ojo (hueco a cubrir)
        d.rectangle((65, 205, 180, 315), fill=(55, 56, 58, 255))      # ropa
        rgba = np.asarray(image)
        regions, _ = analyze_semantics(rgba[:, :, :3], rgba[:, :, 3])
        by_id = {r.id: r for r in regions}

        self.assertTrue(by_id["background"].mask[0, 0])
        self.assertTrue(by_id["white_structure"].mask[30, 120])
        self.assertTrue(by_id["hair"].mask[80, 120])
        self.assertTrue(by_id["skin"].mask[145, 105])  # el ojo queda rellenado en la base
        self.assertTrue(by_id["clothes"].mask[270, 120])
        self.assertGreater(by_id["hair"].mask.mean(), 0.05)


if __name__ == "__main__":
    unittest.main()

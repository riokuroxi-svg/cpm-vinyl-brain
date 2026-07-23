import unittest
import numpy as np
from PIL import Image, ImageDraw

from subparts import build_parts


class Analyzer02BTest(unittest.TestCase):
    def test_builds_semantic_subparts_and_depth(self):
        image = Image.new("RGBA", (320, 480), (0, 0, 0, 0))
        d = ImageDraw.Draw(image)
        d.ellipse((45, 5, 275, 135), fill=(250, 250, 248, 255))
        d.ellipse((55, 55, 265, 330), fill=(235, 145, 180, 255))
        d.ellipse((95, 125, 225, 285), fill=(244, 232, 218, 255))
        # Ojos separados y suficientemente grandes.
        for x in (120, 185):
            d.ellipse((x-20, 165, x+20, 205), fill=(252, 252, 250, 255))
            d.ellipse((x-12, 171, x+12, 201), fill=(35, 45, 70, 255))
            d.ellipse((x-7, 183, x+7, 199), fill=(80, 190, 215, 255))
        d.rectangle((70, 300, 140, 475), fill=(55, 56, 58, 255))
        d.rectangle((180, 300, 250, 475), fill=(55, 56, 58, 255))
        d.polygon([(110,300),(210,300),(230,470),(90,470)], fill=(248,248,247,255))
        rgba = np.asarray(image)
        parts, _ = build_parts(rgba[:,:,:3], rgba[:,:,3])
        by_id = {part.id: part for part in parts}

        for required in ["background", "headpiece", "hair_back", "hair_front", "face", "neck", "apron"]:
            self.assertIn(required, by_id)
        self.assertLess(by_id["hair_back"].z, by_id["face"].z)
        self.assertLess(by_id["face"].z, by_id["hair_front"].z)
        self.assertGreater(by_id["face"].mask.sum(), 100)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path
import numpy as np
import cv2

from solver_v02c import ShapeLibrary, fit_region, SOLID_SHAPES


class Solver02CTest(unittest.TestCase):
    def test_fits_solid_shapes_to_region(self):
        project = Path(__file__).resolve().parents[2]
        library = ShapeLibrary(project / "src/main/resources/shapes", max_side=64)
        target = np.zeros((72, 72), bool)
        cv2.ellipse(target.view(np.uint8), (36, 36), (22, 28), 0, 0, 360, 1, -1)
        rng = np.random.default_rng(42)
        layers, coverage = fit_region(
            "face", target, target.copy(), 3, (240, 220, 205), 10,
            library, rng, candidates=90, refinements=35
        )
        self.assertGreaterEqual(len(layers), 1)
        self.assertGreater(coverage, 0.70)
        self.assertTrue(all(layer.shape_id in SOLID_SHAPES for layer in layers))


if __name__ == "__main__":
    unittest.main()

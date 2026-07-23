import json
import unittest
from pathlib import Path

from solver_final import FINAL_BUDGET, SHAPE_POLICY
from solver_v02c import SOLID_SHAPES


class FinalBrainTest(unittest.TestCase):
    def test_final_budget_fits_game_limit(self):
        self.assertLessEqual(sum(FINAL_BUDGET.values()), 280)
        self.assertGreaterEqual(sum(FINAL_BUDGET.values()), 100)

    def test_shape_policies_only_use_catalog_solids(self):
        allowed=set(SOLID_SHAPES)
        for region,shapes in SHAPE_POLICY.items():
            self.assertTrue(set(shapes)<=allowed,region)

    def test_generated_demonstration_recipe_is_valid_when_present(self):
        project=Path(__file__).resolve().parents[2]
        path=project/'examples/final_bocchi_v03_hq/final_recipe.json'
        if not path.exists():
            self.skipTest('resultado de demostración no presente')
        recipe=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(recipe['version'],'0.3.0')
        self.assertLessEqual(recipe['metrics']['generatedLayers'],280)
        self.assertTrue(all(layer['opacity']==1.0 for layer in recipe['layers']))
        self.assertTrue(all(layer['shapeId'] in SOLID_SHAPES for layer in recipe['layers']))
        self.assertTrue(all(layer['phase'] in {'structure','facial_details','accessories'} for layer in recipe['layers']))


if __name__=='__main__':
    unittest.main()

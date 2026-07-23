import json
import unittest
from pathlib import Path


class Brain05Test(unittest.TestCase):
    def setUp(self):
        self.project=Path(__file__).resolve().parents[2]
        self.out=self.project/'examples/final_bocchi_v05'

    def test_progressive_recipes_when_demo_present(self):
        if not self.out.exists(): self.skipTest('demo 0.5 no presente')
        for budget in (64,128,256,430):
            recipe=json.loads((self.out/f'recipe_{budget:03d}.json').read_text(encoding='utf-8'))
            self.assertEqual(len(recipe['layers']),budget)
            self.assertTrue(all(layer['opacity']==1.0 for layer in recipe['layers']))
            self.assertTrue(all(layer['operation'] in {'ADD','CUT'} for layer in recipe['layers']))
            self.assertLessEqual(len(recipe['layers']),430)

    def test_new_solver_beats_old_at_same_budget(self):
        if not self.out.exists(): self.skipTest('demo 0.5 no presente')
        data=json.loads((self.out/'comparison_metrics.json').read_text(encoding='utf-8'))
        self.assertEqual(data['winnerSameBudget'],'0.5')
        self.assertGreater(data['progressive']['128']['qualityScore'],data['base03']['qualityScore'])

    def test_max_recipe_reserves_calibration_layers(self):
        if not self.out.exists(): self.skipTest('demo 0.5 no presente')
        recipe=json.loads((self.out/'recipe_430.json').read_text(encoding='utf-8'))
        self.assertEqual(recipe['constraints']['gameLimit'],450)
        self.assertEqual(recipe['constraints']['reservedCalibrationLayers'],20)
        self.assertGreater(recipe['operationUsage'].get('CUT',0),0)


if __name__=='__main__':
    unittest.main()

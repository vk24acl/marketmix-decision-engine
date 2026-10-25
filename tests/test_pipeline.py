import tempfile
import unittest
from pathlib import Path
import numpy as np
from marketmix.data import adstock, database, load_data, synthetic, write_data
from marketmix.model import evaluate, fit
from marketmix.optimizer import allocate


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spend, cls.outcome = synthetic()
        cls.model = fit(cls.spend, cls.outcome)

    def test_seed_reproduces_ledger(self):
        a,b = synthetic()
        np.testing.assert_array_equal(a,self.spend)
        np.testing.assert_array_equal(b,self.outcome)

    def test_adstock_carries_state_across_split(self):
        all_states=adstock(self.spend)
        resumed=adstock(self.spend[104:],initial=all_states[103])
        np.testing.assert_allclose(resumed,all_states[104:])

    def test_invalid_spend_rejected(self):
        for bad in [np.array([[-1.,2]]),np.array([[np.nan,2]])]:
            with self.assertRaises(ValueError):adstock(bad)

    def test_heldout_outcomes_cannot_change_predictions(self):
        first=evaluate(self.spend,self.outcome)
        changed=self.outcome.copy();changed[-26:]+=1000
        second=evaluate(self.spend,changed)
        np.testing.assert_allclose(first['predictions'],second['predictions'])
        self.assertGreater(second['model']['rmse'],first['model']['rmse']*10)

    def test_model_beats_seasonal_baseline_on_synthetic_fixture(self):
        report=evaluate(self.spend,self.outcome)
        self.assertLess(report['model']['rmse'],report['seasonal_naive']['rmse'])

    def test_fifteen_allocation_scenarios_reconcile(self):
        for budget in [8000,16000,24000]:
            for movement in [0,.05,.15,.30,.5]:
                with self.subTest(budget=budget,movement=movement):
                    p=allocate(self.model,self.spend,budget,movement)
                    self.assertAlmostEqual(p['allocated'],budget,places=2)
                    self.assertGreaterEqual(p['optimized_expected'],p['baseline_expected']-1e-5)
                    for row in p['channels']:
                        self.assertLessEqual(abs(row['change_percent']),movement*100+1e-5)

    def test_nonfinite_budget_rejected(self):
        for budget in [float('nan'),float('inf'),0,-50]:
            with self.assertRaises(ValueError):allocate(self.model,self.spend,budget)

    def test_zero_spend_history_rejected(self):
        with self.assertRaises(ValueError):allocate(self.model,np.zeros_like(self.spend),1000)

    def test_sql_totals_reconcile_to_source(self):
        with database(self.spend,self.outcome) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM spend').fetchone()[0],780)
            self.assertAlmostEqual(db.execute('SELECT SUM(spend_gbp) FROM spend').fetchone()[0],self.spend.sum(),places=5)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM outcomes').fetchone()[0],130)

    def test_csv_roundtrip_and_missing_channel_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=write_data(d);x,y=load_data(d)
            np.testing.assert_allclose(a,x);np.testing.assert_allclose(b,y)
            p=Path(d)/'weekly_spend.csv';p.write_text('\n'.join(p.read_text().splitlines()[:-1]))
            with self.assertRaises(ValueError):load_data(d)


if __name__=='__main__':unittest.main()

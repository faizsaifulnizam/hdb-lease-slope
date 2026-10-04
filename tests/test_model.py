"""Analytic seam tests: exact OLS and invalid/thin/rank/support guards."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

class ModelTests(unittest.TestCase):
    def test_exact_regression(self):
        from analysis import fit_ols
        import numpy as np
        x=np.array([[1,0],[1,1],[1,2],[1,3]],float)
        # Errors [1,-1,-1,1] are orthogonal to both columns. beta=[1,2], df=2, SSE=4.
        result=fit_ols(x,np.array([2,2,4,8],float))
        np.testing.assert_allclose(result['coef'],[1,2],atol=1e-12)
        self.assertEqual(result['df'],2)
        self.assertIs(type(result['df']),int)  # CLI receipt must serialize without a NumPy fallback.
        self.assertAlmostEqual(result['sse'],4)
        # Slope influence weights [-.3,-.1,.1,.3], leverage [.7,.3,.3,.7].
        # HC3 variance = 2*(.3/.3)^2 + 2*(.1/.7)^2 = 100/49.
        self.assertAlmostEqual(result['cov'][1,1],100/49)
        with self.assertRaises(ValueError): fit_ols(np.ones((4,2)),np.arange(4.))

    def test_segment_guards(self):
        from analysis import segment_model
        import numpy as np
        n=120
        lease=np.linspace(50,90,n)
        storey=np.tile([2,5,8,11,14],24)
        area=85+np.arange(n)%7
        months=np.tile(np.arange(1,13),10)
        logprice=8+0.01*lease+0.02*storey-0.001*area+0.005*months
        result=segment_model(lease,storey,area,months,np.exp(logprice))
        self.assertEqual(result['status'],'estimated')
        self.assertAlmostEqual(result['beta_per_year'],0.01,places=10)
        self.assertAlmostEqual(result['pct_per_year'],1.005016708416795,places=10)
        self.assertEqual(result['residual_df'],105)
        self.assertGreater(result['residual_lease_sd_years'],10)
        self.assertEqual(segment_model(lease[:50],storey[:50],area[:50],months[:50],np.exp(logprice[:50]))['status'],'small_n')
        self.assertEqual(segment_model(lease/10+50,storey,area,months,np.exp(logprice))['status'],'narrow_support')
        self.assertEqual(segment_model(lease,np.ones(n),area,months,np.exp(logprice))['status'],'rank_deficient')
        # Lease varying only with month is unidentifiable once month indicators enter.
        self.assertEqual(segment_model(50+months,storey,area,months,np.exp(logprice))['status'],'rank_deficient')

    def test_complete_year(self):
        from analysis import complete_year
        months=[f'{y}-{m:02}' for y in [2024,2025] for m in range(1,13)]+['2026-01']
        self.assertEqual(complete_year(months,2026),2025)
        self.assertEqual(complete_year(months,2025),2024)
        with self.assertRaises(ValueError): complete_year(['2025-01'],2026)

    def test_group_summary_unweighted(self):
        from analysis import group_summary
        # A thousand-row cell does not receive a thousand votes in a segment comparison.
        data=[dict(historical_group=g,status='estimated',flat_type='4 ROOM',n=n,pct_per_year=v) for g in ['historical_mature','historical_non_mature'] for n,v in [(1000,1),(100,3),(100,5)]]
        result=group_summary(data,'4_room',2025)
        self.assertEqual([r['median_pct_per_year'] for r in result],[3,3])
        self.assertEqual([r['n_transactions'] for r in result],[1200,1200])

if __name__=='__main__': unittest.main()

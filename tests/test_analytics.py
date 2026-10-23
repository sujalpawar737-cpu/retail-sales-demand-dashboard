import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from analytics import product_summary,kmeans_products,weekly_history,model_result

class DashboardAnalyticsTests(unittest.TestCase):
    def setUp(self):
        rng=pd.date_range('2010-12-01',periods=400,freq='D')
        self.df=pd.DataFrame({
            'invoice':[str(i) for i in range(400)],
            'stock_code':['A']*400,
            'description':['PRODUCT']*400,
            'quantity':[3]*400,
            'sales':[6.0]*400,
            'date':rng,
            'country':['United Kingdom']*400,
        })
    def test_product_summary(self):
        summary=product_summary(self.df)
        self.assertEqual(len(summary),1)
        self.assertEqual(int(summary.iloc[0].units),1200)
        self.assertEqual(int(summary.iloc[0].orders),400)
    def test_weekly_backtest(self):
        series=weekly_history(self.df,'A')
        result=model_result(series)
        self.assertEqual(len(result['holdout']),10)
        self.assertTrue(np.isfinite(result['metrics']['MAE']))
        self.assertGreaterEqual(result['estimate'],0)
    def test_empty_clustering(self):
        summary=product_summary(self.df)
        result=kmeans_products(summary,k=3)
        self.assertEqual(result.cluster.iloc[0],'Not available')

if __name__=='__main__':
    unittest.main()

"""Chapter 40 example: capm_statsmodels.py. Run: python capm_statsmodels.py"""
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
rng = np.random.default_rng(7)
df = pd.DataFrame({"market": rng.normal(0, 1, 250)})
df["stock"] = 0.2 + 1.3 * df["market"] + rng.normal(0, 0.5, 250)
res = smf.ols("stock ~ market", data=df).fit()
print(res.summary())

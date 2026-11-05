"""Chapter 40 example: option_quantlib.py. Run: python option_quantlib.py"""
import QuantLib as ql
today = ql.Date(5, 11, 2026)
ql.Settings.instance().evaluationDate = today
dc = ql.Actual365Fixed()
spot = ql.QuoteHandle(ql.SimpleQuote(100.0))
rate = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.065, dc))
div  = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.0, dc))
vol  = ql.BlackVolTermStructureHandle(
          ql.BlackConstantVol(today, ql.India(), 0.20, dc))
process = ql.BlackScholesMertonProcess(spot, div, rate, vol)
option = ql.VanillaOption(ql.PlainVanillaPayoff(ql.Option.Call, 100.0),
                          ql.EuropeanExercise(ql.Date(5, 11, 2027)))
option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
print(f"Call value: {option.NPV():.2f}  Delta: {option.delta():.3f}")

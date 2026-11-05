"""Chapter 39 example. Run: python -m pytest test_gst.py"""
def gst(amount, rate=18.0):
    return round(amount * (1 + rate / 100), 2)

def test_gst():
    assert gst(1000) == 1180.0

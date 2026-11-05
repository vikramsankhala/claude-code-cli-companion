"""Chapter 40 example: sklearn_baseline.py. Run: python sklearn_baseline.py"""
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
X, y = load_iris(return_X_y=True)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)
model = RandomForestClassifier(random_state=42).fit(X_tr, y_tr)
print(f"Accuracy: {model.score(X_te, y_te):.2f}")

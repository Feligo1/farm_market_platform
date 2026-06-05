# test_imports.py
print("Testing imports...")

try:
    import flask
    print(f"✅ Flask {flask.__version__}")
except Exception as e:
    print(f"❌ Flask: {e}")

try:
    import numpy
    print(f"✅ NumPy {numpy.__version__}")
except Exception as e:
    print(f"❌ NumPy: {e}")

try:
    import pandas
    print(f"✅ Pandas {pandas.__version__}")
except Exception as e:
    print(f"❌ Pandas: {e}")

try:
    import sklearn
    print(f"✅ Scikit-learn {sklearn.__version__}")
except Exception as e:
    print(f"❌ Scikit-learn: {e}")

try:
    import africastalking
    print(f"✅ Africa's Talking")
except Exception as e:
    print(f"❌ Africa's Talking: {e}")

try:
    import jwt
    print(f"✅ PyJWT")
except Exception as e:
    print(f"❌ PyJWT: {e}")

print("\nAll tests complete!")
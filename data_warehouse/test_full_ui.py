# -*- coding: utf-8 -*-
"""Test script that mimics exactly what the UI does"""
import sys
sys.path.insert(0, '.')

from repositories.database import DatabaseManager
from ai.order_predictor import AdvancedOrderPredictionModel

print("=== Testing UI-like flow ===")

# 1. Create model (like UI does)
print("1. Creating model...")
ai_model = AdvancedOrderPredictionModel()
print(f"   Model type: {ai_model.model_type}")

# 2. Get orders from database (like UI does)
print("2. Getting orders from database...")
db_manager = DatabaseManager()
orders = db_manager.get_orders()
print(f"   Orders count: {len(orders)}")

# Check what fields are in the orders
if orders:
    print("   First order keys:")
    for key in sorted(orders[0].keys()):
        val = orders[0][key]
        print(f"      {key}: {type(val).__name__}")

# 3. Train the model (like UI does)
print("3. Training model...")
try:
    metrics = ai_model.train(orders)
    print("   SUCCESS!")
    print(f"   RMSE: {metrics.get('rmse', 'N/A')}")
    print(f"   MAE: {metrics.get('mae', 'N/A')}")
    print(f"   Features count: {len(ai_model._feature_names)}")
    print(f"   Feature names: {ai_model._feature_names[:5]}...")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

print("=== Test complete ===")

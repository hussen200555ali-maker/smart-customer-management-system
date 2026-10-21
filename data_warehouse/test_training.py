# -*- coding: utf-8 -*-
"""Test script for AI model training"""
from repositories.database import DatabaseManager
from ai.order_predictor import AdvancedOrderPredictionModel

db = DatabaseManager()
orders = db.get_orders()
print("Orders:", len(orders))

model = AdvancedOrderPredictionModel()
metrics = model.train(orders)
print("SUCCESS - Training completed!")
print("RMSE:", round(metrics.get('rmse', 0), 4))
print("MAE:", round(metrics.get('mae', 0), 4))
print("Data points:", metrics.get('data_points'))

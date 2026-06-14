"""
ml_models/train_model.py
========================
Standalone script to train and save the ML models.
Run from the project root:
    python ml_models/train_model.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()

with app.app_context():
    print("\nTraining Sales Prediction Model...")
    from ml_models.sales_prediction import train_model
    ok, msg = train_model()
    print(f"  {'OK' if ok else 'FAIL'} {msg.replace(chr(0x20B9), 'Rs.')}")

    print("\nTesting Chatbot...")
    from ai.chatbot import get_response
    tests = [
        "Hello",
        "What is the price of a necklace?",
        "Do you have rings in stock?",
        "Recommend something for my wife",
        "What are your shop timings?",
        "Thank you",
    ]
    for q in tests:
        print(f"\n  User: {q}")
        resp = get_response(q).replace('\u20b9', 'Rs.')[:80]
        print(f"  Bot : {resp}...")
    print("\nAll models ready. Start the server with: python run.py\n")

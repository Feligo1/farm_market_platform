#!/usr/bin/env python3
# Quick test script for SMS
import os
from dotenv import load_dotenv

load_dotenv('.env.test')

# Your test code here
print("Test environment loaded")
print(f"Username: {os.getenv('AFRICASTALKING_USERNAME')}")

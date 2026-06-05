#!/bin/bash

echo "Running all tests..."

# Run API tests
python -m pytest tests/ -v

# Run mobile responsiveness test
python mobile_test.py

# Run backup test
python -c "from backup_manager import BackupManager; bm = BackupManager(); bm.create_backup()"

echo "Tests completed!"
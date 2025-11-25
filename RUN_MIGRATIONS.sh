#!/bin/bash
# Script to run database migrations
# Run this on your Raspberry Pi

cd /home/kruzer04/YB-Task-Management/YB-Task-Management

# Activate virtual environment
source venv/bin/activate

# Check current migration status
echo "Current migration status:"
alembic current

echo ""
echo "Migration history:"
alembic history

echo ""
echo "Applying migrations..."
alembic upgrade head

echo ""
echo "Migration complete! Current status:"
alembic current


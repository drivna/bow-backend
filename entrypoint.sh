#!/bin/bash

# Exit on any error
set -e

echo "Starting Flask application..."

# Print environment info
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "Flask app: ${FLASK_APP:-run.py}"
echo "Flask environment: ${FLASK_ENV:-production}"

# Wait for any dependencies if needed (can be extended)
echo "Checking application health..."

# Install any additional requirements if requirements.txt was updated
if [ -f requirements.txt ]; then
    echo "Installing/updating requirements..."
    pip install --no-cache-dir -r requirements.txt
fi

# Run database migrations or setup if needed (can be extended)
# python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

echo "Starting Flask server on port 4000..."

# Start the Flask application
exec python run.py
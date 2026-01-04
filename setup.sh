#!/bin/bash
# Setup script for Inventory Monitoring System

echo "================================================"
echo "Inventory Monitoring System - Setup"
echo "================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version detected"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q pandas numpy plotly streamlit
echo "✓ Dependencies installed"
echo ""

# Generate sample data
echo "Generating sample data..."
cd data
python3 generate_sample_data.py
cd ..
echo "✓ Sample data generated"
echo ""

echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "To run the dashboard:"
echo "  cd streamlit_app"
echo "  streamlit run app.py"
echo ""
echo "The dashboard will open at http://localhost:8501"
echo ""

#!/bin/bash

echo ""
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║      KISHOR AI DESKTOP AGENT — Starting      ║"
echo "  ╚══════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "  [ERROR] Python 3 not found! Install from python.org"
    exit 1
fi

echo "  [1/3] Installing required packages..."
pip3 install -r requirements.txt -q
echo "  [2/3] Packages ready."
echo "  [3/3] Starting Kishor Agent..."
echo ""

python3 kishor_server.py

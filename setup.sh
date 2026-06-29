#!/usr/bin/env bash
# ============================================================
# Tactical Knowledge Assistant — One-time setup script
# ============================================================
set -e

echo ""
echo "  🎯  Tactical Knowledge Assistant — Setup"
echo "  ============================================"
echo ""

# Check Python 3.12
if ! command -v python3.12 &>/dev/null; then
    echo "❌  Python 3.12 not found. Install it from https://www.python.org/"
    exit 1
fi
echo "✅  Python $(python3.12 --version)"

# Check Ollama
if ! command -v ollama &>/dev/null; then
    echo "❌  Ollama not found. Install from https://ollama.ai/"
    exit 1
fi
echo "✅  Ollama found at $(which ollama)"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo ""
    echo "📦  Creating virtual environment…"
    python3.12 -m venv .venv
fi
echo "✅  Virtual environment ready"

# Install dependencies
echo ""
echo "📥  Installing Python dependencies…"
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q
echo "✅  Dependencies installed"

# Pull the Ollama model
echo ""
echo "🤖  Downloading Ollama model qwen2.5:3b (~1.9 GB)…"
ollama pull qwen2.5:3b
echo "✅  Model downloaded"

# Create required directories
mkdir -p data/vector_store logs
echo "✅  Directories ready"

echo ""
echo "  ============================================"
echo "  ✅  Setup complete!"
echo ""
echo "  To start the application:"
echo "    1. ollama serve          (start Ollama in a terminal)"
echo "    2. source .venv/bin/activate"
echo "    3. streamlit run main.py"
echo ""
echo "  Or with the venv activated:"
echo "    .venv/bin/streamlit run main.py"
echo "  ============================================"
echo ""

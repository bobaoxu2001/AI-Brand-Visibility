#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".env" ]]; then
  echo "Missing .env file. Please run: cp .env.example .env and set API keys."
  exit 1
fi

echo "Installing Python dependencies..."
python3 -m pip install -r requirements.txt

echo "Step 1/4: Generate prompts..."
python3 pipeline/1_generate_prompts.py --reset

echo "Step 2/4: Fetch raw responses..."
python3 pipeline/2_fetch_llm_responses.py

echo "Step 3/4: Evaluate responses with judge model..."
python3 pipeline/3_evaluate_responses.py --force

echo "Step 4/4: Build analytics views..."
python3 pipeline/4_create_views.py

echo "Pipeline complete."
echo "Next: cd dashboard && npm install && npm run dev"

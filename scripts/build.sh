#!/bin/bash
mkdir -p _site
uv run marimo export html-wasm apps/language_app.py --mode run --no-show-code --sandbox -o _site/index.html
cp -r apps/public _site/
echo "Done! Run 'python -m http.server -d _site' to test."

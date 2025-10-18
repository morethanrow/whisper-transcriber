#!/bin/bash
export PATH="$PWD/bin:$PATH"
source venv/bin/activate
PORT=8001 python app.py

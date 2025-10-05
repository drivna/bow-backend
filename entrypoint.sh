#!/bin/bash
set -e

exec python "${FLASK_APP:-run.py}"

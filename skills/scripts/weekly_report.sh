#!/bin/bash
source ~/.hermes/scripts/.venv/bin/activate
exec ~/.hermes/scripts/tw_freelance_crawler.py --weekly --days 7 "$@"
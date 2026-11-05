"""Protocol smoke test only: acknowledge each packet without raising an alert."""
import json
import sys

for line in sys.stdin:
    json.loads(line)
    print(json.dumps({"alert": False}), flush=True)

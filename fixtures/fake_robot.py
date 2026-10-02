"""Synthetic robot process used to exercise the scenario runner."""

import json
from pathlib import Path
import sys


events = [
    {"at_ms": 0, "event": "goal_sent"},
    {"at_ms": 250, "event": "obstacle_detected"},
    {"at_ms": 275, "event": "robot_stopped"},
    {"at_ms": 400, "event": "route_replanned"},
    {"at_ms": 900, "event": "goal_reached"},
]
Path(sys.argv[1]).write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")

"""Tests run the app in demo mode so made-up fixture data (tests/fixtures/) is available."""

import os

from app.fixtures import DEMO_ENV

for key, value in DEMO_ENV.items():
    os.environ.setdefault(key, value)

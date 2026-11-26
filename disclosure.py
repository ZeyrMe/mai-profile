"""Disclosure advances only on new real inbound messages, never on reads."""

import math
import random
import time
from collections import OrderedDict


class Clarity:
    def __init__(self):
        self.rows = OrderedDict()
        self.seen = OrderedDict()

    def value(self, key, config, now=None):
        now = time.monotonic() if now is None else now
        row = self.rows.get(key)
        if not row:
            return 0.0
        return row[0] * math.exp2(-max(0, now - row[1]) / (config.half_life_minutes * 60))

    def advance(self, key, message_id, resistance, multiplier, config, now=None):
        if not message_id or (message_id, key) in self.seen:
            return
        now = time.monotonic() if now is None else now
        value = self.value(key, config, now)
        gain = max(0, config.shy_increment + random.uniform(-config.shy_jitter, config.shy_jitter))
        gain *= getattr(config, f"resistance_{resistance}") * multiplier
        self.rows[key] = (min(1.0, value + gain * (1 - value * 0.5)), now)
        self.rows.move_to_end(key)
        self.seen[(message_id, key)] = True
        while len(self.rows) > config.max_clarity_entries:
            self.rows.popitem(last=False)
        while len(self.seen) > config.max_seen_messages:
            self.seen.popitem(last=False)

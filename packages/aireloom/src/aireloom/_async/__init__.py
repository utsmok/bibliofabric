"""I/O modules; the single source of truth for the generated sync twins.

``scripts/unasync.py`` generates ``aireloom._sync`` from these modules at
dev time. Only modules that do I/O live here; pure modules stay one level up
and are imported by both variants.
"""

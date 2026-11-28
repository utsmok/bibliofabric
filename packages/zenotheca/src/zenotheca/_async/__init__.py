"""Async I/O modules; the single source of truth for the sync twins.

``scripts/unasync.py`` generates ``zenotheca._sync`` from these modules at
dev time. Only modules that do I/O live here; pure modules (config, dialect
constants, filters, ids, models, unwrapper) stay one level up and are
imported by both variants.
"""

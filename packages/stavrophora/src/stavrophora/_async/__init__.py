"""Async I/O modules; the single source of truth for the sync twins.

``scripts/unasync.py`` generates ``stavrophora._sync`` from these modules at
dev time. Only modules that do I/O live here; pure modules (models, filters,
the dialect constants in ``stavrophora.dialect``, config, unwrapper) stay one
level up and are imported by both variants.
"""

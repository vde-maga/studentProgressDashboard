"""Application layer: use-cases orchestrating the domain and repositories.

Framework-free. Services depend only on the domain ports, so they can be unit
tested with in-memory fakes and never import FastAPI or SQLAlchemy.
"""

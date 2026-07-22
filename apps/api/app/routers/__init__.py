"""HTTP routers (one module per domain area).

Each router declares FastAPI endpoints and returns the data/source_trace/warnings
envelope. Routers stay thin — query and business logic live in `app.services`.
Members: health, sources, banxico, tariff, countries, agreements, calculator,
classify, wiki.
"""

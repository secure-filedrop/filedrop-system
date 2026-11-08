"""FastAPI entry point for the Secure File Drop backend."""

from fastapi import FastAPI

app = FastAPI(title="Secure File Drop")


@app.get("/health")
async def health() -> dict[str, str]:
    """Report application liveness without accessing external services."""
    return {"status": "ok"}

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer

from .config import get_settings
from .dependencies import build_search_service
from .evaluation import evaluate
from .indexing import index_dataset

app = typer.Typer(help="NEXUS data/index administration")


@app.command()
def ingest(
    dataset: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True),
    limit: int | None = typer.Option(default=None, min=1),
    batch_size: int = typer.Option(default=256, min=16, max=2048),
) -> None:
    result = index_dataset(get_settings(), dataset, limit=limit, batch_size=batch_size)
    typer.echo(json.dumps(result, indent=2))


@app.command("evaluate")
def evaluate_command(
    dataset: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True),
    limit: int | None = typer.Option(default=None, min=1),
    k: int = typer.Option(default=10, min=1, max=50),
) -> None:
    async def run() -> dict[str, object]:
        service = build_search_service(get_settings())
        try:
            return await evaluate(service, dataset / "evaluation_queries.jsonl.gz", limit=limit, k=k)
        finally:
            close = getattr(service.semantic, "close", None)
            if close is not None:
                await close()

    typer.echo(json.dumps(asyncio.run(run()), indent=2))


if __name__ == "__main__":
    app()

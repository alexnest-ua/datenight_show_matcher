"""Command-line interface — the primary, spec-compliant deliverable.

    get-show @art_girl                 # the PDF's /get-show command
    datenight get-show @tech_babe --json
    datenight serve                    # FastAPI + SSE (for the web demo)
    datenight mcp-server               # run the MCP server on stdio
    datenight seed-db                  # (re)build the SQLite catalog
    datenight demo-fixtures            # record offline runs for the frontend
    datenight info                     # show resolved config / mode
"""

from __future__ import annotations

import asyncio
import json
import sys

import typer
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.config import RunMode, get_settings
from app.models import (
    STAGE_LABELS,
    STAGE_ORDER,
    EventType,
    PipelineEvent,
    RunResult,
)

app = typer.Typer(
    add_completion=False,
    help="DateNight Show Matcher — Claude orchestrator + sub-agents.",
    no_args_is_help=True,
)
console = Console()

_PLATFORM_STYLE = {"netflix": "bold red", "hbo": "bold magenta", "prime": "bold cyan"}
_STATUS_ICON = {
    "queued": ("○", "dim"),
    "running": ("◐", "yellow"),
    "done": ("●", "green"),
    "failed": ("✗", "bold red"),
}


def _platform_badges(platforms: list[str]) -> Text:
    text = Text()
    for i, p in enumerate(platforms):
        if i:
            text.append(" ")
        text.append(f" {p.upper()} ", style=_PLATFORM_STYLE.get(p.lower(), "bold white"))
    return text or Text("—", style="dim")


class _Renderer:
    """Holds live pipeline state and renders it as a Rich renderable."""

    def __init__(self, username: str, mode: str):
        self.username = username
        self.mode = mode
        self.status = {s: "queued" for s in STAGE_ORDER}
        self.message = {s: "" for s in STAGE_ORDER}
        self.attempt = 1
        self.repicks: list[str] = []
        self.result: RunResult | None = None
        self.error: str | None = None

    def update(self, ev: PipelineEvent) -> None:
        stage = ev.stage.value if ev.stage else None
        if ev.event is EventType.STAGE_STARTED and stage:
            self.status[stage] = "running"
            self.message[stage] = ev.message
        elif ev.event is EventType.STAGE_COMPLETED and stage:
            self.status[stage] = "done"
            self.message[stage] = ev.message
        elif ev.event is EventType.STAGE_FAILED and stage:
            self.status[stage] = "failed"
            self.message[stage] = ev.message
        elif ev.event is EventType.REPICK:
            self.attempt = ev.attempt
            if isinstance(ev.data, dict):
                for ex in ev.data.get("excluded", []):
                    self.repicks.append(f"{ex['title']} — {ex['reason']}")
            # send matcher/checker back to queued for the new attempt
            self.status["show_matcher"] = "queued"
            self.status["streaming_checker"] = "queued"
        elif ev.event is EventType.RUN_COMPLETED and ev.data:
            self.result = RunResult(**ev.data)
        elif ev.event is EventType.RUN_FAILED:
            self.error = ev.message

    def _stage_table(self) -> Table:
        table = Table.grid(padding=(0, 1))
        table.add_column(justify="center", width=3)
        table.add_column(style="bold", width=20)
        table.add_column(style="dim", overflow="fold")
        for stage in STAGE_ORDER:
            icon, style = _STATUS_ICON[self.status[stage]]
            table.add_row(Text(icon, style=style), STAGE_LABELS[stage], self.message[stage])
        return table

    def __rich__(self) -> Group:
        mode_style = "green" if self.mode == "real" else "yellow"
        header = Text.assemble(
            ("🍿 DateNight Show Matcher  ", "bold"),
            (f"[{self.mode.upper()}]", mode_style),
            (f"   {self.username}", "bold cyan"),
        )
        parts: list = [Panel(self._stage_table(), title=header, border_style="blue")]

        if self.repicks:
            rp = Text("\n".join(f"↺ {r}" for r in self.repicks), style="yellow")
            parts.append(Panel(rp, title="Re-picks", border_style="yellow"))

        if self.error:
            parts.append(
                Panel(Text(self.error, style="bold red"), title="Failed", border_style="red")
            )

        if self.result:
            parts.append(self._result_group(self.result))
        return Group(*parts)

    def _result_group(self, result: RunResult) -> Group:
        prof = result.profile
        prof_table = Table.grid(padding=(0, 1))
        prof_table.add_column(style="bold dim", width=14)
        prof_table.add_column()
        prof_table.add_row("Interests", ", ".join(prof.primary_interests))
        prof_table.add_row("Vibe", prof.aesthetic_vibe)
        prof_table.add_row("Genres", ", ".join(prof.recommended_genres))
        blocks: list = [Panel(prof_table, title="Her vibe", border_style="magenta")]

        for i, pick in enumerate(result.picks, 1):
            title_line = Text.assemble(
                (f"#{i}  ", "bold yellow"),
                (pick.title, "bold"),
                (f"  ({pick.year})" if pick.year else "", "dim"),
            )
            body = Group(
                title_line,
                Text(", ".join(pick.genres), style="dim italic") if pick.genres else Text(""),
                Text(pick.why),
                Text.assemble(("watch on ", "dim"), _platform_badges(pick.platforms)),
            )
            blocks.append(Panel(body, border_style="green"))

        if result.excluded:
            ex = Text("\n".join(f"✗ {e.title} — {e.reason}" for e in result.excluded), style="dim")
            blocks.append(
                Panel(ex, title="Skipped (not on your subscriptions)", border_style="dim")
            )

        footer = Text(
            f"{len(result.picks)} pick(s) · {result.attempts} matcher attempt(s) · "
            f"subscriptions: {', '.join(p.upper() for p in result.user_platforms)}",
            style="dim",
        )
        blocks.append(footer)
        return Group(*blocks)


async def _run_live(username: str) -> _Renderer | None:
    from app.graph.pipeline import run_pipeline

    settings = get_settings()
    renderer = _Renderer(username, settings.effective_mode.value)
    with Live(renderer, console=console, refresh_per_second=12, transient=False) as live:
        async for ev in run_pipeline(username, settings):
            renderer.update(ev)
            live.update(renderer)
    return renderer


@app.command("get-show")
def get_show(
    username: str = typer.Argument(..., help="Instagram handle, e.g. @art_girl"),
    json_out: bool = typer.Option(False, "--json", help="Print the raw RunResult JSON and exit."),
) -> None:
    """Profile a handle and recommend 3 date-night shows on your subscriptions."""
    if json_out:
        from app.graph.pipeline import run_pipeline_to_result

        result = asyncio.run(run_pipeline_to_result(username))
        console.print_json(result.model_dump_json())
        return
    renderer = asyncio.run(_run_live(username))
    if renderer and renderer.error:
        raise typer.Exit(code=1)


@app.command("serve")
def serve(
    host: str | None = typer.Option(None, help="Override API_HOST."),
    port: int | None = typer.Option(None, help="Override API_PORT."),
    reload: bool = typer.Option(False, help="Auto-reload (dev)."),
) -> None:
    """Run the FastAPI + SSE backend (powers the web demo)."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.api:app",
        host=host or settings.api_host,
        port=port or settings.api_port,
        reload=reload,
        log_level=settings.log_level.lower(),
    )


@app.command("mcp-server")
def mcp_server() -> None:
    """Run the local MCP server on stdio (also runnable via `python -m app.mcp_server.server`)."""
    from app.mcp_server.server import main

    main()


@app.command("seed-db")
def seed_db(force: bool = typer.Option(False, help="Drop and rebuild.")) -> None:
    """(Re)build the SQLite catalog the MCP server queries."""
    from app.data_access.catalog import seed_sqlite

    path = seed_sqlite(force=force)
    console.print(f"[green]Seeded[/green] {path}")


@app.command("demo-fixtures")
def demo_fixtures(
    out_dir: str | None = typer.Option(None, help="Output dir (default frontend/src/demo)."),
) -> None:
    """Record offline (mock) runs to JSON for the frontend's demo mode."""
    asyncio.run(_record_fixtures(out_dir))


@app.command("info")
def info() -> None:
    """Show resolved configuration and mode."""
    from app.mock_data.profiles import known_handles

    s = get_settings()
    table = Table(title="DateNight Show Matcher — config")
    table.add_column("setting", style="bold")
    table.add_column("value")
    table.add_row("effective mode", s.effective_mode.value)
    table.add_row("API key present", "yes" if s.has_api_key else "no")
    table.add_row("model (analysis)", s.model_analysis)
    table.add_row("model (fast)", s.model_fast)
    table.add_row("user platforms", ", ".join(s.user_platforms))
    table.add_row("max re-picks", str(s.max_repicks))
    table.add_row("known handles", ", ".join(known_handles()))
    console.print(table)


async def _record_fixtures(out_dir: str | None) -> None:
    from pathlib import Path

    from app.config import REPO_ROOT
    from app.graph.pipeline import run_pipeline

    settings = get_settings().model_copy(update={"app_mode": RunMode.MOCK})
    handles = ["@art_girl", "@tech_babe", "@fitness_jane", "@bookworm_bella"]
    target = Path(out_dir) if out_dir else REPO_ROOT / "frontend" / "src" / "demo"
    target.mkdir(parents=True, exist_ok=True)

    for handle in handles:
        events: list[dict] = []
        async for ev in run_pipeline(handle, settings):
            events.append(ev.model_dump(mode="json"))
        key = handle.lstrip("@").lower()
        path = target / f"{key}.json"
        path.write_text(
            json.dumps({"username": handle, "mode": "mock", "events": events}, indent=2),
            encoding="utf-8",
        )
        console.print(f"[green]Recorded[/green] {path}  ({len(events)} events)")


def run_get_show() -> None:
    """Console-script entrypoint for `get-show` (prepends the subcommand)."""
    sys.argv.insert(1, "get-show")
    app()


if __name__ == "__main__":
    app()

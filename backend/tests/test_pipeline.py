"""End-to-end pipeline behaviour (mock mode): the re-pick loop and event stream."""

from app.graph.pipeline import run_pipeline, run_pipeline_to_result
from app.models import EventType


async def test_repick_loop_excludes_prime_only():
    result = await run_pipeline_to_result("@art_girl")
    assert result.mode == "mock"
    assert result.attempts == 2  # first attempt had a prime-only pick -> one re-pick
    assert len(result.picks) == 3

    titles = {p.title for p in result.picks}
    assert "Fleabag" not in titles
    assert any(e.title == "Fleabag" for e in result.excluded)

    for pick in result.picks:
        assert pick.platforms, "every final pick must stream on a subscribed platform"
        assert set(pick.platforms) <= {"netflix", "hbo"}


async def test_happy_path_single_attempt():
    result = await run_pipeline_to_result("@fitness_jane")
    assert result.attempts == 1
    assert len(result.picks) == 3
    assert not result.excluded


async def test_unknown_handle_still_resolves():
    result = await run_pipeline_to_result("@some_random_person")
    assert len(result.picks) == 3


async def test_event_stream_shape():
    events = [ev async for ev in run_pipeline("@art_girl")]
    assert events[0].event is EventType.RUN_STARTED
    assert events[-1].event is EventType.RUN_COMPLETED
    assert any(e.event is EventType.REPICK for e in events)
    # seq is a 0-based monotonic counter
    assert [e.seq for e in events] == list(range(len(events)))
    # elapsed_ms never decreases
    times = [e.elapsed_ms for e in events]
    assert times == sorted(times)


async def test_max_repicks_is_bounded(monkeypatch):
    # Force the matcher to only ever return a prime-only title -> can never satisfy.
    import app.graph.pipeline as pipeline_mod
    from app.models import ShowCandidate

    async def only_prime(*args, **kwargs):
        return [ShowCandidate(title="The Boys", why="prime only")]

    monkeypatch.setattr(pipeline_mod, "match_shows", only_prime)
    result = await run_pipeline_to_result("@art_girl")
    # Gives up cleanly at the cap rather than looping forever.
    assert result.picks == []
    assert result.attempts <= 4  # max_repicks (3) + 1

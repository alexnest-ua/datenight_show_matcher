from app.config import get_settings
from app.llm.provider import MockProvider, build_provider
from app.mock_data.profiles import get_profile


def test_build_provider_defaults_to_mock():
    assert isinstance(build_provider(get_settings()), MockProvider)


async def test_mock_profile_has_signal():
    provider = MockProvider(get_settings())
    profile = await provider.profile_interests(get_profile("@art_girl"))
    assert profile.primary_interests
    assert profile.recommended_genres
    assert profile.aesthetic_vibe


async def test_mock_match_respects_off_limits_and_attempts():
    provider = MockProvider(get_settings())
    profile = await provider.profile_interests(get_profile("@art_girl"))

    first = await provider.match_shows(profile, handle="@art_girl", off_limits=[], attempt=1)
    assert any(c.title == "Fleabag" for c in first)

    filtered = await provider.match_shows(
        profile, handle="@art_girl", off_limits=["Fleabag"], attempt=1
    )
    assert all(c.title != "Fleabag" for c in filtered)

    # Past the scripted attempts -> no more candidates (loop will give up).
    exhausted = await provider.match_shows(profile, handle="@art_girl", off_limits=[], attempt=9)
    assert exhausted == []

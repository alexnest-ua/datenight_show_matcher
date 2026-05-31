"""Deterministic, scripted outputs for the offline mock-LLM.

Keyed by Instagram handle, these reproduce — without any API key — exactly what
the analytical agents would plausibly return:
  * `interest`  -> the Interest Profiler's InterestProfile
  * `attempts`  -> the Show Matcher's ranked candidates, per attempt

`@art_girl` and `@tech_babe` are scripted so their first attempt includes a
PRIME-only title (Fleabag / Mr. Robot). The Streaming Checker drops it and the
matcher re-picks on attempt 2 — demonstrating the conditional loop. `@fitness_jane`
and `@bookworm_bella` resolve cleanly on the first attempt.
"""

from __future__ import annotations

from app.models import InterestProfile, ShowCandidate


class ProfileScript:
    def __init__(self, interest: InterestProfile, attempts: list[list[ShowCandidate]]):
        self.interest = interest
        self.attempts = attempts


def _c(title: str, why: str) -> ShowCandidate:
    # year/genres are enriched from the catalog downstream.
    return ShowCandidate(title=title, why=why)


SCRIPTS: dict[str, ProfileScript] = {
    "art_girl": ProfileScript(
        interest=InterestProfile(
            primary_interests=[
                "analog & 35mm film photography",
                "indie / arthouse cinema",
                "vintage & thrifted fashion",
                "ceramics and gallery-going",
                "slow, intentional living",
            ],
            aesthetic_vibe="soft, grainy film-still energy — vintage, creative and a "
            "little melancholic, romanticising the ordinary",
            recommended_genres=["prestige drama", "dark comedy", "romance", "coming-of-age"],
        ),
        attempts=[
            [
                _c("Fleabag", "Witty, intimate and achingly stylish — its bittersweet "
                   "humour is catnip for an arthouse romantic who reads Didion on slow mornings."),
                _c("The White Lotus", "Gorgeous to look at and impossible not to dissect "
                   "afterward — perfect for someone who teared up in the Rothko room."),
                _c("Normal People", "Tender, beautifully shot and quietly devastating — "
                   "matches her film-grain, romanticise-the-ordinary energy."),
            ],
            [
                _c("Sex Education", "Warm, funny and visually bold with real heart — easy, "
                   "charming date-night watching that still has something to say."),
                _c("Euphoria", "Stylistically daring and painterly — speaks to her "
                   "aesthetic eye, though it runs bold."),
                _c("Bridgerton", "Lush costuming and swoony romance — pure aesthetic "
                   "comfort viewing."),
            ],
        ],
    ),
    "tech_babe": ProfileScript(
        interest=InterestProfile(
            primary_interests=[
                "building startups / shipping product",
                "machine learning & AI",
                "mechanical keyboards & gadgets",
                "speculative sci-fi",
                "cold brew–fuelled deep work",
            ],
            aesthetic_vibe="high-energy builder with a dark, near-future sci-fi "
            "imagination — fast-talking, opinionated, terminally online",
            recommended_genres=[
                "sci-fi", "psychological thriller", "tech thriller", "dystopian drama",
            ],
        ),
        attempts=[
            [
                _c("Mr. Robot", "A paranoid, beautifully shot hacker thriller — basically "
                   "her timeline rendered as prestige TV."),
                _c("Black Mirror", "Near-future 'documentary about next Tuesday' sci-fi she "
                   "already can't stop thinking about — instant debate fuel."),
                _c("Westworld", "Big-ideas sci-fi about AI and free will — exactly the kind "
                   "of implications she loves to argue at 2am."),
            ],
            [
                _c("Dark", "Mind-bending sci-fi with airtight plotting — a puzzle box for "
                   "someone who solders her own keyboards."),
                _c("The Last of Us", "Sci-fi with real emotional stakes — gripping and "
                   "very discussable."),
                _c("Watchmen", "Cerebral, stylish and political superhero sci-fi — smart "
                   "enough to keep her arguing."),
            ],
        ],
    ),
    "fitness_jane": ProfileScript(
        interest=InterestProfile(
            primary_interests=[
                "marathon & endurance running",
                "strength training",
                "wellness & nutrition",
                "hiking and the outdoors",
                "travel",
            ],
            aesthetic_vibe="sunrise-chasing, good-vibes wellness energy — disciplined "
            "but warm and upbeat",
            recommended_genres=["feel-good comedy", "sitcom", "adventure", "reality competition"],
        ),
        attempts=[
            [
                _c("New Girl", "Sunny, low-stakes and endlessly rewatchable — the feel-good "
                   "comfort she puts on for rest-day stretching."),
                _c("Brooklyn Nine-Nine", "Fast, warm and funny — easy banter that keeps a "
                   "date light and laughing."),
                _c("Outer Banks", "Sun-soaked adventure with momentum — matches her "
                   "outdoorsy, next-trip-already-planned energy."),
            ],
        ],
    ),
    "bookworm_bella": ProfileScript(
        interest=InterestProfile(
            primary_interests=[
                "classic & literary fiction",
                "cosy mysteries",
                "cottagecore & tea culture",
                "history",
                "annotating books",
            ],
            aesthetic_vibe="candlelit cottagecore dark-academia — bookish, nostalgic and "
            "quietly romantic",
            recommended_genres=["period drama", "prestige drama", "mystery", "fantasy"],
        ),
        attempts=[
            [
                _c("The Crown", "Sumptuous period prestige — catnip for a Victorian-"
                   "doorstopper, history-nerd reader."),
                _c("House of the Dragon", "Epic, lavish fantasy with palace intrigue — "
                   "scratches the same itch as a 600-page saga."),
                _c("Bridgerton", "Cosy, romantic and beautifully costumed — period-drama "
                   "comfort with conversation built in."),
            ],
        ],
    ),
}


_GENERIC = ProfileScript(
    interest=InterestProfile(
        primary_interests=[
            "live music & festivals",
            "food & new restaurants",
            "weekend travel",
            "vinyl records",
            "spontaneous adventures",
        ],
        aesthetic_vibe="social, spontaneous and fun-loving — always chasing the next experience",
        recommended_genres=["feel-good comedy", "drama", "thriller"],
    ),
    attempts=[
        [
            _c("Stranger Things", "A crowd-pleasing sci-fi adventure with nostalgia and "
               "heart — almost everyone enjoys it, ideal common ground for a new date."),
            _c("Succession", "Razor-sharp and addictive — prestige drama that sparks "
               "endless 'who's the worst' debate."),
            _c("The Last of Us", "Emotional, gripping and gorgeously made — easy to get "
               "invested in together."),
        ],
    ],
)


def _key(handle: str) -> str:
    return handle.strip().lstrip("@").lower()


def get_script(handle: str) -> ProfileScript:
    return SCRIPTS.get(_key(handle), _GENERIC)

"""Pre-baked Instagram profile dumps.

The assignment is explicit: do NOT build a real scraper. The Insta Reader agent
"imitates" reading a profile by returning one of these dumps for a known handle,
or a generic dump for an unknown one. Each dump is deliberately rich (bio + post
captions + hashtags) so the Interest Profiler has genuine signal to analyse.
"""

from __future__ import annotations

from app.models import ProfileDump

PROFILES: dict[str, ProfileDump] = {
    "art_girl": ProfileDump(
        handle="@art_girl",
        display_name="mara · 35mm",
        bio="painter & analog photographer 🎞️ | thrifted fits | gallery hopping > brunch | "
        "ceramics on sundays | romanticising the ordinary",
        posts=[
            "spent the whole afternoon in the darkroom, smell of fixer >>> any perfume",
            "found a 1970s trench at the flea market for €8, she's coming on every date now",
            "Rothko room at the museum made me cry a little, no notes",
            "slow morning: oat latte, Joan Didion, grainy light through the blinds",
            "my ceramics are lopsided but they're MINE 🏺",
            "rewatched a Wong Kar-wai film for the mood lighting alone",
        ],
        hashtags=[
            "filmphotography", "35mm", "thrifted", "slowliving",
            "arthouse", "ceramics", "analogvibes", "museumdate",
        ],
    ),
    "tech_babe": ProfileDump(
        handle="@tech_babe",
        display_name="Nova ⚡ builds things",
        bio="founder @ stealth | ex-ML eng | mechanical keyboards & cold brew | "
        "sci-fi hoarder | shipping > talking | she/her",
        posts=[
            "shipped a feature at 2am fueled by cold brew and spite, classic",
            "my mechanical keyboard arrived and the thock is *chef's kiss* ⌨️",
            "rewatched Black Mirror, genuinely cannot stop thinking about the implications",
            "hot take: the best sci-fi is the one that's basically a documentary "
            "about next tuesday",
            "soldering my own split keyboard this weekend, wish me luck",
            "demo day prep — investors love a clean dashboard and a scary roadmap",
        ],
        hashtags=[
            "buildinpublic", "startup", "machinelearning", "scifi",
            "mechkeys", "coldbrew", "dystopia", "founderlife",
        ],
    ),
    "fitness_jane": ProfileDump(
        handle="@fitness_jane",
        display_name="Jane | run · lift · travel",
        bio="marathon #4 loading 🏃‍♀️ | strength coach | smoothie scientist | "
        "sunrise > sleep | good vibes only ☀️",
        posts=[
            "5am club checking in — sunrise long run hits different",
            "meal prep sunday: 12 containers, 0 regrets 🥗",
            "PR on deadlifts today!! body is a temple etc etc",
            "weekend hike to the ridge, the view was the whole personality",
            "trying to convince everyone that a smoothie is a valid dinner",
            "rest days are for sitcoms and stretching, fight me",
        ],
        hashtags=[
            "marathontraining", "strengthtraining", "wellness", "hiking",
            "mealprep", "goodvibes", "5amclub", "feelgood",
        ],
    ),
    "bookworm_bella": ProfileDump(
        handle="@bookworm_bella",
        display_name="Bella reads ✦",
        bio="perpetually mid-novel 📚 | classics & cosy mysteries | tea snob | "
        "cottagecore enthusiast | history nerd | TBR longer than my life",
        posts=[
            "finished a 600-page Victorian doorstopper and immediately bought the sequel",
            "tea + rain + a murder mystery = my entire personality this season ☕️",
            "pressed flowers between the pages again, future me will be delighted",
            "the costuming in period dramas is doing more for me than any plot",
            "annotated my favourite novel so heavily it's basically a diary now",
            "cottage daydream: woodsmoke, wool socks, candlelight, a good whodunit",
        ],
        hashtags=[
            "bookstagram", "classics", "cosymystery", "cottagecore",
            "perioddrama", "tealover", "historynerd", "darkacademia",
        ],
    ),
}


def _normalise(handle: str) -> str:
    return handle.strip().lstrip("@").lower()


def get_profile(handle: str) -> ProfileDump:
    """Return the dump for a known handle, or a plausible generic profile.

    Unknown handles still produce a usable dump so the pipeline always has
    something to profile (and the demo never dead-ends).
    """
    key = _normalise(handle)
    if key in PROFILES:
        return PROFILES[key]
    pretty = "@" + (key or "someone")
    return ProfileDump(
        handle=pretty,
        display_name=key or "someone",
        bio="living for good food, good music and spontaneous weekend trips ✨ | "
        "concert tees | always planning the next adventure",
        posts=[
            "another festival in the books, ears ringing, heart full 🎶",
            "found the coziest little ramen spot downtown, obsessed",
            "spontaneous road trip because the weather said so",
            "sunday reset: vinyl on, candles lit, phone away",
            "collecting passport stamps like they're trophies ✈️",
        ],
        hashtags=["music", "foodie", "travel", "weekendvibes", "concerts", "wanderlust"],
    )


def known_handles() -> list[str]:
    return [profile.handle for profile in PROFILES.values()]

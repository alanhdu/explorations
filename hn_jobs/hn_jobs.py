# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "aiohttp[speedups]",
#     "aiolimiter",
#     "tqdm",
# ]
# ///
import html
import re
from tqdm.auto import tqdm
from typing import Any
import aiohttp
import asyncio
from aiolimiter import AsyncLimiter


BASE_URL = "https://hacker-news.firebaseio.com/v0/"
GOOD_PATTERNS = [
    "Bay Area",
    "Boston",
    "CA",
    "Chicago",
    "Los Angeles",
    "NY",
    "New York",
    "SF",
    "San Francisco",
    "Seattle",
    "US",
    "USA",
    "United States",
]
BAD_PATTERNS = [
    "no-code",
    "bitcoin",
    "cryptocurrency",
    "consulting",
    "enterprise sales",
]


def match_any(substrs: list[str]) -> re.Pattern:
    pattern = "|".join(f"({p})" if p.upper() == p else f"(?i:{p})" for p in substrs)
    return re.compile(pattern)


async def fetch_item(
    limiter: AsyncLimiter, session: aiohttp.ClientSession, item: int
) -> Any:
    async with limiter:
        async with session.get(f"{BASE_URL}/item/{item}.json") as response:
            return await response.json()


async def fetch_jobs(root: int):
    good = match_any(GOOD_PATTERNS)
    bad = match_any(BAD_PATTERNS)
    limiter = AsyncLimiter(25, time_period=1)
    async with aiohttp.ClientSession() as session:
        out = await fetch_item(limiter, session, root)
        futures = []
        for kid in out["kids"]:
            futures.append(fetch_item(limiter, session, kid))

        descriptions = []

        for fut in tqdm(asyncio.as_completed(futures), total=len(futures)):
            result = await fut
            if "text" not in result:
                continue
            description: str = html.unescape(result["text"])

            if good.search(description) and not bad.search(description):
                descriptions.append(description)

        print(("\n" + "-" * 80 + "\n").join(sorted(descriptions)))


if __name__ == "__main__":
    asyncio.run(fetch_jobs(44434576))

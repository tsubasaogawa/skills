#!/usr/bin/env python3

import datetime
import json
import urllib.parse
import urllib.request

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"


def get_yesterday_timestamps():
    today = datetime.datetime.now(datetime.timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    yesterday_start = today - datetime.timedelta(days=1)
    yesterday_end = today
    return yesterday_start, yesterday_end


def build_query(start_dt, end_dt):
    numeric_filters = (
        f"created_at_i>={int(start_dt.timestamp())},"
        f"created_at_i<{int(end_dt.timestamp())},points>100"
    )
    params = {
        "tags": "story",
        "numericFilters": numeric_filters,
        "hitsPerPage": 100,
    }
    url = HN_SEARCH_URL + "?" + urllib.parse.urlencode(params)
    return url, params


def fetch_hn_stories(url):
    request = urllib.request.Request(url, headers={"User-Agent": "hn-digest-skill/0.1"})

    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)

    stories = []
    for story in payload.get("hits", []):
        title = story.get("title")
        if not title:
            continue
        stories.append(
            {
                "id": str(story.get("objectID", "")),
                "title": title,
                "url": story.get("url") or "#",
            }
        )
    return stories


def main():
    start_dt, end_dt = get_yesterday_timestamps()
    url, params = build_query(start_dt, end_dt)
    stories = fetch_hn_stories(url)
    result = {
        "window_start_utc": start_dt.isoformat(),
        "window_end_utc": end_dt.isoformat(),
        "source": HN_SEARCH_URL,
        "query_url": url,
        "filters": {
            "tags": params["tags"],
            "numeric_filters": params["numericFilters"],
            "hits_per_page": params["hitsPerPage"],
        },
        "stories": stories,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")

# Comma-separated list of library keys to search in parallel
LIBRARY_KEYS = [k.strip() for k in os.environ.get("LIBRARY_KEYS", "nypl,londonlibraries").split(",") if k.strip()]
THUNDER_API_URL = "https://thunder.api.overdrive.com/v2/media/search"
CLIENT_ID = "dewey"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/14.0.2 Safari/605.1.15"
    ),
    "Referer": "https://libbyapp.com/",
    "Origin": "https://libbyapp.com",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if AUTH_TOKEN:
            token = request.headers.get("AUTHORIZATION", "") or request.headers.get("Authorization", "")
            if token.startswith("Bearer "):
                token = token[7:]
            if token != AUTH_TOKEN:
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def strip_html(text):
    if not text:
        return None
    return re.sub(r"<[^>]+>", "", text).strip() or None


def search_library(query, library_key, limit=10):
    params = {
        "query": query,
        "format": "audiobook-mp3",
        "perPage": limit,
        "page": 1,
        "x-client-id": CLIENT_ID,
        "libraryKey": library_key,
    }
    try:
        resp = requests.get(THUNDER_API_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []
    except requests.RequestException as e:
        app.logger.error(f"OverDrive search error ({library_key}): {e}")
        return []


def search_overdrive(query, author=None, limit=10):
    search_query = f"{query} {author}".strip() if author else query

    seen_ids = set()
    results = []

    with ThreadPoolExecutor(max_workers=len(LIBRARY_KEYS)) as executor:
        futures = {executor.submit(search_library, search_query, key, limit): key for key in LIBRARY_KEYS}
        for future in as_completed(futures):
            for item in future.result():
                item_id = str(item.get("id", "")) or item.get("reserveId", "")
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    results.append(item)

    return results


def format_result(item):
    creators = item.get("creators", [])
    authors = [
        c["name"] for c in creators
        if c.get("role", "").lower() in ("author", "other", "")
        and c.get("roleDiscipline", "").lower() != "audio"
    ]
    narrators = [
        c["name"] for c in creators
        if c.get("role", "").lower() == "narrator"
        or c.get("roleDiscipline", "").lower() == "audio"
    ]

    cover = None
    covers = item.get("covers", {})
    for size in ("cover510Wide", "cover300Wide", "cover150Wide"):
        if size in covers:
            cover = covers[size].get("href")
            break

    publisher = item.get("publisher", {}).get("name") if item.get("publisher") else None
    publish_date = item.get("publishDate", "")
    publish_year = publish_date[:4] if publish_date and len(publish_date) >= 4 else None
    subjects = item.get("subjects", [])
    genres = [s.get("name") for s in subjects if s.get("name")] or None
    description = strip_html(item.get("description"))
    reserve_id = item.get("reserveId", "")
    od_id = str(item.get("id", ""))

    result = {
        "id": reserve_id or od_id,
        "title": item.get("title", ""),
        "subtitle": item.get("subtitle") or None,
        "author": ", ".join(authors) if authors else None,
        "narrator": ", ".join(narrators) if narrators else None,
        "publisher": publisher,
        "publishedYear": publish_year,
        "description": description,
        "cover": cover,
        "genres": genres,
        "series": item.get("series") or None,
        "language": None,
    }

    return {k: v for k, v in result.items() if v is not None}


@app.route("/search")
@require_auth
def search():
    query = request.args.get("query", "").strip()
    author = request.args.get("author", "").strip() or None

    if not query:
        return jsonify({"error": "query parameter is required"}), 400

    items = search_overdrive(query, author=author)
    matches = [format_result(item) for item in items]

    return jsonify({"matches": matches})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "library_keys": LIBRARY_KEYS})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3847))
    app.run(host="0.0.0.0", port=port)

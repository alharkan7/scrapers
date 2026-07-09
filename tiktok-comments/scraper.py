#!/usr/bin/env python3
"""
Scrape TikTok video comments via the public web comment list API.

Usage:
  # Single video (test)
  python scraper.py --url "https://www.tiktok.com/@user/video/123" --max-pages 2

  # All URLs in links.txt
  python scraper.py --links links.txt

  # Cap comments per video
  python scraper.py --links links.txt --max-comments 500
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

COMMENT_API = "https://www.tiktok.com/api/comment/list/"
DEFAULT_HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/141.0.0.0 Safari/537.36"
    ),
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
}

VIDEO_ID_RE = re.compile(r"/video/(\d+)")
SHORT_ID_RE = re.compile(r"^\d+$")


def extract_video_id(url_or_id: str) -> str:
    """Extract aweme/video id from a TikTok URL or bare id."""
    value = url_or_id.strip()
    if not value:
        raise ValueError("Empty URL/id")

    if SHORT_ID_RE.match(value):
        return value

    match = VIDEO_ID_RE.search(value)
    if match:
        return match.group(1)

    # Fallback: last path segment if numeric
    path = urlparse(value).path.rstrip("/").split("/")
    if path and SHORT_ID_RE.match(path[-1]):
        return path[-1]

    raise ValueError(f"Could not extract video id from: {url_or_id}")


def load_links(path: Path) -> list[str]:
    """Load non-empty, non-comment lines from a links file."""
    links: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        links.append(line)
    return links


def normalize_comment(raw: dict[str, Any], video_id: str, video_url: str) -> dict[str, Any]:
    user = raw.get("user") or {}
    create_time = raw.get("create_time")
    created_at = None
    if create_time is not None:
        created_at = datetime.fromtimestamp(int(create_time), tz=timezone.utc).isoformat()

    return {
        "video_id": video_id,
        "video_url": video_url,
        "comment_id": raw.get("cid"),
        "text": raw.get("text"),
        "likes": raw.get("digg_count"),
        "reply_count": raw.get("reply_comment_total"),
        "language": raw.get("comment_language"),
        "create_time": create_time,
        "created_at": created_at,
        "author_pin": raw.get("author_pin"),
        "author_uid": user.get("uid"),
        "author_username": user.get("unique_id"),
        "author_nickname": user.get("nickname"),
    }


def fetch_comments_page(
    session: requests.Session,
    video_id: str,
    cursor: int = 0,
    count: int = 50,
) -> dict[str, Any]:
    params = {
        "aid": "1988",
        "aweme_id": video_id,
        "count": str(count),
        "cursor": str(cursor),
    }
    headers = {
        **DEFAULT_HEADERS,
        "referer": f"https://www.tiktok.com/video/{video_id}",
    }
    resp = session.get(COMMENT_API, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def scrape_video_comments(
    session: requests.Session,
    video_url: str,
    *,
    count: int = 50,
    max_pages: int | None = None,
    max_comments: int | None = None,
    delay: float = 1.5,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Scrape comments for one video with cursor pagination.

    Returns (comments, meta).
    """
    video_id = extract_video_id(video_url)
    comments: list[dict[str, Any]] = []
    cursor = 0
    page = 0
    total_reported: int | None = None
    has_more = True
    status_code = None

    print(f"  video_id={video_id}")

    while has_more:
        if max_pages is not None and page >= max_pages:
            print(f"  stopped: reached max_pages={max_pages}")
            break
        if max_comments is not None and len(comments) >= max_comments:
            print(f"  stopped: reached max_comments={max_comments}")
            break

        data = fetch_comments_page(session, video_id, cursor=cursor, count=count)
        status_code = data.get("status_code")
        if status_code not in (0, None):
            raise RuntimeError(
                f"TikTok API error status_code={status_code} "
                f"status_msg={data.get('status_msg')!r}"
            )

        if total_reported is None:
            total_reported = data.get("total")
            print(f"  reported total={total_reported}")

        raw_comments = data.get("comments") or []
        if not raw_comments:
            print("  no more comments in response")
            break

        for raw in raw_comments:
            comments.append(normalize_comment(raw, video_id, video_url))
            if max_comments is not None and len(comments) >= max_comments:
                break

        page += 1
        has_more = bool(data.get("has_more"))
        cursor = int(data.get("cursor") or 0)
        print(
            f"  page={page} got={len(raw_comments)} "
            f"total_so_far={len(comments)} has_more={has_more} cursor={cursor}"
        )

        if has_more and (
            max_pages is None or page < max_pages
        ) and (
            max_comments is None or len(comments) < max_comments
        ):
            time.sleep(delay)

    meta = {
        "video_id": video_id,
        "video_url": video_url,
        "reported_total": total_reported,
        "fetched": len(comments),
        "pages": page,
        "status_code": status_code,
        "truncated": not has_more,
    }
    return comments, meta


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape TikTok video comments")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="Single TikTok video URL or video id")
    src.add_argument("--links", type=Path, help="Text file with one URL per line")

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for JSON/CSV output (default: output)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Comments per API page (default: 50)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Max pages per video (default: unlimited)",
    )
    parser.add_argument(
        "--max-comments",
        type=int,
        default=None,
        help="Max comments per video (default: unlimited)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Seconds to sleep between page requests (default: 1.5)",
    )
    parser.add_argument(
        "--video-delay",
        type=float,
        default=2.0,
        help="Seconds to sleep between videos (default: 2.0)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.url:
        urls = [args.url]
    else:
        urls = load_links(args.links)
        if not urls:
            raise SystemExit(f"No URLs found in {args.links}")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    all_comments: list[dict[str, Any]] = []
    all_meta: list[dict[str, Any]] = []

    for i, url in enumerate(urls, start=1):
        print(f"\n[{i}/{len(urls)}] {url}")
        try:
            comments, meta = scrape_video_comments(
                session,
                url,
                count=args.count,
                max_pages=args.max_pages,
                max_comments=args.max_comments,
                delay=args.delay,
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            all_meta.append(
                {
                    "video_url": url,
                    "error": str(exc),
                    "fetched": 0,
                }
            )
            continue

        all_comments.extend(comments)
        all_meta.append(meta)

        # Per-video files
        vid = meta["video_id"]
        save_json(output_dir / f"{vid}_comments.json", comments)
        save_csv(output_dir / f"{vid}_comments.csv", comments)
        print(f"  saved {len(comments)} comments -> {output_dir / f'{vid}_comments.json'}")

        if i < len(urls):
            time.sleep(args.video_delay)

    # Combined outputs
    save_json(output_dir / "all_comments.json", all_comments)
    save_csv(output_dir / "all_comments.csv", all_comments)
    save_json(output_dir / "meta.json", all_meta)

    print(f"\nDone. {len(all_comments)} comments across {len(urls)} video(s).")
    print(f"Combined: {output_dir / 'all_comments.json'}")
    print(f"Meta:     {output_dir / 'meta.json'}")


if __name__ == "__main__":
    main()

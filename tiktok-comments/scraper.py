#!/usr/bin/env python3
"""
Scrape TikTok video comments via the public web comment list API.

Features:
  - Jittered delays between page/video requests
  - Pause & resume via progress.json (safe to Ctrl+C and re-run)
  - Periodic progress saves on a wall-clock interval

Usage:
  # Single video (test)
  python scraper.py --url "https://www.tiktok.com/@user/video/123" --max-pages 2

  # All URLs in links.txt
  python scraper.py --links links.txt

  # Resume a previous run (default if progress.json exists)
  python scraper.py --links links.txt --output-dir output/full

  # Fresh start (ignore existing progress)
  python scraper.py --links links.txt --fresh

  # Tune delays / checkpoint interval
  python scraper.py --links links.txt --delay 2.0 --jitter 0.4 --save-interval 180
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
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
PROGRESS_VERSION = 1


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


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


def sleep_with_jitter(base: float, jitter: float) -> float:
    """
    Sleep for a random duration around `base`.

    jitter is a fraction in [0, 1]: final sleep is uniform in
    [base * (1 - jitter), base * (1 + jitter)].
    Returns the actual sleep duration.
    """
    if base <= 0:
        return 0.0
    jitter = max(0.0, min(1.0, jitter))
    lo = max(0.0, base * (1.0 - jitter))
    hi = base * (1.0 + jitter)
    duration = random.uniform(lo, hi)
    time.sleep(duration)
    return duration


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


def atomic_write_json(path: Path, payload: Any) -> None:
    """Write JSON atomically via temp file + replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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

    content_type = (resp.headers.get("content-type") or "").lower()
    if "json" not in content_type:
        snippet = resp.text[:200].replace("\n", " ")
        raise RuntimeError(
            f"Non-JSON response (status={resp.status_code}, "
            f"content-type={content_type!r}): {snippet!r}"
        )
    return resp.json()


class ProgressStore:
    """
    Checkpoint store for pause/resume.

    progress.json tracks per-video cursor/status.
    Per-video comment files are rewritten on each checkpoint.
    """

    def __init__(self, output_dir: Path, save_interval: float) -> None:
        self.output_dir = output_dir
        self.progress_path = output_dir / "progress.json"
        self.save_interval = max(1.0, save_interval)
        self._last_save_mono = time.monotonic()
        self.data: dict[str, Any] = {
            "version": PROGRESS_VERSION,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "videos": {},
        }

    def load_or_init(self, urls: list[str], *, fresh: bool) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not fresh and self.progress_path.exists():
            self.data = load_json(self.progress_path)
            print(f"Resuming from {self.progress_path}")
        else:
            if fresh and self.progress_path.exists():
                print(f"Starting fresh (ignoring {self.progress_path})")
            self.data = {
                "version": PROGRESS_VERSION,
                "created_at": utc_now_iso(),
                "updated_at": utc_now_iso(),
                "videos": {},
            }

        videos: dict[str, Any] = self.data.setdefault("videos", {})
        for url in urls:
            video_id = extract_video_id(url)
            if video_id not in videos:
                videos[video_id] = self._new_video_entry(video_id, url)
            else:
                # Keep resume state; refresh URL in case links file changed slightly
                videos[video_id]["video_url"] = url

        self.save(force=True)

    @staticmethod
    def _new_video_entry(video_id: str, video_url: str) -> dict[str, Any]:
        return {
            "video_id": video_id,
            "video_url": video_url,
            "status": "pending",  # pending | in_progress | done | error
            "cursor": 0,
            "pages": 0,
            "fetched": 0,
            "reported_total": None,
            "has_more": True,
            "status_code": None,
            "error": None,
            "comments_file": f"{video_id}_comments.json",
            "csv_file": f"{video_id}_comments.csv",
            "started_at": None,
            "finished_at": None,
            "last_saved_at": None,
        }

    def get_video(self, video_id: str) -> dict[str, Any]:
        return self.data["videos"][video_id]

    def comments_path(self, video_id: str) -> Path:
        entry = self.get_video(video_id)
        return self.output_dir / entry["comments_file"]

    def csv_path(self, video_id: str) -> Path:
        entry = self.get_video(video_id)
        return self.output_dir / entry["csv_file"]

    def load_comments(self, video_id: str) -> list[dict[str, Any]]:
        path = self.comments_path(video_id)
        if not path.exists():
            return []
        data = load_json(path)
        if not isinstance(data, list):
            raise RuntimeError(f"Expected list in {path}")
        return data

    def save_video_comments(self, video_id: str, comments: list[dict[str, Any]]) -> None:
        atomic_write_json(self.comments_path(video_id), comments)
        save_csv(self.csv_path(video_id), comments)

    def update_video(self, video_id: str, **fields: Any) -> None:
        entry = self.get_video(video_id)
        entry.update(fields)
        entry["last_saved_at"] = utc_now_iso()

    def save(self, *, force: bool = False) -> bool:
        """
        Persist progress.json. Also used as the timed checkpoint gate.

        Returns True if a save was written.
        """
        now = time.monotonic()
        if not force and (now - self._last_save_mono) < self.save_interval:
            return False

        self.data["updated_at"] = utc_now_iso()
        atomic_write_json(self.progress_path, self.data)
        self._last_save_mono = now
        return True

    def checkpoint(
        self,
        video_id: str,
        comments: list[dict[str, Any]],
        *,
        force: bool = False,
        reason: str = "interval",
    ) -> bool:
        """
        Save comments + progress. Forced on complete/error/interrupt;
        otherwise only when save_interval has elapsed.
        """
        if not force and (time.monotonic() - self._last_save_mono) < self.save_interval:
            return False

        self.save_video_comments(video_id, comments)
        entry = self.get_video(video_id)
        entry["fetched"] = len(comments)
        entry["last_saved_at"] = utc_now_iso()
        self.save(force=True)
        print(
            f"  checkpoint ({reason}): "
            f"fetched={len(comments)} cursor={entry.get('cursor')} "
            f"pages={entry.get('pages')} -> {self.progress_path.name}"
        )
        return True


def scrape_video_comments(
    session: requests.Session,
    store: ProgressStore,
    video_url: str,
    *,
    count: int = 50,
    max_pages: int | None = None,
    max_comments: int | None = None,
    delay: float = 2.0,
    jitter: float = 0.4,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Scrape comments for one video with cursor pagination, jitter, and checkpoints.

    Resumes from progress.json cursor/pages and existing comments file when present.
    """
    video_id = extract_video_id(video_url)
    entry = store.get_video(video_id)

    # Only skip when the API itself is exhausted (not when a local limit stopped us).
    if entry.get("status") == "done" and not entry.get("has_more", False):
        comments = store.load_comments(video_id)
        print(
            f"  skip (already done): fetched={entry.get('fetched')} "
            f"pages={entry.get('pages')}"
        )
        return comments, dict(entry)

    comments = store.load_comments(video_id)
    seen_ids = {c.get("comment_id") for c in comments if c.get("comment_id")}

    cursor = int(entry.get("cursor") or 0)
    page = int(entry.get("pages") or 0)
    total_reported = entry.get("reported_total")
    has_more = bool(entry.get("has_more", True))
    status_code = entry.get("status_code")

    # If we have comments but think we are pending, continue from stored cursor
    if entry.get("status") in ("pending", "error", "in_progress"):
        store.update_video(
            video_id,
            status="in_progress",
            started_at=entry.get("started_at") or utc_now_iso(),
            error=None,
        )
        store.save(force=True)

    print(f"  video_id={video_id}")
    if page > 0 or cursor > 0 or comments:
        print(
            f"  resume: pages={page} cursor={cursor} "
            f"already_have={len(comments)} has_more={has_more}"
        )

    try:
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
                has_more = False
                break

            new_count = 0
            for raw in raw_comments:
                normalized = normalize_comment(raw, video_id, video_url)
                cid = normalized.get("comment_id")
                if cid and cid in seen_ids:
                    continue
                if cid:
                    seen_ids.add(cid)
                comments.append(normalized)
                new_count += 1
                if max_comments is not None and len(comments) >= max_comments:
                    break

            page += 1
            has_more = bool(data.get("has_more"))
            cursor = int(data.get("cursor") or 0)

            store.update_video(
                video_id,
                status="in_progress",
                cursor=cursor,
                pages=page,
                fetched=len(comments),
                reported_total=total_reported,
                has_more=has_more,
                status_code=status_code,
            )

            print(
                f"  page={page} new={new_count} raw={len(raw_comments)} "
                f"total_so_far={len(comments)} has_more={has_more} cursor={cursor}"
            )

            # Timed checkpoint (also flushes comments to disk)
            store.checkpoint(video_id, comments, force=False, reason="interval")

            should_continue = has_more and (
                max_pages is None or page < max_pages
            ) and (
                max_comments is None or len(comments) < max_comments
            )
            if should_continue:
                slept = sleep_with_jitter(delay, jitter)
                print(f"  sleep {slept:.2f}s (delay={delay}, jitter={jitter})")

        # Mark done only when TikTok reports no more pages. Local max-* limits
        # leave status as in_progress so a later run can continue.
        fully_complete = not has_more
        store.update_video(
            video_id,
            status="done" if fully_complete else "in_progress",
            cursor=cursor,
            pages=page,
            fetched=len(comments),
            reported_total=total_reported,
            has_more=has_more,
            status_code=status_code,
            finished_at=utc_now_iso() if fully_complete else None,
            error=None,
        )
        store.checkpoint(video_id, comments, force=True, reason="video_end")

    except KeyboardInterrupt:
        store.update_video(
            video_id,
            status="in_progress",
            cursor=cursor,
            pages=page,
            fetched=len(comments),
            reported_total=total_reported,
            has_more=has_more,
            status_code=status_code,
        )
        store.checkpoint(video_id, comments, force=True, reason="interrupt")
        print("\nInterrupted — progress saved. Re-run the same command to resume.")
        raise

    except Exception as exc:
        store.update_video(
            video_id,
            status="error",
            cursor=cursor,
            pages=page,
            fetched=len(comments),
            reported_total=total_reported,
            has_more=has_more,
            status_code=status_code,
            error=str(exc),
        )
        store.checkpoint(video_id, comments, force=True, reason="error")
        raise

    meta = dict(store.get_video(video_id))
    return comments, meta


def rebuild_combined(store: ProgressStore, video_ids: list[str]) -> tuple[int, int]:
    """Write all_comments.json/csv and meta.json from per-video artifacts."""
    all_comments: list[dict[str, Any]] = []
    all_meta: list[dict[str, Any]] = []

    for video_id in video_ids:
        entry = store.get_video(video_id)
        all_meta.append(dict(entry))
        if store.comments_path(video_id).exists():
            all_comments.extend(store.load_comments(video_id))

    atomic_write_json(store.output_dir / "all_comments.json", all_comments)
    save_csv(store.output_dir / "all_comments.csv", all_comments)
    atomic_write_json(store.output_dir / "meta.json", all_meta)
    return len(all_comments), len(video_ids)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape TikTok video comments (jitter + pause/resume)"
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="Single TikTok video URL or video id")
    src.add_argument("--links", type=Path, help="Text file with one URL per line")

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for JSON/CSV/progress output (default: output)",
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
        default=2.0,
        help="Base seconds between page requests (default: 2.0)",
    )
    parser.add_argument(
        "--jitter",
        type=float,
        default=0.4,
        help="Jitter fraction for page delay (default: 0.4 => ±40%%)",
    )
    parser.add_argument(
        "--video-delay",
        type=float,
        default=5.0,
        help="Base seconds between videos (default: 5.0)",
    )
    parser.add_argument(
        "--video-jitter",
        type=float,
        default=0.4,
        help="Jitter fraction for between-video delay (default: 0.4)",
    )
    parser.add_argument(
        "--save-interval",
        type=float,
        default=180.0,
        help="Seconds between timed progress checkpoints (default: 180)",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore existing progress.json and start from scratch",
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

    # Stable video id order matching input URLs
    video_ids = [extract_video_id(u) for u in urls]

    store = ProgressStore(args.output_dir, save_interval=args.save_interval)
    store.load_or_init(urls, fresh=args.fresh)

    print(
        f"Config: delay={args.delay}s jitter={args.jitter} "
        f"video_delay={args.video_delay}s save_interval={args.save_interval}s "
        f"output={args.output_dir}"
    )

    session = requests.Session()
    interrupted = False

    try:
        for i, url in enumerate(urls, start=1):
            video_id = video_ids[i - 1]
            entry = store.get_video(video_id)
            print(f"\n[{i}/{len(urls)}] {url}  [{entry.get('status')}]")

            if entry.get("status") == "done" and not entry.get("has_more", False):
                comments = store.load_comments(video_id)
                print(f"  already done ({len(comments)} comments)")
                continue

            try:
                comments, meta = scrape_video_comments(
                    session,
                    store,
                    url,
                    count=args.count,
                    max_pages=args.max_pages,
                    max_comments=args.max_comments,
                    delay=args.delay,
                    jitter=args.jitter,
                )
            except KeyboardInterrupt:
                interrupted = True
                break
            except Exception as exc:
                print(f"  ERROR: {exc}")
                # Progress already checkpointed inside scrape_video_comments
                continue

            print(
                f"  done: fetched={meta.get('fetched')} "
                f"pages={meta.get('pages')} status={meta.get('status')}"
            )

            if i < len(urls) and not interrupted:
                slept = sleep_with_jitter(args.video_delay, args.video_jitter)
                print(f"  video gap sleep {slept:.2f}s")

    finally:
        total_comments, n_videos = rebuild_combined(store, video_ids)
        store.save(force=True)
        print(f"\nCombined export: {total_comments} comments across {n_videos} video(s).")
        print(f"Progress: {store.progress_path}")
        print(f"Combined: {store.output_dir / 'all_comments.json'}")
        print(f"Meta:     {store.output_dir / 'meta.json'}")
        if interrupted:
            print("Paused. Re-run the same command to resume.")
            sys.exit(130)


if __name__ == "__main__":
    main()

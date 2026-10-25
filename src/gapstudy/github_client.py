"""Cached, rate-limit-aware GitHub REST client.

Every response (including 404s) is written to disk, so the same request is
never sent twice. Requests pinned to a commit SHA are immutable and are served
from the cache forever; pass ``refresh=True`` to revalidate a mutable request
with its ETag (a 304 reply does not count against the rate limit).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

log = logging.getLogger(__name__)

API_ROOT = "https://api.github.com"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "github"

JSON_ACCEPT = "application/vnd.github+json"
RAW_ACCEPT = "application/vnd.github.raw+json"


@dataclass
class CachedResponse:
    status: int
    body: str
    etag: str | None = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def json(self) -> Any:
        return json.loads(self.body)


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    def __init__(
        self,
        token: str | None = None,
        cache_dir: Path = DEFAULT_CACHE_DIR,
        session: requests.Session | None = None,
        max_retries: int = 5,
        min_remaining: int = 5,
    ) -> None:
        load_dotenv(PROJECT_ROOT / ".env")
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            log.warning("No GITHUB_TOKEN set; limited to 60 requests/hour.")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = session or requests.Session()
        self.max_retries = max_retries
        self.min_remaining = min_remaining
        self.network_calls = 0

    # ------------------------------------------------------------------ cache

    def _cache_path(self, url: str, params: dict | None, accept: str) -> Path:
        key = json.dumps([url, sorted((params or {}).items()), accept])
        digest = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / digest[:2] / f"{digest}.json"

    def _read_cache(self, path: Path) -> CachedResponse | None:
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return CachedResponse(data["status"], data["body"], data.get("etag"))

    def _write_cache(self, path: Path, url: str, params: dict | None, resp: CachedResponse) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({
            "url": url,
            "params": params,
            "status": resp.status,
            "etag": resp.etag,
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "body": resp.body,
        }))
        tmp.replace(path)

    # ---------------------------------------------------------------- network

    def _wait_for_reset(self, headers: requests.structures.CaseInsensitiveDict) -> None:
        reset = int(headers.get("X-RateLimit-Reset", time.time() + 60))
        delay = max(reset - time.time(), 0) + 2
        log.warning("Rate limit reached; sleeping %.0fs.", delay)
        time.sleep(delay)

    def _send(self, url: str, params: dict | None, accept: str, etag: str | None) -> requests.Response:
        headers = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if etag:
            headers["If-None-Match"] = etag

        for attempt in range(self.max_retries):
            self.network_calls += 1
            try:
                r = self.session.get(url, params=params, headers=headers, timeout=30)
            except requests.RequestException as exc:
                log.warning("Request error (%s); retrying.", exc)
                time.sleep(2 ** attempt)
                continue

            remaining = r.headers.get("X-RateLimit-Remaining")
            if r.status_code in (403, 429):
                if "Retry-After" in r.headers:  # secondary rate limit
                    time.sleep(int(r.headers["Retry-After"]) + 1)
                    continue
                if remaining == "0":
                    self._wait_for_reset(r.headers)
                    continue
                return r  # genuine permission error
            if r.status_code >= 500:
                time.sleep(2 ** attempt)
                continue

            # Pause before running dry rather than after.
            if remaining is not None and int(remaining) < self.min_remaining:
                self._wait_for_reset(r.headers)
            return r
        raise GitHubError(f"Giving up on {url} after {self.max_retries} attempts")

    # -------------------------------------------------------------- interface

    def get(
        self,
        path: str,
        params: dict | None = None,
        accept: str = JSON_ACCEPT,
        refresh: bool = False,
    ) -> CachedResponse:
        url = path if path.startswith("http") else f"{API_ROOT}/{path.lstrip('/')}"
        cache_path = self._cache_path(url, params, accept)
        cached = self._read_cache(cache_path)
        if cached and not refresh:
            return cached

        r = self._send(url, params, accept, cached.etag if cached else None)
        if r.status_code == 304 and cached:
            return cached
        resp = CachedResponse(r.status_code, r.text, r.headers.get("ETag"))
        if resp.ok or resp.status in (404, 451):  # cache "absent" answers too
            self._write_cache(cache_path, url, params, resp)
        else:
            raise GitHubError(f"{resp.status} for {url}: {resp.body[:200]}")
        return resp

    def get_json(self, path: str, params: dict | None = None, refresh: bool = False) -> Any | None:
        resp = self.get(path, params, refresh=refresh)
        return resp.json() if resp.ok else None

    def resolve_commit(self, repo: str, ref: str) -> str | None:
        """Return the full commit SHA for a branch, tag or short SHA."""
        data = self.get_json(f"repos/{repo}/commits/{ref}")
        return data["sha"] if data else None

    def get_file(self, repo: str, path: str, ref: str) -> str | None:
        """Return a file's text at ``ref`` (ideally a commit SHA), or None if absent."""
        resp = self.get(f"repos/{repo}/contents/{path}", {"ref": ref}, accept=RAW_ACCEPT)
        if not resp.ok:
            return None
        if resp.body.lstrip().startswith("[") and resp.body.rstrip().endswith("]"):
            try:  # path is a directory, not a file
                if isinstance(json.loads(resp.body), list):
                    return None
            except json.JSONDecodeError:
                pass
        return resp.body

    def list_dir(self, repo: str, path: str, ref: str) -> list[dict] | None:
        data = self.get_json(f"repos/{repo}/contents/{path}", {"ref": ref})
        return data if isinstance(data, list) else None

    def rate_limit(self) -> dict:
        r = self._send(f"{API_ROOT}/rate_limit", None, JSON_ACCEPT, None)
        return r.json()["resources"]["core"]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    core = GitHubClient().rate_limit()
    print(f"limit={core['limit']} remaining={core['remaining']} "
          f"resets={time.strftime('%H:%M:%S', time.localtime(core['reset']))}")

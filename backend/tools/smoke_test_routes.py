#!/usr/bin/env python3
"""Authenticated smoke tests for the Play Wave API.

The script uses only the Python standard library so it can run from the host
without installing backend dependencies.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


BASE_URL = os.getenv("PLAYWAVE_API_URL", "http://localhost:8000").rstrip("/")
ADMIN_EMAIL = os.getenv("PLAYWAVE_ADMIN_EMAIL", "admin@playwave.com")
ADMIN_PASSWORD = os.getenv("PLAYWAVE_ADMIN_PASSWORD")


@dataclass
class Result:
    name: str
    ok: bool
    status: int | None = None
    detail: str = ""


class API:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.token: str | None = None

    def set_token(self, token: str | None) -> None:
        self.token = token

    def request(
        self,
        method: str,
        path: str,
        body: Any = None,
        *,
        token: str | None = None,
        device_token: str | None = None,
        expected: tuple[int, ...] = (200,),
        accept_text: bool = False,
    ) -> Any:
        url = self.base_url + path
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        auth_token = token if token is not None else self.token
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        if device_token:
            headers["X-Device-Token"] = device_token

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                status = response.status
                raw = response.read()
                content_type = response.headers.get("content-type", "")
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read()
            content_type = exc.headers.get("content-type", "")

        if status not in expected:
            text = raw.decode("utf-8", "replace")[:600]
            raise AssertionError(f"{method} {path} -> HTTP {status}: {text}")

        if status == 204 or not raw:
            return None
        if accept_text or "application/json" not in content_type:
            return raw.decode("utf-8", "replace")
        return json.loads(raw.decode("utf-8"))


def record(results: list[Result], name: str, fn) -> Any:
    try:
        value = fn()
        results.append(Result(name=name, ok=True))
        return value
    except Exception as exc:  # noqa: BLE001 - smoke test should keep going
        results.append(Result(name=name, ok=False, detail=str(exc)))
        return None


def cleanup_smoke_artifacts(api: API) -> None:
    targets = [
        ("/audio/playlists", lambda item: (item.get("name") or "").startswith("Codex Smoke")),
        ("/audio/tracks", lambda item: (item.get("name") or "").startswith("Codex Smoke")),
        ("/campaigns", lambda item: (item.get("name") or "").startswith("Codex Smoke")),
        ("/devices", lambda item: (item.get("name") or "").startswith("Codex Smoke")),
        ("/locations", lambda item: (item.get("name") or "").startswith("Codex Smoke")),
        ("/media", lambda item: (item.get("name") or "").startswith("Codex Smoke")),
        ("/users", lambda item: (item.get("email") or "").startswith("codex.smoke.")),
    ]
    for collection_path, predicate in targets:
        try:
            items = api.request("GET", collection_path)
            for item in items:
                if predicate(item):
                    api.request("DELETE", f"{collection_path}/{item['id']}", expected=(200, 204, 404))
        except Exception:
            pass


def main() -> int:
    if not ADMIN_PASSWORD:
        print("Defina PLAYWAVE_ADMIN_PASSWORD com a senha do admin antes de rodar o smoke test.")
        return 2

    api = API(BASE_URL)
    results: list[Result] = []
    cleanup: list[tuple[str, str]] = []
    stamp = str(int(time.time()))
    prefix = f"Codex Smoke {stamp}"

    record(results, "health", lambda: api.request("GET", "/health"))
    record(
        results,
        "auth rejects missing bearer",
        lambda: api.request("GET", "/devices", expected=(401, 403)),
    )
    record(
        results,
        "auth rejects invalid login",
        lambda: api.request(
            "POST",
            "/api/auth/login",
            {"email": ADMIN_EMAIL, "password": "__wrong__"},
            expected=(401,),
        ),
    )

    login = record(
        results,
        "auth login admin",
        lambda: api.request(
            "POST",
            "/api/auth/login",
            {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        ),
    )
    if not login:
        print("Login admin falhou; abortando smoke test autenticado.")
        return 1

    api.set_token(login["access_token"])
    admin_user = login["user"]
    cleanup_smoke_artifacts(api)

    record(results, "auth me", lambda: api.request("GET", "/api/auth/me"))
    record(results, "auth logout", lambda: api.request("POST", "/api/auth/logout"))

    test_user_email = f"codex.smoke.{stamp}@playwave.com.br"
    test_user_password = "Teste@123456"
    test_user = record(
        results,
        "users create smoke login",
        lambda: api.request(
            "POST",
            "/users/",
            {
                "name": f"{prefix} User",
                "email": test_user_email,
                "password": test_user_password,
                "role": "operator",
                "is_active": True,
                "tenant_id": admin_user.get("tenant_id"),
            },
        ),
    )
    if test_user:
        cleanup.append(("DELETE", f"/users/{test_user['id']}"))
        operator_login = record(
            results,
            "auth login smoke user",
            lambda: api.request(
                "POST",
                "/api/auth/login",
                {"email": test_user_email, "password": test_user_password},
            ),
        )
        if operator_login:
            record(
                results,
                "auth me smoke user",
                lambda: api.request("GET", "/api/auth/me", token=operator_login["access_token"]),
            )

    media = record(
        results,
        "media create",
        lambda: api.request(
            "POST",
            "/media/",
            {
                "name": f"{prefix} Media",
                "description": "Temporary smoke media",
                "file_url": "https://example.com/smoke.mp4",
                "type": "external_url",
                "duration": 10,
                "tags": ["smoke"],
                "category": "smoke",
            },
        ),
    )
    if media:
        cleanup.append(("DELETE", f"/media/{media['id']}"))
        record(results, "media get", lambda: api.request("GET", f"/media/{media['id']}"))
        record(
            results,
            "media update",
            lambda: api.request("PUT", f"/media/{media['id']}", {"description": "Updated smoke media"}),
        )
        record(
            results,
            "media status",
            lambda: api.request("PATCH", f"/media/{media['id']}/status?status=available"),
        )

    location = record(
        results,
        "locations create",
        lambda: api.request(
            "POST",
            "/locations/",
            {
                "name": f"{prefix} Location",
                "description": "Temporary smoke location",
                "address": "Smoke Street",
            },
        ),
    )
    if location:
        cleanup.append(("DELETE", f"/locations/{location['id']}"))
        record(results, "locations get", lambda: api.request("GET", f"/locations/{location['id']}"))
        record(
            results,
            "locations update",
            lambda: api.request("PUT", f"/locations/{location['id']}", {"description": "Updated"}),
        )
        record(
            results,
            "locations devices",
            lambda: api.request("GET", f"/locations/{location['id']}/devices"),
        )

    device = record(
        results,
        "devices create",
        lambda: api.request(
            "POST",
            "/devices/",
            {
                "name": f"{prefix} Device",
                "pairing_code": f"SMOKE-{stamp}",
                "device_type": "tv",
                "location": location["name"] if location else "Smoke",
                "group": "smoke",
                "is_active": True,
            },
            expected=(200, 201),
        ),
    )
    if device:
        cleanup.append(("DELETE", f"/devices/{device['id']}"))
        record(results, "devices get", lambda: api.request("GET", f"/devices/{device['id']}"))
        record(
            results,
            "devices update",
            lambda: api.request("PUT", f"/devices/{device['id']}", {"status": "offline"}),
        )
        record(results, "devices metrics", lambda: api.request("GET", f"/devices/{device['id']}/metrics"))
        record(
            results,
            "devices heartbeat",
            lambda: api.request(
                "POST",
                f"/devices/{device['id']}/heartbeat",
                {"ip_address": "127.0.0.1", "player_version": "smoke"},
                device_token=device.get("device_token"),
            ),
        )

    campaign = None
    if media and device:
        campaign = record(
            results,
            "campaigns create",
            lambda: api.request(
                "POST",
                "/campaigns/",
                {
                    "name": f"{prefix} Campaign",
                    "description": "Temporary smoke campaign",
                    "status": "active",
                    "priority": 5,
                    "start_date": "2026-05-16",
                    "end_date": "2026-05-20",
                    "device_ids": [device["id"]],
                    "media_ids": [media["id"]],
                    "media_order": [{"media_id": media["id"], "duration": 10}],
                    "schedule_all_day": True,
                    "schedule_days": ["saturday"],
                },
            ),
        )
        if campaign:
            cleanup.append(("DELETE", f"/campaigns/{campaign['id']}"))
            record(results, "campaigns get", lambda: api.request("GET", f"/campaigns/{campaign['id']}"))
            record(
                results,
                "campaigns update",
                lambda: api.request("PUT", f"/campaigns/{campaign['id']}", {"priority": 4}),
            )
            record(results, "campaigns publish", lambda: api.request("POST", f"/campaigns/{campaign['id']}/publish"))
            record(results, "campaigns pause", lambda: api.request("POST", f"/campaigns/{campaign['id']}/pause"))
            record(results, "campaigns resume", lambda: api.request("POST", f"/campaigns/{campaign['id']}/resume"))
            record(results, "campaigns stats", lambda: api.request("GET", f"/campaigns/{campaign['id']}/stats"))
            record(
                results,
                "campaigns by device",
                lambda: api.request("GET", f"/campaigns/by-device/{device['id']}"),
            )
            record(
                results,
                "campaigns by media",
                lambda: api.request("GET", f"/campaigns/by-media/{media['id']}"),
            )
            record(
                results,
                "devices playlist",
                lambda: api.request(
                    "GET",
                    f"/devices/{device['id']}/playlist",
                    device_token=device.get("device_token"),
                ),
            )
            record(
                results,
                "reports register playback",
                lambda: api.request(
                    "POST",
                    "/reports/playback",
                    {
                        "device_id": device["id"],
                        "campaign_id": campaign["id"],
                        "media_id": media["id"],
                        "duration_ms": 1000,
                        "status": "completed",
                    },
                ),
            )

    track = record(
        results,
        "audio tracks create",
        lambda: api.request(
            "POST",
            "/audio/tracks/",
            {
                "name": f"{prefix} Track",
                "description": "Temporary smoke track",
                "file_url": "/uploads/audio/tracks/smoke.mp3",
                "mime_type": "audio/mpeg",
                "file_size": 1234,
                "duration_seconds": 30,
                "category": "music",
                "status": "active",
            },
        ),
    )
    if track:
        cleanup.append(("DELETE", f"/audio/tracks/{track['id']}"))
        record(results, "audio tracks get", lambda: api.request("GET", f"/audio/tracks/{track['id']}"))
        record(
            results,
            "audio tracks update",
            lambda: api.request("PUT", f"/audio/tracks/{track['id']}", {"description": "Updated"}),
        )
        record(
            results,
            "audio tracks by duration",
            lambda: api.request("GET", "/audio/tracks/by-duration?min_seconds=1&max_seconds=120"),
        )

    playlist = None
    if track:
        playlist = record(
            results,
            "audio playlists create",
            lambda: api.request(
                "POST",
                "/audio/playlists/",
                {
                    "name": f"{prefix} Playlist",
                    "description": "Temporary smoke playlist",
                    "status": "active",
                    "volume_default": 0.7,
                    "track_ids": [track["id"]],
                    "track_volumes": {track["id"]: 0.8},
                },
            ),
        )
        if playlist:
            cleanup.append(("DELETE", f"/audio/playlists/{playlist['id']}"))
            record(results, "audio playlists get", lambda: api.request("GET", f"/audio/playlists/{playlist['id']}"))
            record(
                results,
                "audio playlists with tracks",
                lambda: api.request("GET", f"/audio/playlists/{playlist['id']}/with-tracks"),
            )
            record(
                results,
                "audio playlists reorder",
                lambda: api.request("PUT", f"/audio/playlists/{playlist['id']}/tracks/reorder", [track["id"]]),
            )
            if device:
                record(
                    results,
                    "devices attach audio playlist",
                    lambda: api.request("PUT", f"/devices/{device['id']}", {"audio_playlist_id": playlist["id"]}),
                )
                record(
                    results,
                    "audio playlists by device",
                    lambda: api.request("GET", f"/audio/playlists/by-device/{device['id']}"),
                )

    collection_paths = [
        "/dashboard/stats",
        "/devices",
        "/devices/statistics/overview",
        "/devices/online/list",
        "/devices/offline/list",
        "/devices/pairing/waiting",
        "/media",
        "/media/statistics/overview",
        "/media/available/list",
        "/media/processing/list",
        "/media/error/list",
        "/campaigns",
        "/campaigns/statistics/overview",
        "/campaigns/active/list",
        "/campaigns/scheduled/list",
        "/schedule",
        "/schedule/upcoming",
        "/schedule/active",
        "/monitoring/devices",
        "/monitoring/stats",
        "/monitoring/events",
        "/reports/playback",
        "/reports/playback/stats",
        "/reports/summary",
        "/reports/views",
        "/reports/views/stats",
        "/locations",
        "/locations/statistics/overview",
        "/plans",
        "/tenants",
        "/tenants/me",
        "/users",
        "/users/statistics/overview",
        "/users/active/list",
        "/audio/tracks",
        "/audio/tracks/statistics/overview",
        "/audio/tracks/active/list",
        "/audio/playlists",
        "/audio/playlists/statistics/overview",
        "/audio/playlists/active/list",
        "/user-logs",
        "/user-logs/statistics/overview",
        "/user-logs/recent",
    ]
    for path in collection_paths:
        record(results, f"GET {path}", lambda p=path: api.request("GET", p))

    if device:
        record(results, "GET /reports/device/{id}", lambda: api.request("GET", f"/reports/device/{device['id']}"))
        record(results, "GET /monitoring/events/{id}", lambda: api.request("GET", f"/monitoring/events/{device['id']}"))
    if campaign:
        record(results, "GET /reports/campaign/{id}", lambda: api.request("GET", f"/reports/campaign/{campaign['id']}"))
    record(
        results,
        "GET /reports/export/csv",
        lambda: api.request("GET", "/reports/export/csv", accept_text=True),
    )

    for method, path in reversed(cleanup):
        record(results, f"cleanup {path}", lambda m=method, p=path: api.request(m, p, expected=(200, 204, 404)))

    passed = sum(1 for item in results if item.ok)
    failed = [item for item in results if not item.ok]

    print(f"Base URL: {BASE_URL}")
    print(f"Admin login: {ADMIN_EMAIL}")
    print(f"Resultado: {passed}/{len(results)} checks passaram")
    for item in results:
        marker = "OK " if item.ok else "FAIL"
        suffix = f" - {item.detail}" if item.detail else ""
        print(f"{marker} {item.name}{suffix}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import os
from collections.abc import Mapping


PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
)


def proxy_env_map(env: Mapping[str, str] | None = None) -> dict[str, str]:
    source = os.environ if env is None else env
    return {
        key: str(value)
        for key, value in source.items()
        if key in PROXY_ENV_KEYS and str(value).strip()
    }


__all__ = ["PROXY_ENV_KEYS", "proxy_env_map"]

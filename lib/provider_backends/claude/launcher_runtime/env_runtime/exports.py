from __future__ import annotations

from provider_profiles import provider_api_env_keys
from provider_profiles.env_refs import shell_env_assignment
from runtime_env.proxy import proxy_env_map


_CLAUDE_AUTH_ENV_KEYS = {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"}


def build_claude_env_prefix(
    *,
    profile=None,
    extra_env: dict[str, str] | None = None,
    env: dict[str, str] | None = None,
    should_drop_base_url_fn,
    claude_user_base_url_fn,
) -> str:
    api_keys = provider_api_env_keys("claude")
    merged_env = collect_inherited_env(profile=profile, env=env or {})
    merged_env.update(collect_explicit_env(profile=profile, extra_env=extra_env))
    parts = unset_api_env_parts(profile=profile, api_keys=api_keys)

    merged_env = reconcile_base_url(
        merged_env,
        profile=profile,
        env=env or {},
        parts=parts,
        should_drop_base_url_fn=should_drop_base_url_fn,
        claude_user_base_url_fn=claude_user_base_url_fn,
    )

    export_statement = render_export_statement(merged_env)
    if export_statement:
        parts.append(export_statement)
    return "; ".join(parts)


def collect_explicit_env(*, profile=None, extra_env: dict[str, str] | None) -> dict[str, str]:
    explicit_env: dict[str, str] = {}
    if profile is not None:
        explicit_env.update(dict(profile.env))
    if extra_env:
        explicit_env.update(dict(extra_env))
    return explicit_env


def collect_inherited_env(*, profile=None, env: dict[str, str]) -> dict[str, str]:
    inherited = proxy_env_map(env)
    if profile is not None and not profile.inherit_auth:
        return inherited
    for key in sorted(_CLAUDE_AUTH_ENV_KEYS):
        value = str(env.get(key) or "").strip()
        if value:
            inherited[key] = value
    return inherited


def unset_api_env_parts(*, profile=None, api_keys: set[str]) -> list[str]:
    if profile is None:
        return []
    if not profile.inherit_api:
        return [f"unset {key}" for key in sorted(api_keys)]
    if not profile.inherit_auth:
        return [f"unset {key}" for key in sorted(_CLAUDE_AUTH_ENV_KEYS)]
    return []


def reconcile_base_url(
    explicit_env: dict[str, str],
    *,
    profile=None,
    env: dict[str, str],
    parts: list[str],
    should_drop_base_url_fn,
    claude_user_base_url_fn,
) -> dict[str, str]:
    base_url = explicit_env.get("ANTHROPIC_BASE_URL")
    if base_url:
        if should_drop_base_url_fn(base_url):
            explicit_env.pop("ANTHROPIC_BASE_URL", None)
            ensure_unset(parts, "ANTHROPIC_BASE_URL")
        return explicit_env

    if profile is not None and not profile.inherit_api:
        return explicit_env

    inherited_base_url = inherited_base_url_value(env=env, claude_user_base_url_fn=claude_user_base_url_fn)
    if not inherited_base_url:
        return explicit_env
    if should_drop_base_url_fn(inherited_base_url):
        ensure_unset(parts, "ANTHROPIC_BASE_URL")
        return explicit_env
    explicit_env["ANTHROPIC_BASE_URL"] = inherited_base_url
    return explicit_env


def inherited_base_url_value(*, env: dict[str, str], claude_user_base_url_fn) -> str:
    env_base_url = str(env.get("ANTHROPIC_BASE_URL") or "").strip()
    if env_base_url:
        return env_base_url
    return str(claude_user_base_url_fn() or "").strip()


def ensure_unset(parts: list[str], key: str) -> None:
    statement = f"unset {key}"
    if statement not in parts:
        parts.append(statement)


def render_export_statement(explicit_env: dict[str, str]) -> str:
    exports = " ".join(
        shell_env_assignment(key, value)
        for key, value in sorted(explicit_env.items())
        if str(value).strip()
    )
    if not exports:
        return ""
    return f"export {exports}"


__all__ = ["build_claude_env_prefix"]

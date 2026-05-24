from __future__ import annotations

import re
import shlex


_ENV_REF_RE = re.compile(r'^\$(?:\{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)\}|(?P<plain>[A-Za-z_][A-Za-z0-9_]*))$')


def env_ref_name(value: object) -> str | None:
    text = str(value or '').strip()
    match = _ENV_REF_RE.fullmatch(text)
    if match is None:
        return None
    return match.group('braced') or match.group('plain')


def shell_env_assignment(key: str, value: object) -> str:
    name = env_ref_name(value)
    if name is not None:
        return f'{key}="${{{name}}}"'
    return f'{key}={shlex.quote(str(value))}'


__all__ = ['env_ref_name', 'shell_env_assignment']

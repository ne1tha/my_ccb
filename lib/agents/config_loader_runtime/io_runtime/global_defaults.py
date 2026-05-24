from __future__ import annotations

from pathlib import Path

from agents.models import ProjectConfig

from ..defaults import build_default_project_config
from ..defaults_runtime.rendering_runtime.serialization import agent_spec_to_config_dict
from ..parsing import validate_project_config
from .documents import _load_config_document


_GLOBAL_PROVIDER_DEFAULT_KEYS = {'key', 'url', 'model'}


def user_default_config_path() -> Path:
    return Path.home() / '.ccb' / 'ccb.config'


def load_user_default_project_config() -> ProjectConfig | None:
    path = user_default_config_path()
    if not path.is_file():
        return None
    document = _load_config_document(path)
    if _is_provider_defaults_document(document):
        document = _default_project_document_with_provider_defaults(document)
    return validate_project_config(document, source_path=path)


def bootstrap_default_project_config() -> ProjectConfig:
    return load_user_default_project_config() or build_default_project_config()


def _is_provider_defaults_document(document: dict[str, object]) -> bool:
    keys = set(document)
    return bool(keys) and keys <= _GLOBAL_PROVIDER_DEFAULT_KEYS


def _default_project_document_with_provider_defaults(document: dict[str, object]) -> dict[str, object]:
    config = build_default_project_config()
    payload: dict[str, object] = {
        'version': config.version,
        'default_agents': list(config.default_agents),
        'agents': {
            name: agent_spec_to_config_dict(config.agents[name])
            for name in config.default_agents
        },
        'cmd_enabled': config.cmd_enabled,
        'layout': config.layout_spec,
    }
    for key in ('key', 'url', 'model'):
        if document.get(key) is not None:
            payload[key] = document[key]
    return payload


__all__ = ['bootstrap_default_project_config', 'load_user_default_project_config', 'user_default_config_path']

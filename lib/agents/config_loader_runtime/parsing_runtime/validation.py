from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.models import AgentValidationError, ProjectConfig, normalize_agent_name
from provider_model_shortcuts import startup_args_contain_model_flag, supported_provider_model_shortcuts
from provider_profiles import provider_api_env_keys, supported_provider_api_shortcuts

from ..common import ALLOWED_TOP_LEVEL_KEYS, ConfigValidationError
from .agent_specs import parse_agents
from .expectations import expect_bool, expect_mapping, expect_string, expect_string_list


def validate_project_config(document: dict[str, Any], *, source_path: Path | None = None) -> ProjectConfig:
    _validate_document_shape(document)
    expanded_document = _apply_top_level_agent_defaults(document)
    default_agents = _parse_default_agents(expanded_document)
    parsed_agents = parse_agents(expanded_document.get('agents'))
    cmd_enabled = _parse_cmd_enabled(expanded_document)
    layout_spec = _parse_layout_spec(expanded_document)
    return _build_project_config(
        default_agents=default_agents,
        parsed_agents=parsed_agents,
        cmd_enabled=cmd_enabled,
        layout_spec=layout_spec,
        source_path=source_path,
    )


def _validate_document_shape(document: dict[str, Any]) -> None:
    unknown_top = sorted(set(document) - ALLOWED_TOP_LEVEL_KEYS)
    if unknown_top:
        raise ConfigValidationError(
            f'config contains unknown top-level fields: {", ".join(unknown_top)}'
        )
    if document.get('version') != 2:
        raise ConfigValidationError('version must be 2')


def _apply_top_level_agent_defaults(document: dict[str, Any]) -> dict[str, Any]:
    api_defaults = {
        key: expect_string(document[key], field_name=key)
        for key in ('key', 'url')
        if document.get(key) is not None
    }
    model_default = (
        expect_string(document['model'], field_name='model')
        if document.get('model') is not None
        else None
    )
    if not api_defaults and model_default is None:
        return dict(document)

    raw_agents = expect_mapping(document.get('agents'), field_name='agents')
    expanded_agents: dict[str, object] = {}
    for raw_name, raw_spec in raw_agents.items():
        if not isinstance(raw_name, str):
            raise ConfigValidationError('agents table keys must be strings')
        field_prefix = f'agents.{raw_name}'
        agent_payload = dict(expect_mapping(raw_spec, field_name=field_prefix))
        provider = expect_string(agent_payload.get('provider'), field_name=f'{field_prefix}.provider')

        if api_defaults and _agent_accepts_top_level_api_default(agent_payload, provider=provider):
            for key, value in api_defaults.items():
                agent_payload[key] = value
        if model_default is not None and _agent_accepts_top_level_model_default(agent_payload, provider=provider):
            agent_payload['model'] = model_default
        expanded_agents[raw_name] = agent_payload

    expanded = {
        key: value
        for key, value in dict(document).items()
        if key not in {'key', 'url', 'model'}
    }
    expanded['agents'] = expanded_agents
    return expanded


def _agent_accepts_top_level_api_default(raw_agent: dict[str, Any], *, provider: str) -> bool:
    normalized_provider = str(provider or '').strip().lower()
    if normalized_provider not in supported_provider_api_shortcuts():
        return False
    if any(raw_agent.get(field) is not None for field in ('key', 'url', 'api')):
        return False
    api_env_keys = provider_api_env_keys(normalized_provider)
    if _env_contains_any(raw_agent.get('env'), api_env_keys):
        return False
    raw_profile = raw_agent.get('provider_profile')
    if raw_profile is None:
        return True
    profile = expect_mapping(raw_profile, field_name='provider_profile')
    if _env_contains_any(profile.get('env'), api_env_keys):
        return False
    if profile.get('inherit_api') is True:
        return False
    if profile.get('inherit_auth') is True:
        return False
    if normalized_provider == 'codex' and profile.get('inherit_config') is True:
        return False
    return True


def _agent_accepts_top_level_model_default(raw_agent: dict[str, Any], *, provider: str) -> bool:
    normalized_provider = str(provider or '').strip().lower()
    if normalized_provider not in supported_provider_model_shortcuts():
        return False
    if raw_agent.get('model') is not None:
        return False
    startup_args = raw_agent.get('startup_args') or ()
    if isinstance(startup_args, (list, tuple)) and startup_args_contain_model_flag(
        normalized_provider,
        tuple(str(item) for item in startup_args),
    ):
        return False
    return True


def _env_contains_any(raw_env: Any, keys: set[str]) -> bool:
    if raw_env is None:
        return False
    env = expect_mapping(raw_env, field_name='env')
    return bool(set(env) & set(keys))


def _parse_default_agents(document: dict[str, Any]) -> tuple[str, ...]:
    raw_default_agents = document.get('default_agents')
    if raw_default_agents is None:
        raise ConfigValidationError('default_agents is required')
    try:
        return tuple(
            normalize_agent_name(item)
            for item in expect_string_list(raw_default_agents, field_name='default_agents')
        )
    except AgentValidationError as exc:
        raise ConfigValidationError(str(exc)) from exc


def _parse_cmd_enabled(document: dict[str, Any]) -> bool:
    if 'cmd_enabled' not in document:
        return False
    return expect_bool(document['cmd_enabled'], field_name='cmd_enabled')


def _parse_layout_spec(document: dict[str, Any]) -> str | None:
    if document.get('layout') is None:
        return None
    return expect_string(document['layout'], field_name='layout')


def _build_project_config(
    *,
    default_agents: tuple[str, ...],
    parsed_agents,
    cmd_enabled: bool,
    layout_spec: str | None,
    source_path: Path | None,
) -> ProjectConfig:
    try:
        return ProjectConfig(
            version=2,
            default_agents=default_agents,
            agents=parsed_agents,
            cmd_enabled=cmd_enabled,
            layout_spec=layout_spec,
            source_path=str(source_path) if source_path else None,
        )
    except AgentValidationError as exc:
        raise ConfigValidationError(str(exc)) from exc


__all__ = ['validate_project_config']

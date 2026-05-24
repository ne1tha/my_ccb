from __future__ import annotations

from runtime_env.control_plane import control_plane_env


def test_control_plane_env_keeps_provider_api_env(monkeypatch) -> None:
    monkeypatch.setenv('OPENAI_API_KEY', 'openai-key')
    monkeypatch.setenv('OPENAI_BASE_URL', 'https://api.example.test/v1')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'anthropic-key')
    monkeypatch.setenv('GEMINI_API_KEY', 'gemini-key')
    monkeypatch.setenv('MY_APIKEY', 'shared-provider-key')

    env = control_plane_env()

    assert env['OPENAI_API_KEY'] == 'openai-key'
    assert env['OPENAI_BASE_URL'] == 'https://api.example.test/v1'
    assert env['ANTHROPIC_API_KEY'] == 'anthropic-key'
    assert env['GEMINI_API_KEY'] == 'gemini-key'
    assert env['MY_APIKEY'] == 'shared-provider-key'


def test_control_plane_env_keeps_proxy_env(monkeypatch) -> None:
    monkeypatch.setenv('HTTP_PROXY', 'http://127.0.0.1:17890')
    monkeypatch.setenv('HTTPS_PROXY', 'http://127.0.0.1:17890')
    monkeypatch.setenv('ALL_PROXY', 'socks5://127.0.0.1:17891')
    monkeypatch.setenv('NO_PROXY', 'localhost,127.0.0.1,::1')
    monkeypatch.setenv('http_proxy', 'http://127.0.0.1:17890')
    monkeypatch.setenv('https_proxy', 'http://127.0.0.1:17890')
    monkeypatch.setenv('all_proxy', 'socks5://127.0.0.1:17891')
    monkeypatch.setenv('no_proxy', 'localhost,127.0.0.1,::1')

    env = control_plane_env()

    assert env['HTTP_PROXY'] == 'http://127.0.0.1:17890'
    assert env['HTTPS_PROXY'] == 'http://127.0.0.1:17890'
    assert env['ALL_PROXY'] == 'socks5://127.0.0.1:17891'
    assert env['NO_PROXY'] == 'localhost,127.0.0.1,::1'
    assert env['http_proxy'] == 'http://127.0.0.1:17890'
    assert env['https_proxy'] == 'http://127.0.0.1:17890'
    assert env['all_proxy'] == 'socks5://127.0.0.1:17891'
    assert env['no_proxy'] == 'localhost,127.0.0.1,::1'


def test_control_plane_env_keeps_user_session_transport_for_cmd_shell(monkeypatch) -> None:
    monkeypatch.setenv('DISPLAY', ':0')
    monkeypatch.setenv('WAYLAND_DISPLAY', 'wayland-0')
    monkeypatch.setenv('DBUS_SESSION_BUS_ADDRESS', 'unix:path=/run/user/1000/bus')
    monkeypatch.setenv('XAUTHORITY', '/tmp/.Xauthority')
    monkeypatch.setenv('SSH_AUTH_SOCK', '/tmp/ssh-agent.sock')

    env = control_plane_env()

    assert env['DISPLAY'] == ':0'
    assert env['WAYLAND_DISPLAY'] == 'wayland-0'
    assert env['DBUS_SESSION_BUS_ADDRESS'] == 'unix:path=/run/user/1000/bus'
    assert env['XAUTHORITY'] == '/tmp/.Xauthority'
    assert env['SSH_AUTH_SOCK'] == '/tmp/ssh-agent.sock'

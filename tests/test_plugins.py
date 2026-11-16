from pathlib import Path

from plugins.plugin_manager import PluginManager


def test_bundled_plugins_have_usable_state():
    plugins_dir = Path(__file__).resolve().parents[1] / "plugins"
    manager = PluginManager(str(plugins_dir))
    plugins = manager.get_all_plugins()
    assert plugins, "expected the bundled example plugins to load"
    assert all(isinstance(plugin.enabled, bool) for plugin in plugins)
    assert manager.get_enabled_plugins() == plugins


def test_plugin_install_from_url_does_not_claim_success(tmp_path):
    manager = PluginManager(str(tmp_path))
    assert manager.install_plugin_from_url("https://example.invalid/plugin.py") is False
    assert list(tmp_path.glob("*.py")) == []

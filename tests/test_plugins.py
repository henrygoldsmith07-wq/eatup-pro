from plugins.plugin_manager import PluginManager


def test_plugin_install_from_url_does_not_claim_success(tmp_path):
    manager = PluginManager(str(tmp_path))
    assert manager.install_plugin_from_url("https://example.invalid/plugin.py") is False
    assert list(tmp_path.glob("*.py")) == []

from numpy import where
from fixlib.config import Config
from fix_plugin_nutanix import NutanixCollectorPlugin


def test_config():
    config = Config("dummy", "dummy")
    NutanixCollectorPlugin.add_config(config)
    Config.init_default_config()
    assert Config.nutanix.credentials == []

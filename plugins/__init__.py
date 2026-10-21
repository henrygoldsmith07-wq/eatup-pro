"""
EatUp Pro - Plugin System Package
"""

from .base_plugin import (BasePlugin, PluginMetadata, ScanExtensionPlugin, CleanupPlugin,
                          AnalyticsPlugin, NotificationPlugin, PluginRegistry)
from .plugin_manager import PluginManager

__all__ = [
    'BasePlugin',
    'PluginMetadata', 
    'ScanExtensionPlugin',
    'CleanupPlugin',
    'AnalyticsPlugin',
    'NotificationPlugin',
    'PluginManager',
    'PluginRegistry'
]

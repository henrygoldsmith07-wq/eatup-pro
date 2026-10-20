"""
EatUp Pro - Plugin System Package
"""

from .base_plugin import BasePlugin, PluginMetadata, ScanExtensionPlugin
from .plugin_manager import PluginManager, PluginRegistry

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

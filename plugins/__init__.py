"""
EatUp Pro - Plugin System Package
"""

from .base_plugin import BasePlugin, PluginMetadata, ScanExtensionPlugin
from .plugin_manager import PluginManager, PluginRegistry

# Import example plugins
try:
    from .game_cache_cleaner import GameCacheCleanerPlugin
except ImportError:
    pass

try:
    from .duplicate_photos import DuplicatePhotosPlugin
except ImportError:
    pass

__all__ = [
    'BasePlugin',
    'PluginMetadata', 
    'ScanExtensionPlugin',
    'CleanupPlugin',
    'AnalyticsPlugin',
    'NotificationPlugin',
    'GameCacheCleanerPlugin',
    'DuplicatePhotosPlugin',
    'PluginManager',
    'PluginRegistry'
]


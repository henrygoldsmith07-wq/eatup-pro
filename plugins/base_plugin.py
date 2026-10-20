"""
EatUp Pro - Base Plugin Class
All plugins must inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PluginMetadata:
    """Plugin metadata information"""
    name: str
    version: str
    author: str
    description: str
    capabilities: List[str]
    min_version: str = "1.0.0"
    max_version: str = "99.99.99"


class BasePlugin(ABC):
    """Base class for all EatUp Pro plugins"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.plugin_id = None
        self.enabled = True
        
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass
    
    @abstractmethod
    def customize_scan(self, scanner) -> List[str]:
        """Add custom scan rules or extensions"""
        pass
    
    @abstractmethod
    def customize_cleanup(self, cleaner) -> List[str]:
        """Add custom cleanup operations"""
        pass
    
    def post_scan_analysis(self, results) -> Dict[str, Any]:
        """Analyze scan results for insights (optional override)"""
        return {}
    
    def pre_cleanup_validation(self, files_to_delete: List[Dict]) -> bool:
        """Validate files before deletion (returns True if safe)"""
        return True
    
    def get_recommendations(self, scan_results) -> List[Dict[str, Any]]:
        """Generate cleanup recommendations"""
        return []
    
    def on_file_deleted(self, filepath: str, freed_bytes: int):
        """Called when file is deleted (for logging/plugins)"""
        pass
    
    def on_error(self, error: Exception, context: str):
        """Handle errors that occur during scanning/cleanup"""
        print(f"[{self.metadata.name}] Error: {error}")
    
    def validate_config(self) -> bool:
        """Validate plugin configuration"""
        return True
    
    def configure(self, config: Dict[str, Any]):
        """Configure plugin with user settings"""
        self.config.update(config)
    
    def export_data(self) -> Dict[str, Any]:
        """Export plugin data for backup"""
        return {
            'config': self.config,
            'metadata': {
                'name': self.metadata.name,
                'version': self.metadata.version
            }
        }
    
    def import_data(self, data: Dict[str, Any]):
        """Import plugin data from backup"""
        if 'config' in data:
            self.config.update(data['config'])
    
    def get_status(self) -> Dict[str, Any]:
        """Get current plugin status"""
        return {
            'enabled': self.enabled,
            'configured': self.validate_config(),
            'last_used': None
        }


class ScanExtensionPlugin(BasePlugin):
    """Plugin that extends scanning capabilities"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Scan Extension",
            version="1.0.0",
            author="EatUp Team",
            description="Adds custom file type detection",
            capabilities=['scan_extension']
        )
    
    def customize_scan(self, scanner) -> List[str]:
        # Add custom file patterns
        scanner.custom_extensions.extend(['.custom', '.plugin'])
        return ['custom_scan_rules']
    
    def customize_cleanup(self, cleaner) -> List[str]:
        return []


class CleanupPlugin(BasePlugin):
    """Plugin that adds custom cleanup operations"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Cleanup Plugin",
            version="1.0.0",
            author="EatUp Team",
            description="Custom cleanup algorithms",
            capabilities=['cleanup_operation']
        )
    
    def customize_cleanup(self, cleaner) -> List[str]:
        cleaner.add_custom_cleanup('my_special_cleanup')
        return ['special_cleanup']
    
    def customize_scan(self, scanner) -> List[str]:
        return []


class AnalyticsPlugin(BasePlugin):
    """Plugin that provides analytics insights"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Analytics Plugin",
            version="1.0.0",
            author="EatUp Team",
            description="Additional analytics features",
            capabilities=['analytics']
        )
    
    def post_scan_analysis(self, results) -> Dict[str, Any]:
        return {
            'custom_metrics': [],
            'insights': []
        }
    
    def customize_scan(self, scanner) -> List[str]:
        return []
    
    def customize_cleanup(self, cleaner) -> List[str]:
        return []


class NotificationPlugin(BasePlugin):
    """Plugin that sends notifications on events"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Notification Plugin",
            version="1.0.0",
            author="EatUp Team",
            description="Send alerts and notifications",
            capabilities=['notifications']
        )
    
    def on_file_deleted(self, filepath: str, freed_bytes: int):
        # Send notification
        print(f"File deleted: {filepath} freed {freed_bytes} bytes")
    
    def customize_scan(self, scanner) -> List[str]:
        return []
    
    def customize_cleanup(self, cleaner) -> List[str]:
        return []


# Plugin Registry System
class PluginRegistry:
    """Registry for managing plugins"""
    
    def __init__(self):
        self.plugins = {}
        self.available_plugins = []
        
    def register_plugin(self, plugin_instance: BasePlugin):
        """Register a new plugin"""
        plugin_instance.plugin_id = f"{plugin_instance.metadata.name.lower().replace(' ', '_')}_{plugin_instance.metadata.version}"
        self.plugins[plugin_instance.plugin_id] = plugin_instance
        self.available_plugins.append(plugin_instance.metadata.name)
        print(f"Registered plugin: {plugin_instance.metadata.name}")
    
    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """Get plugin by ID"""
        return self.plugins.get(plugin_id)
    
    def get_all_enabled(self) -> List[BasePlugin]:
        """Get all enabled plugins"""
        return [p for p in self.plugins.values() if p.enabled]
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin"""
        if plugin_id in self.plugins:
            self.plugins[plugin_id].enabled = True
            return True
        return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin"""
        if plugin_id in self.plugins:
            self.plugins[plugin_id].enabled = False
            return True
        return False
    
    def load_plugins(self) -> bool:
        """Load all installed plugins"""
        # Load built-in plugins
        self.register_plugin(ScanExtensionPlugin())
        self.register_plugin(CleanupPlugin())
        self.register_plugin(AnalyticsPlugin())
        self.register_plugin(NotificationPlugin())
        
        return True


def create_plugin(name: str, **kwargs) -> BasePlugin:
    """Factory function to create plugins"""
    if name == "scan_extension":
        return ScanExtensionPlugin(kwargs)
    elif name == "cleanup_plugin":
        return CleanupPlugin(kwargs)
    elif name == "analytics":
        return AnalyticsPlugin(kwargs)
    elif name == "notifications":
        return NotificationPlugin(kwargs)
    else:
        raise ValueError(f"Unknown plugin type: {name}")

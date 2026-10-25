#!/usr/bin/env python3
"""
EatUp Pro - Plugin System Manager
Manages plugin loading, configuration, and execution
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import List, Dict, Any
from .base_plugin import BasePlugin, PluginRegistry


class PluginManager:
    """Manages all plugins in EatUp Pro"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.registry = PluginRegistry()
        self.load_plugins()
    
    def load_plugins(self):
        """Load all installed plugins"""
        # Create plugins directory if it doesn't exist
        self.plugins_dir.mkdir(exist_ok=True)
        
        # Load built-in plugins
        self.registry.load_plugins()
        
        # Load custom plugins from directory
        self._load_custom_plugins()
    
    def _load_custom_plugins(self):
        """Load user-installed plugins"""
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith('_'):
                continue
            
            try:
                spec = importlib.util.spec_from_file_location(
                    plugin_file.stem, 
                    plugin_file
                )
                module = importlib.util.module_from_spec(spec)
                
                # Execute the module
                spec.loader.exec_module(module)
                
                # Find and register plugin classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BasePlugin) and 
                        attr != BasePlugin):
                        
                        instance = attr()
                        self.registry.register_plugin(instance)
                        
            except Exception as e:
                print(f"Error loading plugin {plugin_file.name}: {e}")
    
    def get_all_plugins(self) -> List[BasePlugin]:
        """Get all available plugins"""
        return list(self.registry.plugins.values())
    
    def get_enabled_plugins(self) -> List[BasePlugin]:
        """Get only enabled plugins"""
        return [p for p in self.get_all_plugins() if p.enabled]
    
    def find_plugin_by_capability(self, capability: str) -> List[BasePlugin]:
        """Find plugins that support a specific capability"""
        return [
            p for p in self.get_all_plugins()
            if capability in p.metadata.capabilities
        ]
    
    def run_scan_extensions(self, scanner) -> bool:
        """Run all scan extension plugins"""
        enabled_plugins = self.get_enabled_plugins()
        
        success = True
        for plugin in enabled_plugins:
            try:
                rules = plugin.customize_scan(scanner)
                print(f"[{plugin.metadata.name}] Applied {len(rules)} scan rules")
            except Exception as e:
                plugin.on_error(e, "scan_extension")
                success = False
        
        return success
    
    def run_cleanup_plugins(self, cleaner) -> bool:
        """Run all cleanup operation plugins"""
        enabled_plugins = self.get_enabled_plugins()
        
        success = True
        for plugin in enabled_plugins:
            try:
                operations = plugin.customize_cleanup(cleaner)
                print(f"[{plugin.metadata.name}] Added {len(operations)} cleanup operations")
            except Exception as e:
                plugin.on_error(e, "cleanup_operation")
                success = False
        
        return success
    
    def analyze_scan_results(self, results) -> Dict[str, Any]:
        """Run analytics plugins on scan results"""
        insights = {}
        
        for plugin in self.get_enabled_plugins():
            try:
                analysis = plugin.post_scan_analysis(results)
                insights.update(analysis)
            except Exception as e:
                plugin.on_error(e, "post_scan_analysis")
        
        return insights
    
    def generate_recommendations(self, scan_results) -> List[Dict[str, Any]]:
        """Generate recommendations from all plugins"""
        recommendations = []
        
        for plugin in self.get_enabled_plugins():
            try:
                recs = plugin.get_recommendations(scan_results)
                recommendations.extend(recs)
            except Exception as e:
                plugin.on_error(e, "recommendations")
        
        # Sort by confidence
        recommendations.sort(key=lambda r: r.get('confidence', 0), reverse=True)
        
        return recommendations[:10]  # Top 10 recommendations
    
    def install_plugin_from_url(self, url: str) -> bool:
        """Install plugin from URL (placeholder)"""
        print(f"Would download plugin from: {url}")
        return True
    
    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin"""
        if plugin_id in self.registry.plugins:
            del self.registry.plugins[plugin_id]
            print(f"Uninstalled plugin: {plugin_id}")
            return True
        return False
    
    def update_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """Update plugin configuration"""
        if plugin_id in self.registry.plugins:
            self.registry.plugins[plugin_id].configure(config)
            return True
        return False


# Example usage
def main():
    """Test plugin system"""
    manager = PluginManager()
    
    print("=" * 70)
    print("EATUP PRO - PLUGIN SYSTEM MANAGER")
    print("=" * 70)
    
    print(f"\nTotal plugins registered: {len(manager.get_all_plugins())}")
    print(f"Enabled plugins: {len(manager.get_enabled_plugins())}")
    
    print("\nAvailable Plugins:")
    for plugin in manager.get_all_plugins():
        status = "✓" if plugin.enabled else "✗"
        print(f"  [{status}] {plugin.metadata.name} v{plugin.metadata.version}")
    
    print("\nCapabilities:")
    capabilities = set()
    for plugin in manager.get_all_plugins():
        capabilities.update(plugin.metadata.capabilities)
    
    for cap in sorted(capabilities):
        plugins_with_cap = [
            p.metadata.name for p in manager.get_all_plugins()
            if cap in p.metadata.capabilities
        ]
        print(f"  • {cap}: {', '.join(plugins_with_cap)}")


if __name__ == "__main__":
    main()

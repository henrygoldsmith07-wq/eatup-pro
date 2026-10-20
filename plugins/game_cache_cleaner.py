"""
Example Plugin 1: Game Cache Cleaner
Finds and cleans game cache files from Steam, Epic Games, etc.
"""

import os
from pathlib import Path
from datetime import datetime
from plugins.base_plugin import BasePlugin


class GameCacheCleanerPlugin(BasePlugin):
    """Plugin to clean game cache files"""
    
    def __init__(self):
        self.name = "Game Cache Cleaner"
        self.description = "Cleans temporary cache files from popular game platforms"
        self.version = "1.0.0"
        
        # Common game cache locations
        self.cache_patterns = [
            'steam', 'epicgames', 'ubisoft', 'ea', 'bethesda', 'blizzard'
        ]
        
        # File extensions commonly used for game cache
        self.cache_extensions = {'.cache', '.tmp', '.log', '.bak'}
    
    def get_metadata(self):
        """Return plugin metadata"""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': 'EatUp Pro Team',
            'capabilities': ['scan', 'cleanup']
        }
    
    def customize_scan(self, scanner) -> list[str]:
        """Extend scan to detect game cache directories"""
        detected_paths = []
        
        try:
            user_profile = os.environ.get('LOCALAPPDATA', 'C:/Users')
            
            for cache_pattern in self.cache_patterns:
                search_path = os.path.join(user_profile, cache_pattern)
                if os.path.exists(search_path):
                    detected_paths.append(search_path)
                    scanner.custom_paths.append(search_path)
                    
        except Exception as e:
            print(f"[GameCachePlugin] Error scanning game paths: {e}")
        
        return detected_paths
    
    def customize_cleanup(self, cleaner) -> list[str]:
        """Add game-specific cleanup rules"""
        cleaned_files = []
        
        try:
            user_profile = os.environ.get('LOCALAPPDATA', 'C:/Users')
            
            for root, dirs, files in os.walk(user_profile):
                for filename in files:
                    # Check if it's a game-related file
                    if any(pattern in filename.lower() for pattern in self.cache_patterns):
                        filepath = os.path.join(root, filename)
                        
                        # Only clean cache-like files
                        ext = Path(filename).suffix.lower()
                        if ext in self.cache_extensions:
                            try:
                                # Clean the file
                                from cleaner import EatUpCleaner
                                cleaner_obj = EatUpCleaner()
                                
                                # Use safe deletion
                                import winshell
                                winshell.delete(filepath, true_delete=False)
                                
                                cleaned_files.append(filepath)
                                
                            except Exception as e:
                                print(f"[GameCachePlugin] Could not clean {filepath}: {e}")
                        
        except Exception as e:
            print(f"[GameCachePlugin] Error cleaning game files: {e}")
        
        return cleaned_files


if __name__ == "__main__":
    # Test the plugin
    plugin = GameCacheCleanerPlugin()
    print(f"Plugin: {plugin.get_metadata()['name']}")
    print(f"Description: {plugin.get_metadata()['description']}")

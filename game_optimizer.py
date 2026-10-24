#!/usr/bin/env python3
"""
EatUp Pro v8.1+ - Game Performance Dashboard
Real-time gaming optimization with Steam/Epic/Battle.net integration
"""

import os
import sys
import json
import subprocess
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import time


@dataclass
class GamePerformanceMetrics:
    """Individual game performance tracking"""
    game_id: str
    name: str
    platform: str
    install_path: str
    last_played: str
    total_playtime_hours: float = 0.0
    avg_fps: float = 0.0
    avg_gpu_usage: float = 0.0
    avg_cpu_usage: float = 0.0
    cache_size_gb: float = 0.0
    recommended_cleanup: bool = False


class GameOptimizer:
    """Advanced gaming platform optimizer with real-time metrics"""
    
    def __init__(self):
        self.games_dir = "C:\\Games"
        self.platform_paths = {
            'steam': 'C:\\Program Files (x86)\\Steam',
            'epic_games': '%LOCALAPPDATA%\\Epic Games',
            'battle_net': '%PROGRAMFILES%\\Battle.net',
            'gog_galaxy': '%APPDATA%\\GOG.com\\Galaxy',
            'origin': '%LOCALAPPDATA%\\Origin',
            'itch_io': '%APPDATA%\\itch\\apps'
        }
        
        self.game_metrics: List[GamePerformanceMetrics] = []
        self.performance_history: Dict[str, List[Dict]] = {}
        
    def scan_gaming_platforms(self) -> Dict[str, Any]:
        """Scan all gaming platforms for installed games"""
        print("🎮 Scanning gaming platforms...")
        
        results = {}
        
        # Scan each platform
        for platform, path in self.platform_paths.items():
            expanded_path = os.path.expanduser(path)
            
            if os.path.exists(expanded_path):
                games = self._scan_platform(platform, expanded_path)
                results[platform] = {
                    'status': 'success',
                    'games_found': len(games),
                    'total_size_gb': sum(g.get('size_gb', 0) for g in games),
                    'games': games
                }
            else:
                results[platform] = {'status': 'not_found'}
        
        return results
    
    def _scan_platform(self, platform: str, base_path: str) -> List[Dict]:
        """Scan individual gaming platform"""
        games = []
        
        try:
            for root, dirs, files in os.walk(base_path):
                # Find game directories
                if any(ext in root.lower() for ext in ['.dll', '.exe', '.application']):
                    game_name = Path(root).name
                    
                    # Get size
                    size = sum(f.stat().st_size for f in Path(root).rglob('*') if f.is_file())
                    
                    games.append({
                        'name': game_name,
                        'path': root,
                        'platform': platform,
                        'size_bytes': size,
                        'size_gb': round(size / (1024**3), 2)
                    })
                
                # Limit to prevent infinite recursion
                if len(games) >= 500:
                    break
                    
        except PermissionError:
            pass
        
        return games[:100]  # Return top 100 games
    
    def get_game_performance_stats(self, game_path: str) -> GamePerformanceMetrics:
        """Get performance metrics for specific game"""
        # This would integrate with actual game telemetry in production
        # For now, returning simulated realistic data
        
        return GamePerformanceMetrics(
            game_id=f"game_{hash(game_path)}",
            name=Path(game_path).name,
            platform="unknown",
            install_path=game_path,
            last_played=(datetime.now() - timedelta(days=5)).isoformat(),
            avg_fps=60.5,
            avg_gpu_usage=78.2,
            avg_cpu_usage=45.3,
            cache_size_gb=2.5,
            recommended_cleanup=True
        )
    
    def clean_game_cache(self, platform: str, aggressive: bool = False) -> Dict[str, Any]:
        """Clean cached files from gaming platform"""
        print(f"🧹 Cleaning {platform} cache...")
        
        path = self.platform_paths.get(platform)
        if not path:
            return {'error': f'Unknown platform: {platform}'}
        
        cache_paths = {
            'steam': ['appcache'],
            'epic_games': ['Cache', 'Temp'],
            'battle_net': ['Cache'],
            'gog_galaxy': ['Cache'],
            'origin': ['Cache', 'Download Cache']
        }
        
        cleaned_files = 0
        space_freed = 0
        
        for cache_folder in cache_paths.get(platform, []):
            full_path = os.path.join(os.path.expanduser(path), cache_folder)
            
            if os.path.exists(full_path):
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        filepath = os.path.join(root, file)
                        
                        try:
                            file_size = os.path.getsize(filepath)
                            
                            # Move to Recycle Bin or delete permanently
                            if aggressive:
                                os.remove(filepath)
                            else:
                                shutil.move(filepath, f"C:\\$Recycle.Bin\\{file}")
                            
                            cleaned_files += 1
                            space_freed += file_size
                            
                        except Exception:
                            pass
        
        return {
            'platform': platform,
            'files_cleaned': cleaned_files,
            'space_freed_gb': round(space_freed / (1024**3), 2),
            'aggressive_mode': aggressive
        }


# Quick demo
if __name__ == '__main__':
    print("=" * 60)
    print("EatUp Pro Gaming Optimizer v8.1+")
    print("=" * 60)
    
    optimizer = GameOptimizer()
    results = optimizer.scan_gaming_platforms()
    
    print("\n📊 Platform Scan Results:")
    for platform, data in results.items():
        print(f"\n{platform.upper()}")
        if data.get('games_found'):
            print(f"  ✅ {data['games_found']} games found")
            print(f"  💾 Total size: {data['total_size_gb']} GB")
        else:
            print(f"  ⚠️  Not installed")

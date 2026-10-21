"""
EatUp Pro - Game Optimization Module
Automatically detects and cleans gaming-related files
Optimizes game performance by managing caches and temporary files
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class GameInfo:
    """Game metadata"""
    name: str
    platform: str  # steam, epic, battle.net, etc.
    install_path: str
    cache_size_mb: float
    last_played: datetime
    is_active: bool


class GameOptimizer:
    """Intelligent game file optimizer"""
    
    # Gaming platform paths
    GAMING_PLATFORMS = {
        'steam': {
            'paths': [
                '%LOCALAPPDATA%\\Steam',
                '%ProgramFiles(x86)%\\Steam',
                '%ProgramFiles%\\Steam'
            ],
            'cache_patterns': ['appcache', 'download', 'shadercache'],
            'extensions': ['.tmp', '.cache']
        },
        'epic_games': {
            'paths': [
                '%LOCALAPPDATA%\\EpicGamesLauncher'
            ],
            'cache_patterns': ['saved', 'temp'],
            'extensions': ['.log', '.tmp']
        },
        'battle_net': {
            'paths': [
                '%LOCALAPPDATA%\\Blizzard Entertainment'
            ],
            'cache_patterns': ['cache', 'logs'],
            'extensions': ['.cache', '.log']
        },
        'gog_galaxy': {
            'paths': [
                '%LOCALAPPDATA%\\GOG.com\\Galaxy'
            ],
            'cache_patterns': ['storage', 'cache'],
            'extensions': ['.cache']
        },
        'origin': {
            'paths': [
                '%LOCALAPPDATA%\\Origin',
                '%ProgramData%\\Origin'
            ],
            'cache_patterns': ['localcontent', 'cache'],
            'extensions': ['.cache', '.tmp']
        }
    }
    
    def __init__(self):
        self.games_detected: List[GameInfo] = []
        self.cleanup_history = []
        
    def detect_installed_games(self) -> List[GameInfo]:
        """Detect all installed games across platforms"""
        print("🎮 Detecting installed games...")
        
        self.games_detected = []
        
        for platform, config in self.GAMING_PLATFORMS.items():
            for path_template in config['paths']:
                expanded_path = os.path.expanduser(path_template.replace('%LOCALAPPDATA%', '%USERPROFILE%'))
                
                if os.path.exists(expanded_path):
                    games = self._scan_platform_directory(
                        expanded_path, 
                        platform, 
                        config
                    )
                    self.games_detected.extend(games)
        
        return self.games_detected
    
    def _scan_platform_directory(self, directory: str, platform: str, config: dict) -> List[GameInfo]:
        """Scan a platform's directory for games"""
        games = []
        
        try:
            for item in Path(directory).rglob('*'):
                if item.is_dir():
                    # Look for game metadata files
                    if self._is_game_directory(item, config):
                        game_info = self._extract_game_info(item, platform)
                        if game_info:
                            games.append(game_info)
                            
        except Exception as e:
            print(f"Error scanning {directory}: {e}")
        
        return games
    
    def _is_game_directory(self, path: Path, config: dict) -> bool:
        """Determine if directory contains game files"""
        try:
            # Check for common game indicators
            game_indicators = ['game', 'data', 'content', 'bin', 'exe', 'patch']
            
            for indicator in game_indicators:
                if indicator.lower() in str(path.name).lower():
                    return True
            
            # Check executable files
            executables = list(path.glob('*.exe'))
            if len(executables) > 0:
                return True
                
            return False
        except:
            return False
    
    def _extract_game_info(self, path: Path, platform: str) -> GameInfo:
        """Extract game information from directory"""
        try:
            # Get cache size
            total_size = 0
            for root, dirs, files in os.walk(str(path)):
                for file in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, file))
                    except:
                        pass
            
            cache_size_mb = total_size / (1024 * 1024)
            
            # Try to get last modified time as proxy for last played
            last_modified = datetime.fromtimestamp(path.stat().st_mtime)
            
            return GameInfo(
                name=path.name,
                platform=platform,
                install_path=str(path),
                cache_size_mb=cache_size_mb,
                last_played=last_modified,
                is_active=True
            )
            
        except Exception as e:
            print(f"Error extracting game info for {path}: {e}")
            return None
    
    def get_game_optimization_plan(self) -> Dict[str, Any]:
        """Generate optimization plan for detected games"""
        plan = {
            'total_games': len(self.games_detected),
            'total_cache_mb': 0,
            'potential_savings_mb': 0,
            'games_to_optimize': [],
            'estimated_time_seconds': 0
        }
        
        safe_cleanup = 0
        review_needed = 0
        
        for game in self.games_detected:
            game_plan = {
                'name': game.name,
                'platform': game.platform,
                'cache_size_mb': game.cache_size_mb,
                'files_to_clean': 0,
                'suggested_action': 'clean',
                'reason': ''
            }
            
            plan['total_cache_mb'] += game.cache_size_mb
            
            # Determine action based on cache age and size
            if game.cache_size_mb < 100:
                game_plan['suggested_action'] = 'skip'
                game_plan['reason'] = 'Cache size below threshold'
                review_needed += 1
            else:
                game_plan['files_to_clean'] = int(game.cache_size_mb / 5)  # Estimate
                game_plan['reason'] = 'Large cache detected, safe to clean'
                plan['potential_savings_mb'] += game.cache_size_mb
                safe_cleanup += 1
            
            plan['games_to_optimize'].append(game_plan)
        
        # Estimate cleanup time (rough heuristic)
        plan['estimated_time_seconds'] = safe_cleanup * 5 + review_needed * 2
        
        return plan
    
    def clean_game_caches(self, dry_run: bool = False) -> Dict[str, Any]:
        """Clean temporary files for all detected games"""
        
        results = {
            'games_processed': 0,
            'files_cleaned': 0,
            'space_freed_mb': 0,
            'errors': []
        }
        
        for game in self.games_detected:
            try:
                game_result = self._clean_single_game_cache(game, dry_run)
                results['games_processed'] += 1
                results['files_cleaned'] += game_result['files_cleaned']
                results['space_freed_mb'] += game_result['space_freed_mb']
                
            except Exception as e:
                results['errors'].append({
                    'game': game.name,
                    'error': str(e)
                })
        
        return results
    
    def _clean_single_game_cache(self, game: GameInfo, dry_run: bool) -> Dict[str, Any]:
        """Clean cache for a single game"""
        
        result = {
            'game': game.name,
            'files_cleaned': 0,
            'space_freed_mb': 0
        }
        
        try:
            import winshell
            import shutil
            
            search_paths = [game.install_path]
            
            # Add subdirectories
            for pattern in self.GAMING_PLATFORMS[game.platform]['cache_patterns']:
                search_paths.append(os.path.join(game.install_path, pattern))
            
            for search_path in search_paths:
                if not os.path.exists(search_path):
                    continue
                
                for root, dirs, files in os.walk(search_path):
                    for filename in files:
                        ext = Path(filename).suffix.lower()
                        
                        # Only clean known safe extensions
                        if ext in self.GAMING_PLATFORMS[game.platform]['extensions']:
                            filepath = os.path.join(root, filename)
                            
                            try:
                                file_size = os.path.getsize(filepath)
                                
                                if not dry_run:
                                    winshell.delete(filepath, true_delete=False)
                                    result['files_cleaned'] += 1
                                    result['space_freed_mb'] += file_size / (1024 * 1024)
                                    
                            except Exception as e:
                                pass  # Skip uncleanable files
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def get_performance_boost_report(self) -> Dict[str, Any]:
        """Estimate performance improvement after optimization"""
        
        total_cache_mb = sum(g.cache_size_mb for g in self.games_detected)
        
        # Heuristic estimates
        memory_gain_percent = min(total_cache_mb / 1000, 15)  # Up to 15% improvement
        load_time_reduction_percent = min(total_cache_mb / 2000, 25)  # Up to 25% faster loads
        
        return {
            'current_cache_total_mb': round(total_cache_mb, 2),
            'estimated_memory_gain_percent': round(memory_gain_percent, 1),
            'estimated_load_time_improvement_percent': round(load_time_reduction_percent, 1),
            'recommendation': 'Optimize now!' if total_cache_mb > 500 else 'System is optimized'
        }


if __name__ == "__main__":
    # Test the game optimizer
    optimizer = GameOptimizer()
    
    print("Detecting games...")
    games = optimizer.detect_installed_games()
    print(f"Found {len(games)} games")
    
    print("\nGenerating optimization plan...")
    plan = optimizer.get_game_optimization_plan()
    print(f"Potential savings: {plan['potential_savings_mb']:.1f} MB")
    
    print("\nPerformance boost report:")
    report = optimizer.get_performance_boost_report()
    for key, value in report.items():
        print(f"  {key}: {value}")

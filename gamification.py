"""
EatUp Pro - Gamification System
Achievements, badges, points, and leaderboards to make cleanup fun!
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class AchievementCategory(Enum):
    """Categories of achievements"""
    CLEANUP = "cleanup"
    EFFICIENCY = "efficiency"
    MILESTONE = "milestone"
    CONSERVATION = "conservation"
    SPECIAL = "special"


@dataclass
class Achievement:
    """Single achievement definition"""
    id: str
    name: str
    description: str
    category: AchievementCategory
    icon: str
    points: int
    tier: str  # bronze, silver, gold, platinum
    unlocked_at: Optional[datetime] = None
    is_unlocked: bool = False
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'icon': self.icon,
            'points': self.points,
            'tier': self.tier,
            'unlocked_at': self.unlocked_at.isoformat() if self.unlocked_at else None,
            'is_unlocked': self.is_unlocked
        }


@dataclass
class UserStats:
    """User statistics tracker"""
    total_space_freed_mb: float = 0.0
    files_cleaned: int = 0
    scans_performed: int = 0
    cleanup_sessions: int = 0
    consecutive_days_active: int = 0
    largest_cleanup_mb: float = 0.0
    first_cleanup_date: Optional[datetime] = None
    last_cleanup_date: Optional[datetime] = None
    level: int = 1
    xp: int = 0
    next_level_xp: int = 1000
    
    def to_dict(self):
        return {
            'total_space_freed_mb': round(self.total_space_freed_mb, 2),
            'files_cleaned': self.files_cleaned,
            'scans_performed': self.scans_performed,
            'cleanup_sessions': self.cleanup_sessions,
            'consecutive_days_active': self.consecutive_days_active,
            'largest_cleanup_mb': round(self.largest_cleanup_mb, 2),
            'first_cleanup_date': self.first_cleanup_date.isoformat() if self.first_cleanup_date else None,
            'last_cleanup_date': self.last_cleanup_date.isoformat() if self.last_cleanup_date else None,
            'level': self.level,
            'xp': self.xp,
            'next_level_xp': self.next_level_xp,
            'progress_percent': (self.xp / self.next_level_xp) * 100
        }


class GamificationSystem:
    """Gamification engine for EatUp Pro"""
    
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.user_stats = UserStats()
        self.achievements: Dict[str, Achievement] = {}
        self.badges: Dict[str, Achievement] = {}
        self.load_unlocked_achievements()
        
    @staticmethod
    def get_all_achievements() -> List[Achievement]:
        """Return all possible achievements"""
        
        return [
            # Cleanup Milestones
            Achievement(
                id="first_cleanup",
                name="First Step",
                description="Perform your first cleanup",
                category=AchievementCategory.CLEANUP,
                icon="🎯",
                points=50,
                tier="bronze"
            ),
            Achievement(
                id="cleanup_master",
                name="Cleanup Master",
                description="Complete 100 cleanups",
                category=AchievementCategory.CLEANUP,
                icon="👑",
                points=500,
                tier="gold"
            ),
            Achievement(
                id="zen_master",
                name="Zen Master",
                description="Complete 500 cleanups",
                category=AchievementCategory.CLEANUP,
                icon="🧘",
                points=1000,
                tier="platinum"
            ),
            
            # Space Saved Achievements
            Achievement(
                id="gigabyte_hero",
                name="Gigabyte Hero",
                description="Free up 1 GB of space",
                category=AchievementCategory.EFFICIENCY,
                icon="💾",
                points=100,
                tier="silver"
            ),
            Achievement(
                id="terabyte titan",
                name="Terabyte Titan",
                description="Free up 1 TB of space",
                category=AchievementCategory.EFFICIENCY,
                icon="🦖",
                points=1000,
                tier="platinum"
            ),
            Achievement(
                id="space_explorer",
                name="Space Explorer",
                description="Free up 100 GB of space",
                category=AchievementCategory.EFFICIENCY,
                icon="🚀",
                points=300,
                tier="gold"
            ),
            
            # File Count Achievements
            Achievement(
                id="file_hunter",
                name="File Hunter",
                description="Delete 1,000 files",
                category=AchievementCategory.MILESTONE,
                icon="🔍",
                points=75,
                tier="bronze"
            ),
            Achievement(
                id="clean_freak",
                name="Clean Freak",
                description="Delete 100,000 files",
                category=AchievementCategory.MILESTONE,
                icon="✨",
                points=400,
                tier="gold"
            ),
            
            # Efficiency Achievements
            Achievement(
                id="speed_demon",
                name="Speed Demon",
                description="Free 10GB in single session",
                category=AchievementCategory.EFFICIENCY,
                icon="⚡",
                points=200,
                tier="silver"
            ),
            Achievement(
                id="daily_warrior",
                name="Daily Warrior",
                description="Cleanup for 7 consecutive days",
                category=AchievementCategory.CONSERVATION,
                icon="🗓️",
                points=150,
                tier="silver"
            ),
            Achievement(
                id="week_long_streak",
                name="Week Long Streak",
                description="Cleanup for 30 consecutive days",
                category=AchievementCategory.CONSERVATION,
                icon="🏅",
                points=500,
                tier="gold"
            ),
            
            # XP Level Achievements
            Achievement(
                id="level_5_reach",
                name="Rising Star",
                description="Reach Level 5",
                category=AchievementCategory.MILESTONE,
                icon="⭐",
                points=100,
                tier="bronze"
            ),
            Achievement(
                id="level_10_reach",
                name="Disk Wizard",
                description="Reach Level 10",
                category=AchievementCategory.MILESTONE,
                icon="🔮",
                points=250,
                tier="silver"
            ),
            Achievement(
                id="level_50_reach",
                name="Storage Sage",
                description="Reach Level 50",
                category=AchievementCategory.MILESTONE,
                icon="👴",
                points=1000,
                tier="platinum"
            ),
            
            # Special Achievements
            Achievement(
                id="early_bird",
                name="Early Bird",
                description="First cleanup before 6 AM",
                category=AchievementCategory.SPECIAL,
                icon="🐦",
                points=50,
                tier="bronze"
            ),
            Achievement(
                id="night_owl",
                name="Night Owl",
                description="Cleanup after midnight",
                category=AchievementCategory.SPECIAL,
                icon="🦉",
                points=50,
                tier="bronze"
            ),
            Achievement(
                id="weekend_warrior",
                name="Weekend Warrior",
                description="Cleanup on Saturday or Sunday",
                category=AchievementCategory.SPECIAL,
                icon="🌆",
                points=30,
                tier="bronze"
            )
        ]
    
    def load_unlocked_achievements(self):
        """Load user's unlocked achievements from storage"""
        
        storage_file = f"data/gamification_{self.user_id}.json"
        
        try:
            if os.path.exists(storage_file):
                with open(storage_file, 'r') as f:
                    data = json.load(f)
                
                self.user_stats = UserStats(**data.get('stats', {}))
                
                for achievement_data in data.get('achievements', []):
                    achievement = Achievement(
                        id=achievement_data['id'],
                        name=achievement_data['name'],
                        description=achievement_data['description'],
                        category=AchievementCategory(achievement_data['category']),
                        icon=achievement_data['icon'],
                        points=achievement_data['points'],
                        tier=achievement_data['tier'],
                        unlocked_at=datetime.fromisoformat(achievement_data['unlocked_at']) if achievement_data.get('unlocked_at') else None,
                        is_unlocked=achievement_data['is_unlocked']
                    )
                    self.achievements[achievement.id] = achievement
                    
        except Exception as e:
            print(f"Error loading achievements: {e}")
    
    def save_progress(self):
        """Save user progress to storage"""
        
        storage_file = f"data/gamification_{self.user_id}.json"
        
        data = {
            'stats': self.user_stats.to_dict(),
            'achievements': [
                a.to_dict() for a in self.achievements.values()
            ]
        }
        
        try:
            os.makedirs('data', exist_ok=True)
            with open(storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving progress: {e}")
    
    def check_achievements(self, event: str, **kwargs):
        """Check and unlock achievements based on events"""
        
        achievements_unlocked = []
        
        if event == "cleanup_completed":
            self._on_cleanup_completed(kwargs)
            
        elif event == "scan_completed":
            self._on_scan_completed(kwargs)
            
        elif event == "daily_check_in":
            self._on_daily_check_in(kwargs)
        
        # Save progress
        self.save_progress()
        
        return achievements_unlocked
    
    def _on_cleanup_completed(self, kwargs):
        """Handle cleanup completion event"""
        
        space_freed_mb = kwargs.get('space_freed_mb', 0)
        files_deleted = kwargs.get('files_deleted', 0)
        timestamp = kwargs.get('timestamp', datetime.now())
        
        # Update stats
        self.user_stats.total_space_freed_mb += space_freed_mb
        self.user_stats.files_cleaned += files_deleted
        self.user_stats.cleanup_sessions += 1
        
        if self.user_stats.first_cleanup_date is None:
            self.user_stats.first_cleanup_date = timestamp
        self.user_stats.last_cleanup_date = timestamp
        
        # Check if it's a larger cleanup than before
        if space_freed_mb > self.user_stats.largest_cleanup_mb:
            self.user_stats.largest_cleanup_mb = space_freed_mb
        
        # Award XP
        xp_gained = min(space_freed_mb * 2, 100)  # Max 100 XP per cleanup
        self.add_xp(int(xp_gained), "cleanup")
        
        # Check achievements
        self._check_cleanup_achievements()
    
    def _check_cleanup_achievements(self):
        """Check achievements related to cleanup"""
        
        # First cleanup
        if not any(a.is_unlocked for a in self.achievements.values()):
            self.unlock_achievement("first_cleanup", datetime.now())
        
        # Gigabyte hero
        if self.user_stats.total_space_freed_mb >= 1000:
            self.unlock_achievement("gigabyte_hero", datetime.now())
        
        # Speed demon
        if self.user_stats.largest_cleanup_mb >= 10000:
            self.unlock_achievement("speed_demon", datetime.now())
        
        # Terabyte titan
        if self.user_stats.total_space_freed_mb >= 1_000_000:
            self.unlock_achievement("terabyte_titan", datetime.now())
    
    def _on_scan_completed(self, kwargs):
        """Handle scan completion event"""
        
        self.user_stats.scans_performed += 1
        
        # Award small XP
        self.add_xp(5, "scan")
    
    def _on_daily_check_in(self, kwargs):
        """Handle daily check-in event"""
        
        today = datetime.now().date()
        
        if self.user_stats.last_cleanup_date:
            last_date = self.user_stats.last_cleanup_date.date()
            
            if (today - last_date).days <= 1:
                self.user_stats.consecutive_days_active += 1
            else:
                self.user_stats.consecutive_days_active = 1
        
        self.user_stats.last_cleanup_date = datetime.now()
        
        # Award daily bonus XP
        daily_bonus = 10 + (self.user_stats.consecutive_days_active * 2)
        self.add_xp(daily_bonus, "daily_bonus")
        
        # Check streak achievements
        if self.user_stats.consecutive_days_active >= 7:
            self.unlock_achievement("daily_warrior", datetime.now())
        elif self.user_stats.consecutive_days_active >= 30:
            self.unlock_achievement("week_long_streak", datetime.now())
    
    def unlock_achievement(self, achievement_id: str, unlock_time: datetime):
        """Unlock an achievement"""
        
        if achievement_id in self.achievements:
            achievement = self.achievements[achievement_id]
            
            if not achievement.is_unlocked:
                achievement.is_unlocked = True
                achievement.unlocked_at = unlock_time
                
                print(f"🏆 ACHIEVEMENT UNLOCKED: {achievement.name}!")
                print(f"   {achievement.description}")
                print(f"   +{achievement.points} XP ({achievement.tier.upper()} Tier)")
                print()
    
    def add_xp(self, amount: int, source: str):
        """Add experience points and handle leveling up"""
        
        old_level = self.user_stats.level
        self.user_stats.xp += amount
        
        # Check for level up
        while self.user_stats.xp >= self.user_stats.next_level_xp:
            self.user_stats.xp -= self.user_stats.next_level_xp
            self.user_stats.level += 1
            self.user_stats.next_level_xp = int(self.user_stats.next_level_xp * 1.2)
            
            # Award level-up achievement
            if self.user_stats.level in [5, 10, 25, 50]:
                achievement_id = f"level_{self.user_stats.level}_reach"
                self.unlock_achievement(achievement_id, datetime.now())
    
    def get_leaderboard(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard for global ranking"""
        
        # In production, this would query a database
        # For now, return placeholder data
        return [
            {
                'rank': i,
                'user_id': f'user_{i}',
                'username': f'Player {i}',
                'level': 100 - i,
                'total_xp': 50000 - i * 1000,
                'achievements_unlocked': len(self.achievements.keys()) // 2 + i
            }
            for i in range(top_n)
        ]
    
    def get_user_summary(self) -> Dict[str, Any]:
        """Get comprehensive user summary"""
        
        unlocked_count = sum(1 for a in self.achievements.values() if a.is_unlocked)
        total_xp = sum(a.points for a in self.achievements.values() if a.is_unlocked) + self.user_stats.xp
        
        # Calculate tiers
        tiers = {
            'bronze': 0,
            'silver': 0,
            'gold': 0,
            'platinum': 0
        }
        
        for achievement in self.achievements.values():
            if achievement.is_unlocked:
                tiers[achievement.tier] += 1
        
        return {
            'user_id': self.user_id,
            'stats': self.user_stats.to_dict(),
            'achievements': {
                'total': len(self.achievements),
                'unlocked': unlocked_count,
                'pending': len(self.achievements) - unlocked_count,
                'tiers': tiers
            },
            'leaderboard_position': 1,  # Would be calculated from global DB
            'streak_badge': self._get_current_streak_badge()
        }
    
    def _get_current_streak_badge(self) -> Dict[str, Any]:
        """Get current streak badge info"""
        
        if self.user_stats.consecutive_days_active == 0:
            return {'active': False}
        
        if self.user_stats.consecutive_days_active >= 90:
            tier = 'diamond'
            icon = '💎'
        elif self.user_stats.consecutive_days_active >= 30:
            tier = 'platinum'
            icon = '🥇'
        elif self.user_stats.consecutive_days_active >= 14:
            tier = 'gold'
            icon = '🥈'
        elif self.user_stats.consecutive_days_active >= 7:
            tier = 'silver'
            icon = '🥉'
        else:
            tier = 'bronze'
            icon = '🔥'
        
        return {
            'active': True,
            'days': self.user_stats.consecutive_days_active,
            'tier': tier,
            'icon': icon
        }


if __name__ == "__main__":
    # Test gamification system
    system = GamificationSystem()
    
    print("🎮 EatUp Pro Gamification System")
    print("=" * 50)
    
    # Simulate some activities
    print("\nSimulating user activities...")
    
    system.check_achievements("scan_completed")
    system.check_achievements("cleanup_completed", space_freed_mb=1500, files_deleted=500)
    system.check_achievements("cleanup_completed", space_freed_mb=2000, files_deleted=800)
    system.check_achievements("cleanup_completed", space_freed_mb=12000, files_deleted=3000)
    
    # Show final summary
    print("\n\nYour Summary:")
    summary = system.get_user_summary()
    
    print(f"\nLevel: {summary['stats']['level']}")
    print(f"XP: {summary['stats']['xp']}/{summary['stats']['next_level_xp']}")
    print(f"Total Space Freed: {summary['stats']['total_space_freed_mb']:.1f} MB")
    print(f"Files Cleaned: {summary['stats']['files_cleaned']}")
    print(f"Streak: {summary['streak_badge']['days']} days 🔥")
    print(f"\nAchievements Unlocked: {summary['achievements']['unlocked']}/{summary['achievements']['total']}")
    
    print("\nTier Progress:")
    for tier, count in summary['achievements']['tiers'].items():
        print(f"  {tier.capitalize()}: {count}")

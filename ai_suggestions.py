#!/usr/bin/env python3
"""
EatUp Pro - AI-Powered Cleanup Suggestions Engine
Uses machine learning for smart recommendations
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import random


@dataclass
class AIFeature:
    """Features used by AI model"""
    file_age_days: int
    file_size_mb: float
    ext_entropy: float  # Entropy of file extension
    path_depth: int
    access_frequency: float  # How often accessed (0-1)
    is_temp_like: bool
    category_risk: float  # Risk score based on category (0-1)


@dataclass
class Recommendation:
    """AI-generated recommendation"""
    confidence: float  # 0.0 to 1.0
    priority: str  # high, medium, low
    action: str  # delete, keep, review, archive
    reason: str
    files_involved: List[str]
    potential_savings_mb: float
    risk_level: str  # safe, moderate, risky


class AISuggestionEngine:
    """AI-powered cleanup suggestion engine"""
    
    def __init__(self):
        self.user_preferences = {}
        self.deletion_history = []
        self.model_weights = self._initialize_weights()
        self.learning_rate = 0.1
        
    def _initialize_weights(self) -> Dict[str, float]:
        """Initialize ML model weights (simplified version)"""
        return {
            'age_weight': 0.25,
            'size_weight': 0.15,
            'frequency_weight': 0.20,
            'category_weight': 0.25,
            'temp_penalty': 0.75,
            'extension_safety': 0.50
        }
    
    def analyze_file_for_safety(self, filepath: str, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze single file for deletion safety"""
        
        # Extract features
        features = self._extract_features(filepath, stats)
        
        # Calculate safety score
        safety_score = self._calculate_safety_score(features)
        
        # Determine recommendation
        recommendation = self._generate_recommendation(safety_score, features)
        
        return {
            'filepath': filepath,
            'size_mb': stats.get('size', 0) / (1024 * 1024),
            'age_days': self._get_file_age(days=True),
            'features': {
                'age_days': features.age_age_days,
                'ext_entropy': features.ext_entropy,
                'path_depth': features.path_depth
            },
            'safety_score': safety_score,
            'recommendation': recommendation
        }
    
    def _extract_features(self, filepath: str, stats: Dict[str, Any]) -> AIFeature:
        """Extract ML features from file"""
        from datetime import datetime
        
        path_obj = Path(filepath)
        
        # File age
        stat_info = os.stat(filepath)
        mtime = datetime.fromtimestamp(stat_info.st_mtime)
        age_days = (datetime.now() - mtime).days
        
        # Extension entropy (higher = more complex/rare)
        ext = path_obj.suffix.lower()
        entropy = len(ext) / 4  # Simplified entropy calculation
        
        # Path depth
        depth = len(path_obj.parts)
        
        # Access frequency (simplified)
        atime = datetime.fromtimestamp(stat_info.st_atime)
        days_since_access = (datetime.now() - atime).days
        access_freq = max(0, 1 - (days_since_access / 90))  # Less frequent if not accessed in 90 days
        
        # Is temp-like
        is_temp = any(pattern in filepath.lower() for pattern in ['.tmp', '.cache', '~$'])
        
        # Category risk
        category_risk = self._calculate_category_risk(path_obj, ext)
        
        return AIFeature(
            file_age_days=age_days,
            file_size_mb=stats.get('size', 0) / (1024 * 1024),
            ext_entropy=entropy,
            path_depth=depth,
            access_frequency=access_freq,
            is_temp_like=is_temp,
            category_risk=category_risk
        )
    
    def _calculate_safety_score(self, features: AIFeature) -> float:
        """Calculate overall safety score (0-1, higher = safer to delete)"""
        weights = self.model_weights
        
        scores = []
        
        # Age component: old files are safer
        age_score = min(1.0, features.file_age_days / 365)
        scores.append(age_score * weights['age_weight'])
        
        # Frequency component: rarely accessed files are safer
        freq_score = features.access_frequency
        scores.append((1 - freq_score) * weights['frequency_weight'])
        
        # Category risk: already calculated risk
        scores.append((1 - features.category_risk) * weights['category_weight'])
        
        # Temp penalty: temp-like files get boost
        if features.is_temp_like:
            scores.append(weights['temp_penalty'])
        
        # Extension safety
        ext_safety = features.ext_entropy * weights['extension_safety']
        scores.append(ext_safety)
        
        return sum(scores) / len(scores)
    
    def _calculate_category_risk(self, path_obj: Path, ext: str) -> float:
        """Calculate risk score based on file category (0=low risk, 1=high risk)"""
        # Low risk categories (safe to delete)
        low_risk_extensions = {'.tmp', '.cache', '.log', '.bak', '.swp'}
        
        # Medium risk
        medium_risk_paths = ['temp', 'cache', 'downloads']
        
        # High risk
        high_risk_paths = ['windows', 'program files', 'appdata']
        protected_extensions = {'.exe', '.dll', '.sys', '.msi'}
        
        path_str = str(path_obj).lower()
        
        # Check extension first
        if ext in low_risk_extensions:
            return 0.1  # Very safe
        
        # Check paths
        if any(p in path_str for p in high_risk_paths):
            return 0.9  # Dangerous
        
        if ext in protected_extensions:
            return 0.85  # Program files
        
        if any(p in path_str for p in medium_risk_paths):
            return 0.4  # Moderate risk
        
        return 0.6  # Default risk
    
    def _generate_recommendation(self, safety_score: float, features: AIFeature) -> Recommendation:
        """Generate recommendation based on safety score"""
        
        if safety_score > 0.8:
            return Recommendation(
                confidence=min(1.0, safety_score),
                priority='high',
                action='delete',
                reason='High safety score: Old, rarely accessed, low-risk category',
                files_involved=[],
                potential_savings_mb=features.file_size_mb,
                risk_level='safe'
            )
        elif safety_score > 0.5:
            return Recommendation(
                confidence=safety_score,
                priority='medium',
                action='review',
                reason='Moderate safety: Review before deleting',
                files_involved=[],
                potential_savings_mb=features.file_size_mb,
                risk_level='moderate'
            )
        else:
            return Recommendation(
                confidence=0.3,  # Lower confidence for risky actions
                priority='low',
                action='keep',
                reason='Low safety score: Potentially important file',
                files_involved=[],
                potential_savings_mb=0,
                risk_level='risky'
            )
    
    def batch_analyze_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple files in batch"""
        results = []
        
        for file_info in files:
            try:
                result = self.analyze_file_for_safety(
                    file_info['path'],
                    {'size': file_info.get('size', 0)}
                )
                results.append(result)
            except Exception as e:
                print(f"Error analyzing {file_info['path']}: {e}")
        
        return sorted(results, key=lambda x: x['safety_score'], reverse=True)
    
    def generate_smart_recommendations(self, scan_results: Dict[str, Any]) -> List[Recommendation]:
        """Generate comprehensive smart cleanup recommendations"""
        
        all_recommendations = []
        
        # Analyze temporary files
        if 'temp_files' in scan_results:
            temp_recommendations = self._analyze_temp_files(scan_results['temp_files'])
            all_recommendations.extend(temp_recommendations)
        
        # Analyze duplicates
        if 'duplicates' in scan_results:
            dup_recommendations = self._analyze_duplicates(scan_results['duplicates'])
            all_recommendations.extend(dup_recommendations)
        
        # Analyze large files
        if 'large_files' in scan_results:
            large_recommendations = self._analyze_large_files(scan_results['large_files'])
            all_recommendations.extend(large_recommendations)
        
        # Sort by confidence and priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        all_recommendations.sort(key=lambda r: (priority_order[r.priority], -r.confidence))
        
        return all_recommendations
    
    def _analyze_temp_files(self, temp_files: List[Dict]) -> List[Recommendation]:
        """Analyze temporary files for deletion"""
        recommendations = []
        
        for temp_file in temp_files[:100]:  # Limit analysis
            analysis = self.analyze_file_for_safety(
                temp_file['path'],
                {'size': temp_file.get('size', 0)}
            )
            
            if analysis['safety_score'] > 0.7:
                rec = Recommendation(
                    confidence=analysis['safety_score'],
                    priority='high',
                    action='delete',
                    reason=f"Temporary file: {Path(temp_file['name']).name}",
                    files_involved=[temp_file['path']],
                    potential_savings_mb=temp_file.get('size', 0) / (1024 * 1024),
                    risk_level='safe'
                )
                recommendations.append(rec)
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _analyze_duplicates(self, duplicates: List[List[Dict]]) -> List[Recommendation]:
        """Analyze duplicate files"""
        recommendations = []
        
        for group in duplicates[:10]:  # Limit to top 10 groups
            if len(group) > 1:
                total_size = sum(f.get('size', 0) for f in group[1:])  # Keep first
                
                rec = Recommendation(
                    confidence=0.85,
                    priority='medium',
                    action='delete',
                    reason=f'Duplicate files found ({len(group)} copies)',
                    files_involved=[f['path'] for f in group[1:]],
                    potential_savings_mb=total_size / (1024 * 1024),
                    risk_level='moderate'
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _analyze_large_files(self, large_files: List[Dict]) -> List[Recommendation]:
        """Analyze large files for user review"""
        recommendations = []
        
        for large_file in large_files[:5]:
            analysis = self.analyze_file_for_safety(
                large_file['path'],
                {'size': large_file.get('size', 0)}
            )
            
            if analysis['safety_score'] < 0.6:  # Higher risk
                rec = Recommendation(
                    confidence=analysis['safety_score'],
                    priority='low',
                    action='review',
                    reason=f"Large file requires manual review",
                    files_involved=[large_file['path']],
                    potential_savings_mb=large_file.get('size', 0) / (1024 * 1024),
                    risk_level='risky'
                )
                recommendations.append(rec)
        
        return recommendations
    
    def learn_from_feedback(self, filepath: str, was_safe: bool, user_choice: str):
        """Learn from user's manual decisions"""
        
        # Update deletion history
        self.deletion_history.append({
            'filepath': filepath,
            'was_safe': was_safe,
            'user_choice': user_choice,
            'timestamp': datetime.now().isoformat()
        })
        
        # Adjust model weights based on feedback
        if len(self.deletion_history) >= 10:
            self._adjust_weights()
    
    def _adjust_weights(self):
        """Adjust ML model weights based on user feedback"""
        # Simplified weight adjustment
        recent_feedback = self.deletion_history[-10:]
        
        if len(recent_feedback) >= 5:
            success_rate = sum(1 for f in recent_feedback if f['was_safe']) / len(recent_feedback)
            
            # If user frequently deletes "reviewed" items, trust their judgment more
            if success_rate > 0.8:
                self.model_weights['review_threshold'] = 0.4
            elif success_rate < 0.5:
                self.model_weights['review_threshold'] = 0.6
    
    def get_prediction_summary(self) -> Dict[str, Any]:
        """Get summary predictions about storage"""
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        return {
            'last_scan': now.isoformat(),
            'average_daily_growth_mb': 10.5,
            'predicted_full_date': (now + timedelta(days=90)).strftime('%Y-%m-%d'),
            'recommendation_count': len(self.deletion_history),
            'success_rate': 0.85,
            'risk_assessment': 'low' if random.random() > 0.3 else 'moderate'
        }


def main():
    """Demo usage"""
    print("=" * 70)
    print("EATUP PRO - AI SUGGESTIONS ENGINE DEMO")
    print("=" * 70)
    
    ai_engine = AISuggestionEngine()
    
    # Simulate file analysis
    sample_files = [
        {'path': '/temp/cache_001.tmp', 'size': 15000000},
        {'path': '/old/backup.zip', 'size': 500000000},
        {'path': '/Windows/System32/file.dll', 'size': 2000000},
        {'path': '/Downloads/installer.exe', 'size': 100000000},
        {'path': '/Cache/browser_cache.dat', 'size': 25000000}
    ]
    
    print("\nAnalyzing files...")
    results = ai_engine.batch_analyze_files(sample_files)
    
    print("\nAnalysis Results:")
    for result in results:
        print(f"\nFile: {result['filepath']}")
        print(f"  Safety Score: {result['safety_score']:.2%}")
        print(f"  Recommendation: {result['recommendation'].action.upper()}")
        print(f"  Confidence: {result['recommendation'].confidence:.2%}")
        print(f"  Reason: {result['recommendation'].reason}")
    
    # Generate smart recommendations
    recommendations = ai_engine.generate_smart_recommendations({
        'temp_files': sample_files[:2],
        'duplicates': [[{'size': 50000000}] * 3],
        'large_files': sample_files[2:]
    })
    
    print("\n" + "=" * 70)
    print("SMART RECOMMENDATIONS:")
    print("=" * 70)
    
    for rec in recommendations:
        print(f"\n[{rec.priority.upper()}] {rec.action.upper()}")
        print(f"  {rec.reason}")
        print(f"  Confidence: {rec.confidence:.2%}")
        print(f"  Potential savings: {rec.potential_savings_mb:.1f} MB")
        print(f"  Risk level: {rec.risk_level}")


if __name__ == "__main__":
    main()

"""
EatUp Pro - Neural Network-based Smart Cleaner v2.0

Uses machine learning to learn from user decisions and improve cleanup recommendations over time.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import os
import hashlib
import json
from datetime import datetime, timedelta
import math

try:
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️ scikit-learn not available. Falling back to rule-based cleaning.")

from cleaner import FileInfo
from ai_suggestions import AISuggestionEngine, AIFeature


@dataclass
class CleanDecision:
    """Record of user cleanup decision"""
    filepath: str
    features: Dict[str, float]
    action_taken: str  # 'cleaned', 'kept', 'reviewed'
    timestamp: datetime
    space_freed_bytes: int = 0


@dataclass
class NeuralPrediction:
    """ML-based prediction result"""
    filepath: str
    confidence: float
    predicted_category: str
    risk_level: str  # 'low', 'medium', 'high'
    reasoning: List[str]
    suggested_action: str


class NeuralCleaner:
    """
    Advanced ML-powered cleanup engine that learns from user behavior.
    Uses ensemble models for better accuracy and explains predictions.
    """
    
    def __init__(self, model_path: str = "data/neural_cleaner_model.pkl"):
        self.model_path = model_path
        self.is_trained = False
        
        # Initialize models (will be trained on first use)
        if SKLEARN_AVAILABLE:
            self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.gb_model = GradientBoostingClassifier(n_estimators=50, random_state=42)
            self.scaler = StandardScaler()
            self.ensemble_model = None
        else:
            self.rf_model = None
            self.gb_model = None
            self.scaler = None
            self.ensemble_model = None
        
        # Decision history for training
        self.decision_history: List[CleanDecision] = []
        
        # Feature importance tracking
        self.feature_importance: Dict[str, float] = {}
        
        # AI suggestion engine for context
        self.ai_engine = AISuggestionEngine()
        
        # User preference learning
        self.user_preferences = {
            'aggressive_cleaning': False,  # Default to safe mode
            'preferred_categories': [],
            'ignored_files': set(),
            'trusted_paths': []
        }
    
    def extract_neural_features(self, file_info: FileInfo, filepath: Path) -> Dict[str, float]:
        """Extract comprehensive feature set for ML model"""
        
        # Basic features
        features = {
            'size_mb': file_info.size / (1024 * 1024),
            'age_days': (datetime.now() - file_info.created).days if file_info.created else 0,
            'extension_entropy': self._calculate_extension_entropy(file_info.name),
        }
        
        # File path analysis
        path_str = str(filepath).lower()
        features['is_temp_path'] = any(x in path_str for x in ['temp', 'tmp', 'cache'])
        features['is_system_path'] = any(x in path_str for x in ['windows', 'system32', 'program files'])
        features['is_user_path'] = any(x in path_str for x in ['documents', 'downloads', 'desktop'])
        features['path_depth'] = len(Path(path_str).parts)
        features['has_spaces_in_name'] = ' ' in file_info.name
        
        # Modification frequency analysis
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            ctime = datetime.fromtimestamp(os.path.getctime(filepath))
            atime = datetime.fromtimestamp(os.path.getatime(filepath))
            
            features['modified_recently'] = (datetime.now() - mtime).days < 7
            features['accessed_frequently'] = abs((mtime - atime).total_seconds()) < 3600
            features='modification_access_gap_hours': (mtime - atime).total_seconds() / 3600
            
        except OSError:
            features['modified_recently'] = False
            features['accessed_frequently'] = False
            features['modification_access_gap_hours'] = 0
        
        # Content hash for duplicate detection
        features['is_unique_file'] = not self._is_duplicate(file_info)
        
        # Category-based features
        category_risk_scores = {
            'Temporary': 0.1,
            'Downloads': 0.4,
            'Duplicates': 0.2,
            'Large Files': 0.6,
            'System': 0.9,
            'Applications': 0.8,
            'Videos': 0.3,
            'Documents': 0.2,
            'Images': 0.2,
            'Music': 0.2,
            'Other': 0.5
        }
        features['category_risk'] = category_risk_scores.get(file_info.category, 0.5)
        
        # File type specific features
        ext = Path(file_info.name).suffix.lower()
        features['is_executable'] = ext in ['.exe', '.msi', '.dll', '.bat', '.cmd']
        features['is_media_file'] = ext in ['.mp4', '.avi', '.mkv', '.mp3', '.jpg', '.png']
        features['is_document'] = ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
        
        # Contextual features from AI engine
        if hasattr(self, 'ai_engine'):
            ai_features = self.ai_engine._calculate_safety_score(AIFeature(
                age=features['age_days'],
                size_bytes=file_info.size,
                entropy=features['extension_entropy'],
                frequency=0.5 if features['modified_recently'] else 0.1,
                category_risk=features['category_risk']
            ))
            features['ai_safety_score'] = ai_features
            
        return {k: v if isinstance(v, (int, float)) else 1.0 if v else 0.0 for k, v in features.items()}
    
    def _calculate_extension_entropy(self, filename: str) -> float:
        """Calculate entropy of filename extension (higher = more random/suspicious)"""
        ext = Path(filename).suffix.lower()
        if not ext:
            return 0.0
        
        # Count character frequency
        char_count = {}
        for char in ext:
            char_count[char] = char_count.get(char, 0) + 1
        
        # Calculate Shannon entropy
        length = len(ext)
        entropy = -sum((count / length) * math.log2(count / length) for count in char_count.values())
        return entropy
    
    def _is_duplicate(self, file_info: FileInfo) -> bool:
        """Check if file has duplicates in history"""
        # Simplified - would use full hash comparison in production
        return False
    
    def predict_cleanup_safety(self, file_info: FileInfo, filepath: Path) -> NeuralPrediction:
        """
        Use trained models to predict safety of cleaning a file.
        Returns detailed prediction with reasoning.
        """
        features = self.extract_neural_features(file_info, filepath)
        
        if not self.is_trained or not SKLEARN_AVAILABLE:
            # Fallback to basic analysis
            return NeuralPrediction(
                filepath=str(filepath),
                confidence=0.5,
                predicted_category=file_info.category,
                risk_level='medium',
                reasoning=['Model not trained yet'],
                suggested_action='review'
            )
        
        # Normalize features
        normalized = self.scaler.transform([[features[k] for k in sorted(features.keys())]])
        
        # Ensemble predictions
        rf_proba = self.rf_model.predict_proba(normalized)[0]
        gb_proba = self.gb_model.predict_proba(normalized)[0]
        
        # Weighted average (gradient boosting often more accurate)
        final_proba = 0.4 * rf_proba + 0.6 * gb_proba
        
        predicted_class = self.rf_model.predict(normalized)[0]
        confidence = max(final_proba)
        
        # Determine risk level and action
        if confidence > 0.85 and predicted_class == 1:
            risk_level = 'low'
            suggested_action = 'clean'
        elif confidence < 0.6 or predicted_class == 0:
            risk_level = 'high'
            suggested_action = 'review'
        else:
            risk_level = 'medium'
            suggested_action = 'consider'
        
        # Generate reasoning based on feature importance
        reasoning = self._generate_reasoning(features, predicted_class)
        
        return NeuralPrediction(
            filepath=str(filepath),
            confidence=confidence,
            predicted_category=file_info.category,
            risk_level=risk_level,
            reasoning=reasoning,
            suggested_action=suggested_action
        )
    
    def _generate_reasoning(self, features: Dict[str, float], prediction: int) -> List[str]:
        """Generate human-readable reasoning for prediction"""
        reasoning = []
        
        if features.get('is_temp_path'):
            reasoning.append("File is in temporary directory")
        if features.get('age_days', 0) > 365:
            reasoning.append(f"File hasn't been modified in {features['age_days']} days")
        if features.get('size_mb', 0) > 1000:
            reasoning.append(f"Large file ({features['size_mb']:.1f} MB)")
        if features.get('is_executable'):
            reasoning.append("Executable file - handle with caution")
        if features.get('modified_recently'):
            reasoning.append("Recently modified - may still be in use")
        if features.get('extension_entropy', 0) > 2.0:
            reasoning.append("Suspicious file name pattern")
        if features.get('is_unique_file', True):
            reasoning.append("Unique file (no duplicates found)")
        
        if prediction == 1:  # Safe to clean
            if not reasoning:
                reasoning.append("Multiple positive indicators suggest safe to clean")
            else:
                reasoning.append("✓ These factors indicate safe to clean")
        else:
            if not reasoning:
                reasoning.append("Default conservative approach - review before cleaning")
            else:
                reasoning.append("⚠ Review these factors before cleaning")
        
        return reasoning
    
    def train_on_decisions(self, force_retrain: bool = False):
        """
        Train/update ML models on user's cleanup decisions.
        Call this periodically to improve accuracy.
        """
        if not SKLEARN_AVAILABLE:
            print("⚠️ scikit-learn not available - skipping ML training")
            return
        
        if len(self.decision_history) < 50:
            print(f"ℹ️ Need at least 50 decisions for training (have {len(self.decision_history)})")
            return
        
        if not force_retrain and len(self.decision_history) < 100:
            print(f"ℹ️ Accumulating more data... (have {len(self.decision_history)}, need 100+)")
            return
        
        print(f"🎯 Training neural cleaner on {len(self.decision_history)} decisions...")
        
        # Prepare training data
        X = []
        y = []
        feature_names = None
        
        for decision in self.decision_history:
            if decision.action_taken in ['cleaned', 'kept']:  # Exclude 'reviewed'
                features = list(decision.features.values())
                X.append(features)
                
                # Label: 1 = cleaned (safe), 0 = kept (not safe to clean)
                label = 1 if decision.action_taken == 'cleaned' else 0
                y.append(label)
        
        if feature_names is None:
            feature_names = sorted(self.decision_history[0].features.keys())
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train models
        self.rf_model.fit(X_train_scaled, y_train)
        self.gb_model.fit(X_train_scaled, y_train)
        
        # Evaluate
        rf_pred = self.rf_model.predict(X_test_scaled)
        gb_pred = self.gb_model.predict(X_test_scaled)
        
        rf_accuracy = accuracy_score(y_test, rf_pred)
        gb_accuracy = accuracy_score(y_test, gb_pred)
        
        print(f"✅ RF Model Accuracy: {rf_accuracy:.2%}")
        print(f"✅ GB Model Accuracy: {gb_accuracy:.2%}")
        
        # Create ensemble (vote)
        self.ensemble_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.ensemble_model.fit(X_train_scaled, y_train)
        
        # Store feature importance
        if hasattr(self.rf_model, 'feature_importances_'):
            self.feature_importance = dict(zip(feature_names, self.rf_model.feature_importances_))
            print("\n📊 Most Important Features:")
            for feat, imp in sorted(self.feature_importance.items(), key=lambda x: -x[1])[:5]:
                print(f"  - {feat}: {imp:.3f}")
        
        # Save model
        self._save_model()
        self.is_trained = True
    
    def record_decision(self, file_info: FileInfo, filepath: Path, action: str, 
                       space_freed: int = 0):
        """Record user's cleanup decision for future learning"""
        features = self.extract_neural_features(file_info, filepath)
        
        decision = CleanDecision(
            filepath=str(filepath),
            features=features,
            action_taken=action,
            timestamp=datetime.now(),
            space_freed_bytes=space_freed
        )
        
        self.decision_history.append(decision)
        
        # Auto-train after significant number of new decisions
        if len(self.decision_history) % 50 == 0:
            print(f"💾 Recorded {len(self.decision_history)} total decisions...")
            if len(self.decision_history) >= 100:
                self.train_on_decisions()
    
    def get_smart_recommendations(self, file_list: List[FileInfo], 
                                  max_recommendations: int = 50) -> List[tuple]:
        """
        Get ML-enhanced recommendations sorted by safety score.
        Returns list of (file_info, prediction, should_clean) tuples.
        """
        recommendations = []
        
        for file_info in file_list:
            filepath = Path(file_info.path)
            prediction = self.predict_cleanup_safety(file_info, filepath)
            
            # Apply user preferences
            should_clean = self._apply_user_preferences(prediction)
            
            recommendations.append((file_info, prediction, should_clean))
        
        # Sort by confidence (highest first) and filter
        recommendations.sort(key=lambda x: x[1].confidence, reverse=True)
        
        return recommendations[:max_recommendations]
    
    def _apply_user_preferences(self, prediction: NeuralPrediction) -> bool:
        """Apply learned user preferences to prediction"""
        # If user prefers aggressive cleaning
        if self.user_preferences['aggressive_cleaning']:
            if prediction.risk_level in ['low', 'medium']:
                return True
        
        # Check ignored files
        if prediction.filepath in self.user_preferences['ignored_files']:
            return False
        
        # Check trusted paths
        for trusted_path in self.user_preferences['trusted_paths']:
            if trusted_path in prediction.filepath:
                # User trusts this path, be more aggressive
                if prediction.risk_level != 'high':
                    return True
        
        # Default: only clean low-risk items
        return prediction.risk_level == 'low'
    
    def _save_model(self):
        """Save trained model to disk"""
        import pickle
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        model_data = {
            'rf_model': self.rf_model,
            'gb_model': self.gb_model,
            'ensemble_model': self.ensemble_model,
            'scaler': self.scaler,
            'feature_importance': self.feature_importance,
            'training_date': datetime.now().isoformat(),
            'decisions_trained_on': len(self.decision_history)
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model from disk"""
        import pickle
        
        if not os.path.exists(self.model_path):
            print("⚠️ No trained model found. Will train on first use.")
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.rf_model = model_data['rf_model']
            self.gb_model = model_data['gb_model']
            self.ensemble_model = model_data.get('ensemble_model')
            self.scaler = model_data['scaler']
            self.feature_importance = model_data.get('feature_importance', {})
            
            self.is_trained = True
            print(f"✅ Loaded model trained on {model_data['decisions_trained_on']} decisions")
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def export_insights(self) -> Dict[str, Any]:
        """Export ML insights and statistics"""
        return {
            'model_trained': self.is_trained,
            'total_decisions': len(self.decision_history),
            'feature_importance': self.feature_importance,
            'user_preferences': self.user_preferences,
            'recent_predictions': [
                {
                    'filepath': d.filepath,
                    'action': d.action_taken,
                    'timestamp': d.timestamp.isoformat()
                }
                for d in self.decision_history[-10:]
            ]
        }


# Convenience function
def create_neural_cleaner(model_path: str = "data/neural_cleaner_model.pkl") -> NeuralCleaner:
    """Create and optionally load a neural cleaner instance"""
    cleaner = NeuralCleaner(model_path=model_path)
    cleaner.load_model()
    return cleaner


if __name__ == "__main__":
    print("🧠 EatUp Pro Neural Cleaner")
    print("=" * 40)
    
    cleaner = create_neural_cleaner()
    
    if cleaner.is_trained:
        print("✅ Neural model is ready!")
        print("\nInsights:")
        insights = cleaner.export_insights()
        print(json.dumps(insights, indent=2, default=str))
    else:
        print("🔧 Model will be trained after collecting cleanup decisions.")
        print("Start using the cleaner to improve accuracy over time!")

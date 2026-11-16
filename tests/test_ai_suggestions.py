import os
import time

from ai_suggestions import AIFeature, AISuggestionEngine


def feature(**kwargs):
    defaults = dict(
        file_age_days=400,
        file_size_mb=5,
        ext_entropy=1.0,
        path_depth=3,
        access_frequency=0.0,
        is_temp_like=True,
        category_risk=0.1,
    )
    defaults.update(kwargs)
    return AIFeature(**defaults)


def test_score_is_normalised_and_delete_is_reachable():
    engine = AISuggestionEngine()
    features = feature()
    score = engine._calculate_safety_score(features)
    assert 0.0 <= score <= 1.0
    assert score > 0.8  # the old average-by-count could never exceed ~0.435

    rec = engine._generate_recommendation(score, features)
    assert rec.action == 'delete'
    assert rec.risk_level == 'safe'


def test_high_scoring_user_document_is_only_reviewed():
    engine = AISuggestionEngine()
    features = feature(is_temp_like=False, category_risk=0.6)
    score = engine._calculate_safety_score(features)
    assert score > 0.8

    rec = engine._generate_recommendation(score, features)
    assert rec.action == 'review'
    assert rec.risk_level == 'risky'


def test_protected_file_is_never_a_delete_candidate():
    engine = AISuggestionEngine()
    features = feature(is_temp_like=False, category_risk=0.9, ext_entropy=1.0)
    rec = engine._generate_recommendation(engine._calculate_safety_score(features), features)
    assert rec.action != 'delete'


def test_feedback_threshold_is_used():
    engine = AISuggestionEngine()
    engine.model_weights['review_threshold'] = 0.4
    features = feature(is_temp_like=False, category_risk=0.6, access_frequency=0.9)
    rec = engine._generate_recommendation(0.45, features)
    assert rec.action == 'review'


def test_prediction_without_history_says_unavailable():
    engine = AISuggestionEngine()
    summary = engine.get_prediction_summary({'data_points': 1})
    assert summary['available'] is False
    assert summary['success_rate'] is None
    assert 'average_daily_growth_mb' not in summary  # no invented growth figure


def test_prediction_uses_supplied_trends():
    engine = AISuggestionEngine()
    summary = engine.get_prediction_summary(
        {'data_points': 5, 'daily_growth_mb': 100, 'trend_direction': 'increasing'},
        available_bytes=10 * 1024 ** 3,
    )
    assert summary['available'] is True
    assert summary['average_daily_growth_mb'] == 100
    assert summary['risk_assessment'] == 'moderate'
    assert 'predicted_full_date' in summary


def test_analyze_file_for_safety_uses_real_stats(tmp_path):
    path = tmp_path / 'old.tmp'
    path.write_bytes(b'x' * 1024)
    old = time.time() - 400 * 86400
    os.utime(path, (old, old))

    result = AISuggestionEngine().analyze_file_for_safety(str(path), {'size': path.stat().st_size})
    assert 0.0 <= result['safety_score'] <= 1.0
    assert result['recommendation'].action == 'delete'

"""
Tests for AI Gameplay Coach (coach_utils.py, coach_orchestrator.py)

Tests cover:
- Retriever: Game history context extraction
- Analyzer: Pattern detection accuracy
- Evaluator: Coaching quality scoring
- Logger: Event logging
- Orchestrator: End-to-end coaching flow
"""

import pytest
import json
from src.coach_utils import (
    GameRetriever,
    StrategyAnalyzer,
    CoachingQualityEvaluator,
    CoachEventLogger,
)
from coach_orchestrator import GameplayCoach, reset_coach


class TestGameRetriever:
    """Tests for game history retrieval (RAG component)."""
    
    def test_get_game_context_basic(self):
        """Test basic context retrieval."""
        context = GameRetriever.get_game_context(
            history=[15, 20, 25],
            difficulty="Easy",
            attempts=3,
            attempt_limit=10,
            range_low=1,
            range_high=20
        )
        
        assert context["game_state"]["difficulty"] == "Easy"
        assert context["guess_count"] == 3
        assert context["game_state"]["attempts_used"] == 3
        assert context["game_state"]["attempts_remaining"] == 7
    
    def test_get_game_context_empty_history(self):
        """Test context with no guesses yet."""
        context = GameRetriever.get_game_context(
            history=[],
            difficulty="Medium",
            attempts=0,
            attempt_limit=7,
            range_low=1,
            range_high=50
        )
        
        assert context["guess_count"] == 0
        assert context["guess_spread"] is None
    
    def test_format_context_for_prompt(self):
        """Test formatting context as readable text."""
        context = GameRetriever.get_game_context(
            history=[25, 35, 30],
            difficulty="Medium",
            attempts=3,
            attempt_limit=7,
            range_low=1,
            range_high=50
        )
        
        formatted = GameRetriever.format_context_for_prompt(context)
        
        assert "Medium" in formatted
        assert "25, 35, 30" in formatted
        assert "3 guesses so far" in formatted.replace("\n", " ").replace("  ", " ")


class TestStrategyAnalyzer:
    """Tests for pattern detection in guessing strategies."""
    
    def test_detect_binary_search_pattern(self):
        """Test detection of binary search strategy."""
        # Binary search: starts at midpoint (25 for 1-50 range)
        history = [25, 38, 31, 28]
        patterns = StrategyAnalyzer.detect_patterns(history, 1, 50)
        
        assert patterns["is_binary_search"] is True
    
    def test_detect_random_walk_pattern(self):
        """Test detection of random/scattered guessing."""
        # Random jumps: 5, 45, 10, 49 (high variance)
        history = [5, 45, 10, 49]
        patterns = StrategyAnalyzer.detect_patterns(history, 1, 50)
        
        assert patterns["is_random"] is True
    
    def test_detect_clustering_pattern(self):
        """Test detection of clustering strategy."""
        # All guesses in narrow range 20-30
        history = [22, 25, 27, 24]
        patterns = StrategyAnalyzer.detect_patterns(history, 1, 50)
        
        assert patterns["is_clustering"] is True
    
    def test_convergence_quality_improves(self):
        """Test that convergence improves with better strategy."""
        # Poor convergence: scattered guesses
        poor_history = [5, 45, 10, 50]
        poor_patterns = StrategyAnalyzer.detect_patterns(poor_history, 1, 50)
        
        # Good convergence: narrowing range
        good_history = [25, 35, 30, 32]
        good_patterns = StrategyAnalyzer.detect_patterns(good_history, 1, 50)
        
        assert good_patterns["convergence_quality"] > poor_patterns["convergence_quality"]
    
    def test_pattern_description_output(self):
        """Test human-readable pattern descriptions."""
        patterns = {
            "is_binary_search": True,
            "is_random": False,
            "is_clustering": False,
            "is_systematic": False,
            "convergence_quality": 0.9,
        }
        
        description = StrategyAnalyzer.get_pattern_description(patterns)
        
        assert "binary search" in description.lower()
        assert "efficient" in description.lower() or "🔥" in description


class TestCoachingQualityEvaluator:
    """Tests for coaching quality scoring and validation."""
    
    def test_specific_suggestion_scores_higher(self):
        """Test that specific advice scores higher than generic."""
        generic = "Great job! Keep trying!"
        specific = "You're clustering around 20-30. Try guessing 40 next to explore the upper half."
        
        score_generic = CoachingQualityEvaluator.score_suggestion(
            generic, [], 0.5
        )
        score_specific = CoachingQualityEvaluator.score_suggestion(
            specific, [], 0.5
        )
        
        assert score_specific > score_generic
    
    def test_repetition_heavily_penalized(self):
        """Test that repeated suggestions are heavily penalized."""
        suggestion = "Try using binary search strategy."
        previous = [suggestion]
        
        score_new = CoachingQualityEvaluator.score_suggestion(
            suggestion, [], 0.5
        )
        score_repeated = CoachingQualityEvaluator.score_suggestion(
            suggestion, previous, 0.5
        )
        
        assert score_repeated < score_new * 0.5  # Heavily penalized
    
    def test_actionable_keywords_boost_score(self):
        """Test that actionable keywords increase score."""
        base = "Your strategy is okay."
        actionable = "Your strategy is okay. Try narrowing your range by focusing on the midpoint."
        
        score_base = CoachingQualityEvaluator.score_suggestion(base, [], 0.5)
        score_actionable = CoachingQualityEvaluator.score_suggestion(actionable, [], 0.5)
        
        assert score_actionable > score_base
    
    def test_acceptance_threshold(self):
        """Test quality threshold for suggestion acceptance."""
        high_quality = 75.0
        low_quality = 45.0
        
        assert CoachingQualityEvaluator.is_suggestion_acceptable(high_quality, threshold=60.0)
        assert not CoachingQualityEvaluator.is_suggestion_acceptable(low_quality, threshold=60.0)


class TestCoachEventLogger:
    """Tests for event logging and retrieval."""
    
    def test_log_coaching_event(self):
        """Test logging a coaching event."""
        logger = CoachEventLogger()
        
        # This should not raise an error
        logger.log_coaching_event(
            event_type="coaching_generated",
            guess_number=1,
            difficulty="Easy",
            data={"suggestion": "Try binary search"}
        )
    
    def test_get_session_stats(self):
        """Test retrieving session statistics."""
        logger = CoachEventLogger()
        stats = logger.get_session_stats()
        
        # Should return dict even if no events
        assert isinstance(stats, dict)
        assert "total_coaching_events" in stats or "message" in stats


class TestGameplayCoach:
    """Integration tests for the full coaching system."""
    
    def test_coach_initialization(self):
        """Test coach initialization without Claude (fallback mode)."""
        reset_coach()
        coach = GameplayCoach(enable_claude=False)
        
        assert coach is not None
        assert coach.suggestion_history == []
    
    def test_get_coaching_with_fallback(self):
        """Test getting coaching in fallback mode (no Claude)."""
        coach = GameplayCoach(enable_claude=False)
        
        coaching = coach.get_coaching(
            history=[25, 30],
            difficulty="Medium",
            attempts=2,
            attempt_limit=7,
            range_low=1,
            range_high=50,
            current_guess=30,
            outcome="Too High"
        )
        
        assert "suggestion" in coaching
        assert "quality_score" in coaching
        assert "patterns" in coaching
        assert coaching["method"] == "fallback"
        assert coaching["suggestion"]  # Should have some suggestion
    
    def test_suggestion_history_tracking(self):
        """Test that coach tracks suggestion history."""
        coach = GameplayCoach(enable_claude=False)
        
        # First coaching
        coaching1 = coach.get_coaching(
            history=[25],
            difficulty="Easy",
            attempts=1,
            attempt_limit=10,
            range_low=1,
            range_high=20,
            current_guess=25,
            outcome="Too High"
        )
        
        # Second coaching
        coaching2 = coach.get_coaching(
            history=[25, 12],
            difficulty="Easy",
            attempts=2,
            attempt_limit=10,
            range_low=1,
            range_high=20,
            current_guess=12,
            outcome="Too Low"
        )
        
        assert len(coach.suggestion_history) == 2
        # Second suggestion should be different from first (no repetition)
        # Note: This might not always be true for fallback, but intent is clear
    
    def test_session_summary(self):
        """Test getting session summary."""
        coach = GameplayCoach(enable_claude=False)
        
        coach.get_coaching(
            history=[25],
            difficulty="Easy",
            attempts=1,
            attempt_limit=10,
            range_low=1,
            range_high=20,
            current_guess=25,
            outcome="Too High"
        )
        
        summary = coach.get_session_summary()
        
        assert "total_suggestions" in summary
        assert summary["total_suggestions"] == 1


class TestIntegration:
    """End-to-end integration tests."""
    
    def test_full_game_coaching_flow(self):
        """Test a complete game session with coaching."""
        coach = GameplayCoach(enable_claude=False)
        
        # Simulate a 3-guess game
        guesses = [25, 12, 18]
        outcomes = ["Too High", "Too Low", "Win"]
        
        for i, (guess, outcome) in enumerate(zip(guesses, outcomes)):
            history = guesses[:i+1]
            coaching = coach.get_coaching(
                history=history,
                difficulty="Easy",
                attempts=i+1,
                attempt_limit=10,
                range_low=1,
                range_high=20,
                current_guess=guess,
                outcome=outcome
            )
            
            # Verify coaching structure
            assert isinstance(coaching, dict)
            assert "suggestion" in coaching
            assert "quality_score" in coaching
            assert 0 <= coaching["quality_score"] <= 100
    
    def test_strategy_improves_with_coaching(self):
        """Test that detected strategy quality improves."""
        coach = GameplayCoach(enable_claude=False)
        
        # Poor strategy: random guesses
        poor_guesses = [5, 50, 3, 47]
        coaching_poor = coach.get_coaching(
            history=poor_guesses,
            difficulty="Easy",
            attempts=4,
            attempt_limit=10,
            range_low=1,
            range_high=20,
            current_guess=47,
            outcome="Too Low"
        )
        poor_convergence = coaching_poor["patterns"]["convergence_quality"]
        
        # Reset coach
        reset_coach()
        coach = GameplayCoach(enable_claude=False)
        
        # Better strategy: binary search
        good_guesses = [10, 15, 18, 17]
        coaching_good = coach.get_coaching(
            history=good_guesses,
            difficulty="Easy",
            attempts=4,
            attempt_limit=10,
            range_low=1,
            range_high=20,
            current_guess=17,
            outcome="Win"
        )
        good_convergence = coaching_good["patterns"]["convergence_quality"]
        
        assert good_convergence > poor_convergence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Coach Orchestrator - Main interface for AI Gameplay Coach

Coordinates:
- Retriever (get history)
- Analyzer (detect patterns)
- Claude client (generate coaching)
- Evaluator (score quality)
- Logger (track events)
"""

import logging
from typing import Dict, Optional, Tuple
from src.coach_utils import (
    GameRetriever,
    StrategyAnalyzer,
    CoachingQualityEvaluator,
    CoachEventLogger
)
from claude_integration import ClaudeCoachClient, get_coach_client

logger = logging.getLogger(__name__)


class GameplayCoach:
    """
    Main AI Gameplay Coach that orchestrates the RAG system.
    
    Flow:
    1. Retrieve game history context
    2. Analyze patterns in strategy
    3. Generate coaching via Claude (with context)
    4. Evaluate coaching quality
    5. Log the interaction
    6. Return coaching to player
    """
    
    def __init__(self, enable_claude: bool = True):
        """
        Initialize the coach.
        
        Args:
            enable_claude: Whether to use Claude API (False = use fallback only)
        """
        self.retriever = GameRetriever()
        self.analyzer = StrategyAnalyzer()
        self.evaluator = CoachingQualityEvaluator()
        self.logger = CoachEventLogger()
        
        # Initialize Claude client
        self.claude_client = None
        if enable_claude:
            self.claude_client = get_coach_client()
        
        # Session state tracking
        self.suggestion_history = []
        self.previous_patterns = None
        
        logger.info("Gameplay Coach initialized")
    
    def get_coaching(
        self,
        history: list,
        difficulty: str,
        attempts: int,
        attempt_limit: int,
        range_low: int,
        range_high: int,
        current_guess: int,
        outcome: str
    ) -> Dict:
        """
        Generate coaching for a player after their guess.
        
        Args:
            history: List of all guesses so far (including current)
            difficulty: Current difficulty level
            attempts: Number of attempts used
            attempt_limit: Max attempts allowed
            range_low: Range minimum
            range_high: Range maximum
            current_guess: The guess just made
            outcome: Result (e.g., "Too High", "Too Low", "Win")
            
        Returns:
            Dictionary with coaching data:
            {
                "suggestion": str,
                "quality_score": float (0-100),
                "patterns": dict,
                "method": "claude" | "fallback",
                "error": str or None
            }
        """
        # Step 1: Retrieve context (RAG)
        game_context = self.retriever.get_game_context(
            history=history[:-1] if history else [],  # Exclude current guess
            difficulty=difficulty,
            attempts=attempts,
            attempt_limit=attempt_limit,
            range_low=range_low,
            range_high=range_high
        )
        context_text = self.retriever.format_context_for_prompt(game_context)
        
        # Step 2: Analyze patterns
        patterns = self.analyzer.detect_patterns(
            history=history[:-1] if history else [],
            range_low=range_low,
            range_high=range_high
        )
        pattern_description = self.analyzer.get_pattern_description(patterns)
        
        # Step 3: Generate coaching
        if self.claude_client:
            suggestion, api_error = self.claude_client.get_coaching_advice(
                game_context=context_text,
                patterns=patterns,
                previous_suggestions=self.suggestion_history
            )
            
            if suggestion:
                method = "claude"
            else:
                # Fallback to pattern-based coaching
                suggestion = self.claude_client.get_fallback_coaching(patterns)
                method = "fallback"
                logger.warning(f"Claude failed, using fallback: {api_error}")
        else:
            # No Claude available, use fallback
            suggestion = ClaudeCoachClient.get_fallback_coaching(patterns)
            method = "fallback"
            api_error = "Claude client not initialized"
        
        # Step 4: Evaluate quality
        quality_score = self.evaluator.score_suggestion(
            suggestion=suggestion,
            previous_suggestions=self.suggestion_history,
            pattern_quality=patterns.get("convergence_quality", 0.5)
        )
        
        # Only use suggestion if it meets quality threshold
        is_acceptable = self.evaluator.is_suggestion_acceptable(quality_score)
        
        if not is_acceptable:
            # If quality is poor, use fallback instead
            suggestion = self.claude_client.get_fallback_coaching(patterns) \
                if self.claude_client else self._get_safe_coaching(patterns)
            method = "fallback"
            quality_score = 75.0  # Fallback gets safe score
        
        # Step 5: Log the event
        self.logger.log_coaching_event(
            event_type="coaching_generated",
            guess_number=attempts,
            difficulty=difficulty,
            data={
                "guess": current_guess,
                "outcome": outcome,
                "method": method,
                "quality_score": quality_score,
                "patterns": patterns,
                "suggestion": suggestion[:100]  # Log first 100 chars
            }
        )
        
        # Step 6: Update session history
        self.suggestion_history.append(suggestion)
        self.previous_patterns = patterns
        
        # Return coaching package
        return {
            "suggestion": suggestion,
            "quality_score": quality_score,
            "patterns": patterns,
            "pattern_description": pattern_description,
            "method": method,
            "error": api_error if method == "fallback" else None
        }
    
    def get_session_summary(self) -> Dict:
        """Get summary of coaching for the current session."""
        stats = self.logger.get_session_stats()
        return {
            "total_suggestions": len(self.suggestion_history),
            "coaching_events": stats,
            "last_patterns": self.previous_patterns
        }
    
    def _get_safe_coaching(self, patterns: dict) -> str:
        """Fallback coaching when Claude and pattern detection fail."""
        return "💡 Keep analyzing the hints and narrowing your search range!"


# Singleton coach instance for Streamlit
_coach_instance = None


def get_gameplay_coach(enable_claude: bool = True) -> GameplayCoach:
    """
    Get or create the global coach instance (Streamlit singleton).
    
    Args:
        enable_claude: Whether to enable Claude
        
    Returns:
        GameplayCoach instance
    """
    global _coach_instance
    if _coach_instance is None:
        _coach_instance = GameplayCoach(enable_claude=enable_claude)
    return _coach_instance


def reset_coach() -> None:
    """Reset the coach instance (useful for testing)."""
    global _coach_instance
    _coach_instance = None

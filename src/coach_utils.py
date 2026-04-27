"""
Coach Utilities for AI Gameplay Coach (RAG System)

This module provides:
- Retriever: Extracts game history context for RAG
- Analyzer: Detects patterns in guessing strategies
- Evaluator: Scores coaching quality and reliability
- Logger: Tracks all AI decisions for testing/debugging
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coach_events.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GameRetriever:
    """Retrieves game history and formats it for RAG context."""
    
    @staticmethod
    def get_game_context(
        history: List[int],
        difficulty: str,
        attempts: int,
        attempt_limit: int,
        range_low: int,
        range_high: int
    ) -> Dict:
        """
        Retrieve game context for AI coach analysis.
        
        Args:
            history: List of guesses made (in order)
            difficulty: Current difficulty level
            attempts: Number of attempts used
            attempt_limit: Maximum attempts allowed
            range_low: Minimum range value
            range_high: Maximum range value
            
        Returns:
            Dictionary with formatted context for LLM
        """
        context = {
            "game_state": {
                "difficulty": difficulty,
                "range": f"{range_low}-{range_high}",
                "attempts_used": attempts,
                "attempts_limit": attempt_limit,
                "attempts_remaining": attempt_limit - attempts,
            },
            "guess_history": history,
            "guess_count": len(history),
            "guess_spread": _calculate_spread(history) if history else None,
            "first_half_avg": _calculate_first_half_avg(history, range_low, range_high),
        }
        
        logger.info(f"Retrieved context: {context['game_state']}")
        return context
    
    @staticmethod
    def format_context_for_prompt(context: Dict) -> str:
        """
        Format retrieved context as readable text for Claude.
        
        Args:
            context: Retrieved game context
            
        Returns:
            Formatted string for inclusion in prompt
        """
        hist = context["guess_history"]
        state = context["game_state"]
        
        formatted = f"""
GAME STATE:
- Difficulty: {state['difficulty']}
- Range: {state['range']}
- Attempts: {state['attempts_used']}/{state['attempts_limit']} ({state['attempts_remaining']} remaining)

GUESS HISTORY ({len(hist)} guesses so far):
{', '.join(map(str, hist)) if hist else 'No guesses yet'}

STRATEGY ANALYSIS:
- Guess spread: {context['guess_spread']}
- First/Second half balance: {context['first_half_avg']}
"""
        return formatted


def _calculate_spread(history: List[int]) -> str:
    """Calculate how spread out the guesses are."""
    if not history:
        return "No guesses"
    if len(history) == 1:
        return "Single guess"
    
    min_guess = min(history)
    max_guess = max(history)
    spread = max_guess - min_guess
    return f"{spread} (min: {min_guess}, max: {max_guess})"


def _calculate_first_half_avg(
    history: List[int],
    range_low: int,
    range_high: int
) -> str:
    """Analyze if guesses are clustered in first or second half of range."""
    if not history:
        return "N/A"
    
    midpoint = (range_low + range_high) // 2
    first_half = sum(1 for g in history if g <= midpoint)
    second_half = len(history) - first_half
    
    if first_half > second_half:
        return f"Favoring lower half ({first_half}/{len(history)})"
    elif second_half > first_half:
        return f"Favoring upper half ({second_half}/{len(history)})"
    else:
        return "Balanced split"


class StrategyAnalyzer:
    """Analyzes guessing patterns and strategy quality."""
    
    @staticmethod
    def detect_patterns(history: List[int], range_low: int, range_high: int) -> Dict:
        """
        Detect key patterns in guessing strategy.
        
        Args:
            history: List of guesses
            range_low: Minimum range
            range_high: Maximum range
            
        Returns:
            Dictionary with detected patterns
        """
        patterns = {
            "is_binary_search": _is_binary_search(history, range_low, range_high),
            "is_random": _is_random_walk(history),
            "is_clustering": _is_clustering(history),
            "is_systematic": _is_systematic(history),
            "convergence_quality": _measure_convergence(history, range_low, range_high),
        }
        
        logger.info(f"Detected patterns: {patterns}")
        return patterns
    
    @staticmethod
    def get_pattern_description(patterns: Dict) -> str:
        """
        Generate human-readable description of detected patterns.
        
        Args:
            patterns: Dictionary of detected patterns
            
        Returns:
            Descriptive string
        """
        descriptions = []
        
        if patterns["is_binary_search"]:
            descriptions.append("✅ Excellent binary search technique")
        elif patterns["is_systematic"]:
            descriptions.append("📊 Using a systematic approach")
        elif patterns["is_clustering"]:
            descriptions.append("🎯 Guesses clustered in a region")
        elif patterns["is_random"]:
            descriptions.append("🎲 Exploratory/scattered approach")
        
        convergence = patterns["convergence_quality"]
        if convergence > 0.8:
            descriptions.append("🔥 Converging efficiently")
        elif convergence > 0.5:
            descriptions.append("📈 Improving convergence")
        
        return " | ".join(descriptions) if descriptions else "Analyzing strategy..."


def _is_binary_search(history: List[int], range_low: int, range_high: int) -> bool:
    """Check if guesses follow binary search pattern."""
    if len(history) < 2:
        return False
    
    # Binary search should pick midpoint-ish and then halve ranges
    midpoint = (range_low + range_high) / 2
    first_guess = history[0]
    
    # First guess should be close to midpoint
    if abs(first_guess - midpoint) > (range_high - range_low) * 0.2:
        return False
    
    # Check if subsequent guesses follow halving pattern
    for i in range(1, min(3, len(history))):
        # Simple heuristic: each guess should be roughly half the range away
        pass  # Simplified for now
    
    return len(history) >= 2 and abs(first_guess - midpoint) < (range_high - range_low) * 0.1


def _is_random_walk(history: List[int]) -> bool:
    """Check if guesses are scattered/random."""
    if len(history) < 3:
        return False
    
    # Random walk: big jumps between guesses, no clear pattern
    jumps = [abs(history[i+1] - history[i]) for i in range(len(history)-1)]
    avg_jump = sum(jumps) / len(jumps)
    return avg_jump > 10  # High variation between guesses


def _is_clustering(history: List[int]) -> bool:
    """Check if guesses cluster around a region."""
    if len(history) < 3:
        return False
    
    range_span = max(history) - min(history)
    return range_span < 25  # All guesses within small range


def _is_systematic(history: List[int]) -> bool:
    """Check if guesses follow a systematic progression."""
    if len(history) < 3:
        return False
    
    # Systematic: consistent direction or narrowing pattern
    differences = [history[i+1] - history[i] for i in range(len(history)-1)]
    same_direction = all(d > 0 for d in differences) or all(d < 0 for d in differences)
    return same_direction


def _measure_convergence(history: List[int], range_low: int, range_high: int) -> float:
    """
    Measure how efficiently guesses are converging to the target.
    Returns 0-1 score.
    """
    if len(history) < 2:
        return 0.0
    
    total_range = range_high - range_low
    first_span = total_range  # Start with full range
    last_span = max(history) - min(history)
    
    if first_span == 0:
        return 0.0
    
    convergence = 1.0 - (last_span / first_span)
    return max(0.0, min(1.0, convergence))  # Clamp 0-1


class CoachingQualityEvaluator:
    """Evaluates quality and reliability of AI coaching suggestions."""
    
    @staticmethod
    def score_suggestion(
        suggestion: str,
        previous_suggestions: List[str],
        pattern_quality: float
    ) -> float:
        """
        Score AI coaching suggestion (0-100).
        Higher = more valuable, specific, actionable.
        
        Args:
            suggestion: The coaching suggestion text
            previous_suggestions: List of prior suggestions (check for repetition)
            pattern_quality: 0-1 quality of detected patterns
            
        Returns:
            0-100 quality score
        """
        score = 50.0  # Base score
        
        # Check specificity (not generic)
        generic_phrases = [
            "great job",
            "keep trying",
            "good luck",
            "you can do it"
        ]
        suggestion_lower = suggestion.lower()
        generic_count = sum(1 for phrase in generic_phrases if phrase in suggestion_lower)
        score -= generic_count * 15
        
        # Check for actionable advice
        actionable_keywords = [
            "try", "consider", "focus on", "next", "narrow",
            "binary", "midpoint", "range", "strategy"
        ]
        actionable_count = sum(1 for keyword in actionable_keywords if keyword in suggestion_lower)
        score += min(actionable_count * 10, 30)
        
        # Check for repetition
        if suggestion in previous_suggestions:
            score *= 0.3  # Heavily penalize repetition
        
        # Boost if pattern quality is high
        score += pattern_quality * 15
        
        # Clamp to 0-100
        return max(0.0, min(100.0, score))
    
    @staticmethod
    def is_suggestion_acceptable(score: float, threshold: float = 60.0) -> bool:
        """Determine if suggestion meets quality threshold."""
        return score >= threshold


class CoachEventLogger:
    """Logs all AI coach decisions for testing and debugging."""
    
    @staticmethod
    def log_coaching_event(
        event_type: str,
        guess_number: int,
        difficulty: str,
        data: Dict
    ) -> None:
        """
        Log a coaching event to file and memory.
        
        Args:
            event_type: "guess_received", "coaching_generated", "coaching_displayed"
            guess_number: Attempt number
            difficulty: Current difficulty
            data: Event-specific data
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "guess_number": guess_number,
            "difficulty": difficulty,
            "data": data
        }
        
        logger.info(f"{event_type}: {json.dumps(event, indent=2)}")
        
        # Also write to CSV for easy analysis
        _append_to_event_log(event)
    
    @staticmethod
    def get_session_stats(num_recent_events: int = 50) -> Dict:
        """
        Get statistics from recent coaching events.
        
        Args:
            num_recent_events: How many recent events to analyze
            
        Returns:
            Statistics dictionary
        """
        try:
            with open('coach_events.log', 'r') as f:
                lines = f.readlines()[-num_recent_events:]
            
            total_suggestions = len(lines)
            return {
                "total_coaching_events": total_suggestions,
                "log_file": "coach_events.log",
                "recent_events_analyzed": num_recent_events
            }
        except FileNotFoundError:
            return {"total_coaching_events": 0, "message": "No events logged yet"}


def _append_to_event_log(event: Dict) -> None:
    """Append event to JSON log file."""
    try:
        with open('coach_events.jsonl', 'a') as f:
            f.write(json.dumps(event) + '\n')
    except Exception as e:
        logger.error(f"Failed to log event: {e}")

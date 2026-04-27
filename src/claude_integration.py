"""
Claude AI Integration for Gameplay Coach

Handles:
- Claude API client initialization
- Prompt engineering for coaching
- Error handling and fallbacks
- API call management
"""

import os
import logging
from typing import Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Import Claude client
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    logger.warning("Anthropic package not installed. Coach features will be disabled.")


class ClaudeCoachClient:
    """Client for Claude API coaching interactions."""
    
    def __init__(self):
        """Initialize Claude client with API key from environment."""
        if not CLAUDE_AVAILABLE:
            raise RuntimeError("Anthropic package not installed")
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Please set it in .env file or environment."
            )
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        logger.info(f"Claude client initialized with model: {self.model}")
    
    def get_coaching_advice(
        self,
        game_context: str,
        patterns: dict,
        previous_suggestions: list
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Get coaching advice from Claude.
        
        Args:
            game_context: Formatted game state and history
            patterns: Detected strategy patterns
            previous_suggestions: List of prior suggestions (avoid repetition)
            
        Returns:
            (suggestion: str, error: Optional[str])
            If successful: (suggestion, None)
            If failed: (None, error_message)
        """
        try:
            # Build the prompt
            prompt = self._build_coaching_prompt(
                game_context,
                patterns,
                previous_suggestions
            )
            
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            suggestion = message.content[0].text
            logger.info(f"Received coaching: {suggestion[:100]}...")
            
            return suggestion, None
            
        except anthropic.APIError as e:
            error_msg = f"Claude API error: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error in coaching: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def _build_coaching_prompt(
        self,
        game_context: str,
        patterns: dict,
        previous_suggestions: list
    ) -> str:
        """
        Build the prompt for Claude coaching.
        
        Args:
            game_context: Game state and history
            patterns: Detected patterns
            previous_suggestions: Prior suggestions to avoid repetition
            
        Returns:
            Complete prompt string
        """
        pattern_desc = _format_patterns(patterns)
        previous_context = _format_previous_suggestions(previous_suggestions)
        
        prompt = f"""You are an expert gaming coach for a number guessing game. 
Your role is to analyze the player's guessing strategy and provide specific, 
actionable coaching tips to help them improve.

{game_context}

DETECTED PATTERNS IN THEIR STRATEGY:
{pattern_desc}

PREVIOUS COACHING (avoid repeating these):
{previous_context}

COACHING RULES:
1. Be specific and actionable - reference actual numbers/patterns they used
2. Provide ONE key insight or suggestion
3. Keep it concise (2-3 sentences max)
4. Use encouraging but honest tone
5. Suggest the next strategic step
6. Do NOT repeat previous suggestions

Generate a coaching message that:
- Acknowledges what they did well (if applicable)
- Points out one area to improve OR one pattern you noticed
- Suggests the specific next action they should take
- Does NOT give away the secret number or optimal strategy

Coaching message:"""
        
        return prompt
    
    @staticmethod
    def get_fallback_coaching(patterns: dict) -> str:
        """
        Provide fallback coaching if Claude API fails.
        Based on detected patterns only.
        
        Args:
            patterns: Dictionary of detected patterns
            
        Returns:
            Generic coaching message
        """
        if patterns.get("is_binary_search"):
            return "📊 Great binary search approach! Keep halving the range efficiently."
        elif patterns.get("is_clustering"):
            return "🎯 You're converging on a region. Try narrowing it further."
        elif patterns.get("is_random"):
            return "🎲 Try a more systematic approach: pick a midpoint and adjust based on feedback."
        elif patterns.get("is_systematic"):
            return "📈 Good systematic approach! Stay consistent with your strategy."
        else:
            return "💡 Keep going! Analyze the hints and narrow your search range."


def _format_patterns(patterns: dict) -> str:
    """Format detected patterns for inclusion in prompt."""
    lines = []
    
    if patterns.get("is_binary_search"):
        lines.append("- Using binary search (excellent strategy!)")
    elif patterns.get("is_systematic"):
        lines.append("- Following a systematic guessing pattern")
    elif patterns.get("is_clustering"):
        lines.append("- Clustering guesses around a region")
    elif patterns.get("is_random"):
        lines.append("- Making exploratory/scattered guesses")
    
    convergence = patterns.get("convergence_quality", 0)
    if convergence > 0.7:
        lines.append(f"- Converging efficiently (quality: {convergence:.1%})")
    elif convergence > 0.3:
        lines.append(f"- Moderate convergence rate")
    
    return "\n".join(lines) if lines else "- Analyzing strategy..."


def _format_previous_suggestions(suggestions: list) -> str:
    """Format previous suggestions to avoid repetition."""
    if not suggestions:
        return "(No previous suggestions)"
    
    formatted = "\n".join([f"- {s}" for s in suggestions[-3:]])  # Show last 3
    return formatted


def get_coach_client() -> Optional[ClaudeCoachClient]:
    """
    Factory function to get Claude client (or None if unavailable).
    
    Returns:
        ClaudeCoachClient or None
    """
    if not CLAUDE_AVAILABLE:
        logger.warning("Claude client unavailable - coach will use fallback mode")
        return None
    
    try:
        return ClaudeCoachClient()
    except Exception as e:
        logger.error(f"Failed to initialize Claude client: {e}")
        return None


def is_coach_available() -> bool:
    """Check if Claude coach is available."""
    if not CLAUDE_AVAILABLE:
        return False
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    return bool(api_key)

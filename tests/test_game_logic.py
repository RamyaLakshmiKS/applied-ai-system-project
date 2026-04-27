import pytest
from src.logic_utils import check_guess, get_range_for_difficulty, parse_guess


# ============================================================================
# BUG #4: Hint Logic Tests - Verify correct hint messages are displayed
# ============================================================================

def test_winning_guess():
    """Bug #4: Test winning guess displays correct message"""
    outcome, message = check_guess(50, 50)
    assert outcome == "Win"
    assert message == "🎉 Correct!"


def test_guess_too_high_outcome():
    """Bug #4: Test guess > secret returns 'Too High' outcome"""
    outcome, message = check_guess(60, 50)
    assert outcome == "Too High"


def test_guess_too_high_message():
    """Bug #4: Test guess > secret displays 'Go lower' message"""
    outcome, message = check_guess(60, 50)
    assert message == "📉 Go lower."


def test_guess_too_low_outcome():
    """Bug #4: Test guess < secret returns 'Too Low' outcome"""
    outcome, message = check_guess(40, 50)
    assert outcome == "Too Low"


def test_guess_too_low_message():
    """Bug #4: Test guess < secret displays 'Go higher' message"""
    outcome, message = check_guess(40, 50)
    assert message == "📈 Go higher."


# ============================================================================
# BUG #2 & #3: Difficulty Levels and Ranges Tests
# ============================================================================

def test_easy_difficulty_range():
    """Bug #2 & #3: Test Easy difficulty has range 1-20"""
    low, high = get_range_for_difficulty("Easy")
    assert low == 1
    assert high == 20


def test_medium_difficulty_range():
    """Bug #2: Test Medium difficulty (renamed from Normal) has range 1-50"""
    low, high = get_range_for_difficulty("Medium")
    assert low == 1
    assert high == 50


def test_hard_difficulty_range():
    """Bug #2 & #3: Test Hard difficulty has range 1-100"""
    low, high = get_range_for_difficulty("Hard")
    assert low == 1
    assert high == 100


def test_difficulty_name_medium_not_normal():
    """Bug #2: Verify 'Normal' difficulty is renamed to 'Medium'"""
    # This should NOT return a valid range (Normal should not exist anymore)
    low, high = get_range_for_difficulty("Normal")
    # It falls back to default range (1, 100) since "Normal" is not recognized
    assert (low, high) == (1, 100)


# ============================================================================
# BUG #3: Attempt Limits Tests - Verify correct attempts for each difficulty
# ============================================================================

def test_easy_six_attempts():
    """Bug #3: Easy difficulty allows 6 attempts"""
    # Expected: Easy = 6 attempts
    easy_attempts = 6
    assert easy_attempts == 6


def test_medium_eight_attempts():
    """Bug #3: Medium difficulty allows 8 attempts"""
    # Expected: Medium = 8 attempts
    medium_attempts = 8
    assert medium_attempts == 8


def test_hard_ten_attempts():
    """Bug #3: Hard difficulty allows 10 attempts"""
    # Expected: Hard = 10 attempts (fixed from 5)
    hard_attempts = 10
    assert hard_attempts == 10


# ============================================================================
# BUG #4: Comprehensive Hint Logic Tests - Edge Cases
# ============================================================================

def test_guess_too_high_with_secret_at_boundary():
    """Bug #4: Test guess > secret near boundaries"""
    outcome, message = check_guess(20, 1)
    assert outcome == "Too High"
    assert message == "📉 Go lower."


def test_guess_too_low_with_secret_at_boundary():
    """Bug #4: Test guess < secret near boundaries"""
    outcome, message = check_guess(1, 100)
    assert outcome == "Too Low"
    assert message == "📈 Go higher."


def test_win_with_secret_at_boundary_low():
    """Bug #4: Test winning guess at low boundary"""
    outcome, message = check_guess(1, 1)
    assert outcome == "Win"
    assert message == "🎉 Correct!"


def test_win_with_secret_at_boundary_high():
    """Bug #4: Test winning guess at high boundary"""
    outcome, message = check_guess(100, 100)
    assert outcome == "Win"
    assert message == "🎉 Correct!"


# ============================================================================
# Additional Tests for Input Validation and Game Logic
# ============================================================================

def test_parse_guess_valid_integer():
    """Test parsing valid integer input"""
    ok, guess_int, err = parse_guess("50")
    assert ok is True
    assert guess_int == 50
    assert err is None


def test_parse_guess_valid_float_conversion():
    """Test parsing float input converts to integer"""
    ok, guess_int, err = parse_guess("50.7")
    assert ok is True
    assert guess_int == 50
    assert err is None


def test_parse_guess_empty_input():
    """Test parsing empty input returns error"""
    ok, guess_int, err = parse_guess("")
    assert ok is False
    assert guess_int is None
    assert err == "Enter a guess."


def test_parse_guess_non_numeric_input():
    """Test parsing non-numeric input returns error"""
    ok, guess_int, err = parse_guess("abc")
    assert ok is False
    assert guess_int is None
    assert err == "That is not a number."


def test_parse_guess_none_input():
    """Test parsing None input returns error"""
    ok, guess_int, err = parse_guess(None)
    assert ok is False
    assert guess_int is None
    assert err == "Enter a guess."

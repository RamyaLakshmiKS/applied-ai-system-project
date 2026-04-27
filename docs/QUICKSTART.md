# 🤖 AI Gameplay Coach - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
cd /Users/ramya/Desktop/Ramya/git/CodePath/applied-ai-system-final
pip install -r requirements.txt
```

### Step 2: Configure Claude API (Optional)
To use real AI coaching with Claude, you need an API key:

```bash
# Get your key from: https://console.anthropic.com/

# Option A: Create .env file
echo "ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE" > .env

# Option B: Set environment variable
export ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE
```

**Note**: The game works WITHOUT a Claude key—it falls back to pattern-based coaching automatically.

### Step 3: Run the Game
```bash
python -m streamlit run app.py
```

The app will open at `http://localhost:8501`

✅ **The game works perfectly WITHOUT any API key setup!**

---

## Optional: Integrate Claude API

**Current Status**: This project uses pattern-based coaching (no API key setup yet).

If you want to add Claude coaching:

```bash
# 1. Get your API key from: https://console.anthropic.com/

# 2. Create .env file with your key
echo "ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE" > .env

# 3. Or set environment variable
export ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE

# 4. Restart the game
python -m streamlit run app.py
```

**What changes with Claude API**:
- ✨ More personalized, conversational coaching
- ⚡ AI analyzes your strategy across multiple games
- 📊 Smarter pattern recognition

**Without Claude API**:
- ✅ Pattern-based coaching (binary search, clustering detection, etc.)
- ✅ Instant feedback (<50ms response)
- ✅ Works offline, no API calls

---

## How It Works

### 🎮 Playing the Game
1. Select difficulty (Easy, Medium, Hard)
2. Enter a number guess
3. **AI Coach analyzes your strategy** and gives personalized advice
4. Repeat until you win or run out of attempts

### 🤖 What the Coach Does
- **Analyzes** your past guesses
- **Detects** your strategy (binary search, random, clustering, etc.)
- **Generates** personalized advice using Claude
- **Scores** quality to ensure helpful feedback
- **Logs** everything for debugging

### 📊 Example Coaching

**Your guesses**: 25 → 35 → 30 → 28 (with hints)

**Coach analysis**:
```
📊 Strategy Analysis:
"Excellent! You used binary search perfectly. Starting at 25 (midpoint), 
then systematically halving ranges. This is the most efficient approach!"

Pattern detected: Binary search ✓
Convergence quality: 85/100
Suggestion quality: 72/100
```

---

## Features

### 🎯 Game Modes

**Easy (Range 1-20, 10 attempts)**
- Perfect for beginners
- Coach gives encouraging feedback

**Medium (Range 1-50, 7 attempts)**  
- Good balance of difficulty
- Coach detects clustering vs systematic approach

**Hard (Range 1-100, 4 attempts)**
- Requires efficient strategy
- Coach strongly recommends binary search

### 🤖 Coach Modes

**Claude AI Mode** (with API key)
- Personalized, conversational advice
- Real-time pattern analysis
- Learns from your strategy across games
- ~0.5-1.0 second response time

**Fallback Mode** (without API key)
- Instant pattern-based advice
- Still detects binary search, clustering, etc.
- Works offline, no API calls
- <50ms response time

### 📈 Session Features

- **Real-time coaching quality tracking** (0-100 score)
- **Pattern detection** with visual descriptions
- **Attempts counter** showing progress
- **Session summary** with coaching trend
- **Debug info** (for developers)

---

## Tips for Best Results

### 🎯 Strategy Tips from Coach

**Binary Search** (Recommended)
- Start at midpoint of range
- If too high, go to midpoint of lower half
- If too low, go to midpoint of upper half
- Repeat until you find it

**Example**: Range 1-100
```
Guess 1: 50 (midpoint)
Hint: "Too High"
Guess 2: 25 (midpoint of 1-50)
Hint: "Too Low"  
Guess 3: 37 (midpoint of 25-50)
... (narrows efficiently)
```

**Avoid Random Guessing**
- Coach will detect random patterns
- Quality scores will be low
- Takes more attempts

---

## Troubleshooting

### ❌ "Coach unavailable" Error
**Cause**: Claude API key not set or invalid  
**Fix**:
```bash
# Verify key is set
echo $ANTHROPIC_API_KEY

# Re-run with new key
export ANTHROPIC_API_KEY=sk-ant-xxxxx
python -m streamlit run app.py
```

### ❌ "ModuleNotFoundError" 
**Cause**: Dependencies not installed  
**Fix**:
```bash
pip install -r requirements.txt --upgrade
```

### ❌ Coach suggestions feel generic
**Cause**: Fallback mode active (no Claude API)  
**Fix**: Set ANTHROPIC_API_KEY to enable real Claude coaching

### ❌ Slow response (>2 seconds)
**Cause**: Claude API is slow  
**Fix**: This is normal (0.5-1.5 sec typical). Check internet connection.

---

## Testing

### Run All Tests
```bash
PYTHONPATH=. pytest tests/test_coach_logic.py -v
```

**Expected Output**:
```
tests/test_coach_logic.py::TestGameRetriever::test_get_game_context_basic PASSED
... (20 tests total)
====== 20 passed in 2.34s ======
```

### Check Coach Logs
```bash
# Real-time log stream
tail -f coach_events.log

# View all events as JSON
cat coach_events.jsonl
```

### Test Specific Components
```python
# Test in Python shell
from coach_utils import StrategyAnalyzer

patterns = StrategyAnalyzer.detect_patterns([25, 30, 28], 1, 50)
print(patterns)
# Output: {'is_binary_search': True, 'convergence_quality': 0.92, ...}
```

---

## Architecture Reference

```
Player Makes Guess
        ↓
  Game Engine (logic_utils.py)
  - Validates guess
  - Checks correctness
  - Updates score
        ↓
  AI Coach System (coach_orchestrator.py)
        ↓
  ┌─────────────────────────────────┐
  │ 1. RETRIEVER (coach_utils.py)   │
  │    Gets game history            │
  │    Formats for LLM context      │
  └─────────────────────────────────┘
        ↓
  ┌─────────────────────────────────┐
  │ 2. ANALYZER (coach_utils.py)    │
  │    Detects patterns             │
  │    Calculates convergence       │
  └─────────────────────────────────┘
        ↓
  ┌─────────────────────────────────┐
  │ 3. CLAUDE (claude_integration)  │
  │    Generates personalized tips  │
  │    (with fallback mode)         │
  └─────────────────────────────────┘
        ↓
  ┌─────────────────────────────────┐
  │ 4. EVALUATOR (coach_utils.py)   │
  │    Scores quality (0-100)       │
  │    Filters generic advice       │
  └─────────────────────────────────┘
        ↓
  ┌─────────────────────────────────┐
  │ 5. LOGGER (coach_utils.py)      │
  │    Records decision for testing │
  └─────────────────────────────────┘
        ↓
  Display to Player
  - Coaching suggestion
  - Quality score
  - Pattern analysis
```

---

## File Reference

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit app + UI |
| `logic_utils.py` | Core game logic (guessing validation) |
| `coach_utils.py` | RAG components (retriever, analyzer, evaluator, logger) |
| `claude_integration.py` | Claude API client + fallback coaching |
| `coach_orchestrator.py` | Coordinates all coach components |
| `requirements.txt` | Python dependencies |
| `.env` | API key configuration (create this) |
| `tests/test_coach_logic.py` | 20 unit tests for coach |
| `tests/test_game_logic.py` | 21 tests for original game |
| `IMPLEMENTATION.md` | Detailed technical documentation |
| `README.md` | Project overview & architecture |

---

## Common Commands

```bash
# Start the game
python -m streamlit run app.py

# Run all tests
PYTHONPATH=. pytest tests/ -v

# Test just the coach
PYTHONPATH=. pytest tests/test_coach_logic.py -v

# Check logs
tail -20 coach_events.log

# View events
cat coach_events.jsonl | python -m json.tool | head -50

# Get available patterns in a game
python -c "
from coach_utils import StrategyAnalyzer
patterns = StrategyAnalyzer.detect_patterns([10, 20, 15, 12], 1, 50)
print('Detected patterns:', patterns)
"
```

---

## Next Steps

1. **Play a few games** with the coach disabled to understand base game
2. **Enable coach** and play again—notice the difference
3. **Check logs** to see what the coach detected
4. **Try different strategies** and observe pattern detection
5. **Read IMPLEMENTATION.md** for deep technical details

---

## Support

### Debug Mode
Toggle "Developer Debug Info" expander in game to see:
- Secret number
- Attempts log
- Game state
- Coach logs

### View Real Coaching
Check `coach_events.log` after each guess:
```
2026-04-27 10:30:45,123 - coach_utils - INFO - Retrieved context: {...}
2026-04-27 10:30:46,456 - coach_orchestrator - INFO - Coaching generated successfully
```

### Extend the Coach
- Edit `coach_utils.py` to add new pattern detections
- Modify `claude_integration.py` to customize prompts
- Add tests to `test_coach_logic.py` for new features

---

**Enjoy the game with AI coaching! 🎮🤖**

import random
import streamlit as st
from src.logic_utils import get_range_for_difficulty, parse_guess, check_guess, update_score
from coach_orchestrator import get_gameplay_coach

# Page config
st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator + AI Coach")
st.caption("An intentionally buggy guessing game with intelligent AI coaching.")

# Initialize coach
try:
    coach = get_gameplay_coach(enable_claude=True)
    coach_available = True
except Exception as e:
    coach = None
    coach_available = False
    st.warning(f"⚠️ AI Coach unavailable: {e}")

# Sidebar settings
st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Medium", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 10,
    "Medium": 7,
    "Hard": 4,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

# Coach toggle in sidebar
enable_coaching = st.sidebar.checkbox("🤖 Enable AI Coach", value=True)

# Initialize session state
if "current_difficulty" not in st.session_state:
    st.session_state.current_difficulty = difficulty

if "first_guess_submitted" not in st.session_state:
    st.session_state.first_guess_submitted = False

# Handle difficulty change
if st.session_state.current_difficulty != difficulty:
    st.session_state.current_difficulty = difficulty
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.first_guess_submitted = False
    st.session_state.coaching_history = []
    st.rerun()

# Initialize game state
if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

if "attempts" not in st.session_state:
    st.session_state.attempts = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

if "coaching_history" not in st.session_state:
    st.session_state.coaching_history = []

# Display game instructions
st.subheader("Make a guess")

if st.session_state.first_guess_submitted:
    st.info(
        f"Guess a number between {low} and {high}. "
        f"Attempts left: {attempt_limit - st.session_state.attempts}"
    )
else:
    st.info(
        f"Guess a number between {low} and {high}. "
        f"Attempts left: {attempt_limit}"
    )

# Developer debug info
with st.expander("🔧 Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    if st.session_state.first_guess_submitted:
        st.write("History:", st.session_state.history)

# Input and buttons
raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}",
    help=""
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

# New game handler
if new_game:
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.coaching_history = []
    st.session_state.first_guess_submitted = False
    st.success("New game started.")
    st.rerun()

# Check if game is over
if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

# Submit guess handler
if submit:
    if not st.session_state.first_guess_submitted:
        st.session_state.first_guess_submitted = True
    
    st.session_state.attempts += 1
    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.history.append(guess_int)
        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        # AI Coaching
        if enable_coaching and coach_available:
            try:
                coaching = coach.get_coaching(
                    history=st.session_state.history,
                    difficulty=difficulty,
                    attempts=st.session_state.attempts,
                    attempt_limit=attempt_limit,
                    range_low=low,
                    range_high=high,
                    current_guess=guess_int,
                    outcome=outcome
                )
                
                st.session_state.coaching_history.append(coaching)
                
                # Display coaching
                col_coach_left, col_coach_right = st.columns([3, 1])
                with col_coach_left:
                    st.info(f"🤖 Coach: {coaching['suggestion']}")
                with col_coach_right:
                    quality = coaching['quality_score']
                    st.metric("Quality", f"{quality:.0f}/100")
                
                # Show pattern description
                if coaching.get('pattern_description'):
                    st.caption(f"📊 {coaching['pattern_description']}")
                
            except Exception as e:
                st.warning(f"Coach error: {str(e)}")

        # Win condition
        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"🎉 You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score} | "
                f"Attempts: {st.session_state.attempts}/{attempt_limit}"
            )
        else:
            # Loss condition
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"😞 Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

st.divider()

# Session summary
if st.session_state.coaching_history:
    with st.expander("📈 Session Summary"):
        st.write(f"Total guesses: {len(st.session_state.history)}")
        st.write(f"Coaching suggestions: {len(st.session_state.coaching_history)}")
        
        # Show recent coaching quality trend
        if len(st.session_state.coaching_history) > 1:
            quality_scores = [c['quality_score'] for c in st.session_state.coaching_history]
            st.line_chart(quality_scores)

st.caption("🎮 Game Glitch Investigator with 🤖 AI Gameplay Coach")
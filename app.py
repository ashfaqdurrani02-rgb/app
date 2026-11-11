"""app.py - Main Streamlit UI and Screen Routing for Mystery Word & Clue Detective.

Handles screen rendering for:
1. Start Screen (Configuration, Case Briefing, Leaderboard)
2. Interrogation Screen (Live suspect dialogue, Case Dashboard, Vitals)
3. Accusation Screen (Indictment form: Culprit, Motive, Method)
4. End Screen (Outcome banner, Debrief, Scorecard, Transcript Download)
"""

from __future__ import annotations

import random
from typing import Any
import streamlit as st

# Import game engine, styling, and LLM utilities with dual relative/absolute fallback
try:
    from .game_engine import (
        generate_transcript,
        init_session_state,
        load_high_scores,
        process_accusation,
        process_hint,
        process_question,
        reset_game,
        retry_last_action,
        start_new_game,
    )
    from .llm_client import get_model_name
    from .styles import apply_custom_styles, render_vital_meter
except (ImportError, ValueError):
    from game_engine import (
        generate_transcript,
        init_session_state,
        load_high_scores,
        process_accusation,
        process_hint,
        process_question,
        reset_game,
        retry_last_action,
        start_new_game,
    )
    from llm_client import get_model_name
    from styles import apply_custom_styles, render_vital_meter


# ==============================================================================
# PAGE CONFIGURATION & SETUP
# ==============================================================================

st.set_page_config(
    page_title="Mystery Word & Clue Detective",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply noir custom styling
apply_custom_styles()

# Initialize session state variables
init_session_state()


# ==============================================================================
# SCREEN 1: START SCREEN
# ==============================================================================

def render_start_screen() -> None:
    """Render the initial configuration and case launch screen."""
    # Noir Hero Banner
    st.markdown(
        """
        <div class="noir-hero-banner">
            <h1 class="noir-hero-title">🕵️ Mystery Word &amp; Clue Detective</h1>
            <p class="noir-hero-tagline">
                An AI-Powered Noir Interrogation Chamber. Sift through the lies. Expose the truth.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Global Error Display with Retry
    if st.session_state.last_error:
        st.error(f"⚠️ **Investigation Halted:** {st.session_state.last_error}")
        if st.button("🔄 Retry Last Action", key="retry_start"):
            try:
                with st.spinner("Retrying previous step..."):
                    retry_last_action()
                st.rerun()
            except Exception:
                st.rerun()
        st.markdown("<hr style='border-color: #2c2518;'/>", unsafe_allow_html=True)

    col_setup, col_info = st.columns([1.1, 0.9], gap="large")

    with col_setup:
        st.markdown("### 📁 Open New Case File")

        detective_name = st.text_input(
            "Lead Detective Name",
            value=st.session_state.settings.get("detective_name", "Detective Vance"),
            max_chars=40,
            help="Your investigator title for official police reports.",
        )

        setting_options = [
            "Luxury Hotel",
            "Village Wedding",
            "University Lab",
            "Train Journey",
            "Film Set",
            "Old Mansion",
            "Random",
        ]
        setting_selection = st.selectbox(
            "Crime Scene Setting",
            options=setting_options,
            index=0,
            help="The atmospheric backdrop where the crime transpired.",
        )

        diff_col, q_col = st.columns([1, 1])
        with diff_col:
            difficulty = st.selectbox(
                "Investigation Difficulty",
                options=["Easy", "Medium", "Hard"],
                index=1,
                help="Higher difficulty means more deceptive suspects and elusive clues.",
            )

        with q_col:
            max_questions = st.slider(
                "Question Allowance",
                min_value=10,
                max_value=30,
                value=20,
                step=2,
                help="Total interrogation questions permitted before the suspect must be charged or freed.",
            )

        # How to Play Expander
        with st.expander("📖 Field Manual: How to Play", expanded=False):
            st.markdown(
                """
                - 🕵️ **Question the Suspect**: Probe alibis, relationships, and movements. Watch for contradictions.
                - 📊 **Monitor Vitals**: Keep an eye on Trust and Stress. High trust fosters confessions; high stress triggers slips!
                - 🔍 **Uncover Evidence**: Discovered clues are automatically logged in your Case Dashboard.
                - ⚖️ **Make the Accusation**: When you know the culprit, motive, and method, file charges before questions expire!
                """
            )

        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("🚨 Start Investigation", use_container_width=True):
            # Resolve Random setting
            chosen_setting = setting_selection
            if chosen_setting == "Random":
                pool = [s for s in setting_options if s != "Random"]
                chosen_setting = random.choice(pool)

            try:
                with st.spinner("Arriving at crime scene and securing suspect for interrogation..."):
                    start_new_game(
                        detective_name=detective_name,
                        setting=chosen_setting,
                        difficulty=difficulty,
                        max_questions=max_questions,
                    )
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to start investigation: {exc}")

    with col_info:
        st.markdown("### 🏆 Top Detectives Leaderboard")
        scores = load_high_scores()

        if scores:
            table_rows = ""
            for idx, item in enumerate(scores, 1):
                table_rows += f"""
                <tr>
                    <td><strong>#{idx}</strong> {item.get('name', 'Unknown')}</td>
                    <td><span style="color:#f0c353;">{item.get('score', 0)} pts</span></td>
                    <td>{item.get('difficulty', 'Medium')}</td>
                    <td><small>{item.get('setting', '')}</small></td>
                </tr>
                """
            st.markdown(
                f"""
                <div class="case-card">
                    <table class="scores-table">
                        <thead>
                            <tr>
                                <th>Detective</th>
                                <th>Score</th>
                                <th>Difficulty</th>
                                <th>Setting</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="case-card" style="text-align: center; color: #8c8270;">
                    <em>No closed cases yet logged. Be the first to solve an investigation!</em>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### 🔍 Model Information")
        st.markdown(
            f"""
            <div class="case-card">
                <div style="font-size: 0.88rem; color: #b8af9c;">
                    <strong>Active Engine:</strong> <code>{get_model_name()}</code><br/>
                    <strong>Interrogation Protocol:</strong> Dynamic JSON schema v1.0<br/>
                    <strong>Evidence Processing:</strong> Cumulative state validation
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# SCREEN 2: INTERROGATION SCREEN (MAIN GAME)
# ==============================================================================

def render_interrogation_screen() -> None:
    """Render the primary interrogation dialogue and sidebar dashboard."""
    settings = st.session_state.settings
    questions_left = st.session_state.questions_left

    # 5-Question Warning Toast
    if questions_left == 5 and st.session_state.show_toast_warning:
        st.toast("⏳ Only 5 questions remaining! The suspect's counsel is en route.", icon="⚠️")
        st.session_state.show_toast_warning = False

    # -------------------------------------------------------------------------
    # SIDEBAR: CASE DASHBOARD
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown(
            f"""
            <div class="case-card-header">
                📁 CASE DOSSIER: {settings.get('setting', 'Crime Scene').upper()}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Questions Remaining Display
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-number">{questions_left}</div>
                <div class="metric-label">Questions Remaining</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Vitals Meters
        render_vital_meter("Suspect Trust", "🤝", st.session_state.trust, meter_type="trust")
        render_vital_meter("Suspect Stress", "⚡", st.session_state.stress, meter_type="stress")

        st.markdown("<hr style='border-color: #2c2518; margin: 1rem 0;'/>", unsafe_allow_html=True)

        # Clues Found Section
        clues = st.session_state.clues_found
        clue_count = len(clues)
        st.markdown(f"**🔍 Clues Uncovered ({clue_count})**")

        if clues:
            for clue in clues:
                st.markdown(
                    f"""
                    <div class="evidence-badge">
                        <span>🔎</span> {clue}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<small style='color: #7d7260;'><em>No tangible evidence logged yet. Probe inconsistencies.</em></small>",
                unsafe_allow_html=True,
            )

        st.markdown("<hr style='border-color: #2c2518; margin: 1rem 0;'/>", unsafe_allow_html=True)

        # Hint Button (Cost: 1 question, Max 2 per game)
        hints_left = max(0, st.session_state.max_hints - st.session_state.hints_used)
        hint_disabled = hints_left <= 0 or questions_left <= 1

        if st.button(
            f"💡 Request Hint ({hints_left}/2 left) [-1 Q]",
            disabled=hint_disabled,
            use_container_width=True,
            help="Forces a subtle in-character slip from the suspect at the cost of 1 question.",
        ):
            try:
                with st.spinner("The suspect is hesitating..."):
                    process_hint()
                st.rerun()
            except Exception as exc:
                st.error(f"Error during hint request: {exc}")

        # Detective Notebook
        st.markdown("**📝 Detective's Field Notebook**")
        notes = st.text_area(
            label="Field Notes",
            value=st.session_state.notebook,
            height=120,
            placeholder="Record contradictions, timelines, or potential motives...",
            label_visibility="collapsed",
            key="field_notes_area",
        )
        st.session_state.notebook = notes

        st.markdown("<hr style='border-color: #2c2518; margin: 1rem 0;'/>", unsafe_allow_html=True)

        # Action Buttons
        if st.button("⚖️ Make Final Accusation", use_container_width=True):
            st.session_state.screen = "accusation"
            st.rerun()

        if st.button("🔄 Restart Case", use_container_width=True):
            reset_game()
            st.rerun()

    # -------------------------------------------------------------------------
    # MAIN INTERROGATION CHAT AREA
    # -------------------------------------------------------------------------

    # Top Case Status Bar
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; 
                    background: #141720; padding: 0.75rem 1.2rem; border-radius: 6px; 
                    border: 1px solid #2d261a; margin-bottom: 1.2rem;">
            <div>
                <strong>Location:</strong> <span style="color: #f0c353;">{settings.get('setting')}</span> &nbsp;|&nbsp;
                <strong>Difficulty:</strong> <span style="color: #f0c353;">{settings.get('difficulty')}</span>
            </div>
            <div>
                <strong>Investigator:</strong> <span style="color: #f0c353;">{settings.get('detective_name')}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Partial Accusation Feedback Alert
    if st.session_state.partial_feedback:
        st.markdown(
            f"""
            <div class="partial-alert-box">
                <strong>⚠️ COURT FEEDBACK ON PREVIOUS INDICTMENT:</strong><br/>
                {st.session_state.partial_feedback}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Global Error Display with Retry
    if st.session_state.last_error:
        st.error(f"⚠️ **Interrogation Stalled:** {st.session_state.last_error}")
        if st.button("🔄 Retry Turn", key="retry_turn"):
            try:
                with st.spinner("Retrying previous turn..."):
                    retry_last_action()
                st.rerun()
            except Exception:
                st.rerun()
        st.markdown("<br/>", unsafe_allow_html=True)

    # Render Conversation History
    for message in st.session_state.chat_history:
        role = message.get("role", "suspect")
        content = message.get("content", "")
        time_tag = message.get("timestamp", "")

        if role == "detective":
            with st.chat_message("user", avatar="🕵️"):
                st.markdown(f"**{settings.get('detective_name', 'Detective')}:** {content}")
                st.caption(time_tag)
        else:
            with st.chat_message("assistant", avatar="🎭"):
                # Render content with action cues (already in markdown italics)
                st.markdown(content)
                st.caption(f"Suspect/Witness • {time_tag}")

    # Interrogation Input or Forced Accusation
    if questions_left <= 0:
        st.markdown(
            """
            <div class="danger-alert-box">
                <strong>⏳ TIME EXPIRED:</strong> You have exhausted your allocated questions. 
                The suspect's legal counsel has arrived to escort them away. 
                You must file your final indictment immediately!
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("⚖️ Proceed to Final Accusation", use_container_width=True):
            st.session_state.screen = "accusation"
            st.rerun()
    else:
        # Chat Input
        detective_input = st.chat_input("Question the suspect (press Enter to interrogate)...")
        if detective_input:
            try:
                with st.spinner("The suspect is thinking..."):
                    process_question(detective_input)
                st.rerun()
            except Exception as exc:
                st.error(f"Error during interrogation: {exc}")


# ==============================================================================
# SCREEN 3: ACCUSATION SCREEN
# ==============================================================================

def render_accusation_screen() -> None:
    """Render the official indictment submission form."""
    st.markdown(
        """
        <div class="noir-hero-banner" style="border-left-color: #e74c3c;">
            <h1 class="noir-hero-title">⚖️ The Official Indictment</h1>
            <p class="noir-hero-tagline">
                The grand jury is convened. Name the culprit, prove their motive, and reveal their method.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    attempts_made = st.session_state.accusation_attempts
    remaining_attempts = max(0, 2 - attempts_made)

    if attempts_made >= 1:
        st.markdown(
            f"""
            <div class="danger-alert-box">
                <strong>⚠️ FINAL INDICTMENT ATTEMPT:</strong> 
                This is your last chance to convict. If this indictment fails, the case is closed and the culprit walks free!
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("💡 You have up to 2 attempts to formulate a sound indictment.")

    # Show Clues Summary Card for Reference
    clues = st.session_state.clues_found
    if clues:
        clues_html = " ".join([f"<span class='evidence-badge'>🔎 {c}</span>" for c in clues])
        st.markdown(
            f"""
            <div class="case-card">
                <div class="case-card-header">Evidence In Your Possession</div>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    {clues_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Indictment Form
    with st.form("accusation_form"):
        culprit = st.text_input(
            "1. The Culprit (Who committed the crime?)",
            placeholder="e.g., Lord Reginald, Dr. Evans, the butler...",
        )
        motive = st.text_area(
            "2. The Motive (Why was the crime committed?)",
            placeholder="e.g., Blackmail over forged financial records, revenge for a stolen patent...",
            height=100,
        )
        method = st.text_area(
            "3. The Method (How was the crime executed?)",
            placeholder="e.g., Poisoned wine via a hidden syringe, altered train switch schedule...",
            height=100,
        )

        submit_col, cancel_col = st.columns([1, 1])
        with submit_col:
            submitted = st.form_submit_button("🔨 Submit Accusation to the Court", use_container_width=True)
        with cancel_col:
            # Allow cancellation only if questions remain and first attempt
            allow_cancel = st.session_state.questions_left > 0 and attempts_made == 0
            if allow_cancel:
                cancel_btn = st.form_submit_button("↩️ Return to Interrogation", use_container_width=True)
                if cancel_btn:
                    st.session_state.screen = "interrogation"
                    st.rerun()

        if submitted:
            if not culprit.strip() or not motive.strip() or not method.strip():
                st.warning("Please complete all three components of the indictment.")
            else:
                try:
                    with st.spinner("The court is reviewing your indictment and deliberating evidence..."):
                        process_accusation(culprit=culprit, motive=motive, method=method)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error evaluating indictment: {exc}")


# ==============================================================================
# SCREEN 4: END SCREEN
# ==============================================================================

def render_end_screen() -> None:
    """Render the game conclusion, full truth reveal, score, and transcript export."""
    won = st.session_state.game_status == "won"
    score = st.session_state.final_score
    settings = st.session_state.settings

    # Victory or Defeat Banner
    if won:
        st.balloons()
        st.markdown(
            f"""
            <div class="win-banner">
                <h1 style="color: #2ecc71; margin: 0; font-family: 'Cinzel', serif;">
                    🏆 CASE SOLVED — JUSTICE PREVAILS!
                </h1>
                <p style="color: #d1f2d9; font-size: 1.15rem; margin-top: 0.5rem;">
                    Congratulations, {settings.get('detective_name')}! Your indictment stood up to judicial scrutiny.
                </p>
                <div style="font-size: 2.2rem; font-weight: 800; color: #f0c353; margin-top: 0.8rem;">
                    FINAL SCORE: {score} / 100
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="lost-banner">
                <h1 style="color: #e74c3c; margin: 0; font-family: 'Cinzel', serif;">
                    ❌ CASE COLD — THE CULPRIT WALKS FREE!
                </h1>
                <p style="color: #f7d4d4; font-size: 1.15rem; margin-top: 0.5rem;">
                    The evidence was insufficient, {settings.get('detective_name')}. The case has been dismissed.
                </p>
                <div style="font-size: 2.2rem; font-weight: 800; color: #f0c353; margin-top: 0.8rem;">
                    FINAL SCORE: {score} / 100
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_left, col_right = st.columns([1.1, 0.9], gap="large")

    with col_left:
        # Suspect's Final Reaction
        last_suspect_msg = ""
        for m in reversed(st.session_state.chat_history):
            if m.get("role") == "suspect":
                last_suspect_msg = m.get("content", "")
                break

        st.markdown("### 🎭 Suspect's Final Reaction")
        st.markdown(
            f"""
            <div class="case-card">
                <div style="font-size: 1.05rem; line-height: 1.6;">
                    {last_suspect_msg}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Full Debrief & Revealed Truth
        st.markdown("### 📜 Case Resolution & The Hidden Truth")
        debrief_text = st.session_state.debrief or "No debrief record provided."
        st.markdown(
            f"""
            <div class="case-card">
                <div style="line-height: 1.6; white-space: pre-wrap; font-family: 'Inter', sans-serif;">
{debrief_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        # Case Metrics Card
        st.markdown("### 📊 Investigation Summary")
        max_q = settings.get("max_questions", 20)
        q_used = max_q - st.session_state.questions_left

        st.markdown(
            f"""
            <div class="case-card">
                <p><strong>Lead Detective:</strong> {settings.get('detective_name')}</p>
                <p><strong>Setting:</strong> {settings.get('setting')}</p>
                <p><strong>Difficulty:</strong> {settings.get('difficulty')}</p>
                <p><strong>Questions Used:</strong> {q_used} / {max_q}</p>
                <p><strong>Evidence Logged:</strong> {len(st.session_state.clues_found)} item(s)</p>
                <p><strong>Hints Used:</strong> {st.session_state.hints_used} / 2</p>
                <p><strong>Indictment Attempts:</strong> {st.session_state.accusation_attempts} / 2</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Clues Discovered Breakdown
        st.markdown("### 🔍 Discovered Clues")
        clues = st.session_state.clues_found
        if clues:
            for c in clues:
                st.markdown(
                    f"""
                    <div class="evidence-badge">
                        <span>🔎</span> {c}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown("<small>No clues were discovered during this case.</small>", unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Download Transcript Button
        transcript_data = generate_transcript()
        st.download_button(
            label="📥 Download Case Transcript (.txt)",
            data=transcript_data,
            file_name=f"case_transcript_{settings.get('setting', 'mystery').lower().replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

        # Play Again Button
        if st.button("🔄 Play Again / Open New Case", use_container_width=True):
            reset_game()
            st.rerun()


# ==============================================================================
# ROUTER
# ==============================================================================

def main() -> None:
    """Route application execution according to the active screen in session state."""
    current_screen = st.session_state.get("screen", "start")

    if current_screen == "start":
        render_start_screen()
    elif current_screen == "interrogation":
        render_interrogation_screen()
    elif current_screen == "accusation":
        render_accusation_screen()
    elif current_screen == "end":
        render_end_screen()
    else:
        # Fallback to start
        render_start_screen()


if __name__ == "__main__":
    main()

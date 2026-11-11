"""game_engine.py - Core game logic, state management, and JSON parsing.

This module coordinates the detective game lifecycle: initializing session
state, parsing and validating structured LLM output with retry mechanisms,
tracking clues and vitals, processing interrogation actions, handling high
scores, and compiling transcript exports.
"""

from __future__ import annotations

import datetime
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import streamlit as st

try:
    from . import llm_client
    from . import prompts
except (ImportError, ValueError):
    import llm_client
    import prompts

SCORES_FILE = os.path.join(os.path.dirname(__file__), "scores.json")


# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================

def init_session_state() -> None:
    """Initialize all required keys in Streamlit's session_state."""
    defaults: Dict[str, Any] = {
        "screen": "start",  # "start", "interrogation", "accusation", "end"
        "system_prompt": "",
        "api_messages": [],  # Anthropic format: [{'role': 'user'|'assistant', 'content': str}]
        "chat_history": [],  # Display format: [{'role': 'detective'|'suspect', 'content': str, 'timestamp': str}]
        "trust": 40,
        "stress": 30,
        "clues_found": [],
        "questions_left": 20,
        "max_questions": 20,
        "game_status": "ongoing",  # "ongoing", "won", "lost"
        "notebook": "",
        "settings": {
            "detective_name": "Detective Vance",
            "setting": "Luxury Hotel",
            "difficulty": "Medium",
            "max_questions": 20,
        },
        "accusation_attempts": 0,
        "hints_used": 0,
        "max_hints": 2,
        "debrief": "",
        "final_score": 0,
        "partial_feedback": "",
        "last_error": None,
        "last_failed_action": None,  # For retry mechanism: ('action_name', kwargs)
        "is_processing": False,
        "show_toast_warning": True,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_game() -> None:
    """Reset the game session state to play again while preserving notebook/settings."""
    saved_name = st.session_state.settings.get("detective_name", "Detective Vance")
    st.session_state.screen = "start"
    st.session_state.system_prompt = ""
    st.session_state.api_messages = []
    st.session_state.chat_history = []
    st.session_state.trust = 40
    st.session_state.stress = 30
    st.session_state.clues_found = []
    st.session_state.questions_left = 20
    st.session_state.max_questions = 20
    st.session_state.game_status = "ongoing"
    st.session_state.notebook = ""
    st.session_state.accusation_attempts = 0
    st.session_state.hints_used = 0
    st.session_state.debrief = ""
    st.session_state.final_score = 0
    st.session_state.partial_feedback = ""
    st.session_state.last_error = None
    st.session_state.last_failed_action = None
    st.session_state.is_processing = False
    st.session_state.show_toast_warning = True
    st.session_state.settings["detective_name"] = saved_name


# ==============================================================================
# ROBUST JSON PARSING & VALIDATION
# ==============================================================================

def clean_json_string(raw_text: str) -> str:
    """Strip markdown code fences and extract the outermost JSON object.

    Args:
        raw_text: Raw response string from the LLM.

    Returns:
        str: Extracted candidate JSON substring.
    """
    text = raw_text.strip()

    # Strip markdown code blocks like ```json ... ``` or ``` ... ```
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first fence
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        # Remove last fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # Extract outermost JSON object bracketed by { ... }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1]

    return text


def parse_llm_json(raw_text: str, current_questions: int = 20) -> Dict[str, Any]:
    """Parse and validate JSON response from the LLM with defensive defaults.

    Args:
        raw_text: Output from the Claude API.
        current_questions: Fallback questions remaining.

    Returns:
        Dict[str, Any]: Validated dictionary with expected game schema.

    Raises:
        ValueError: If JSON cannot be decoded.
    """
    cleaned = clean_json_string(raw_text)
    data = json.loads(cleaned)

    if not isinstance(data, dict):
        raise ValueError("Decoded JSON is not a dictionary.")

    # 1. character_reply
    reply = str(data.get("character_reply", "")).strip()
    if not reply:
        reply = "*The suspect remains silent, watching you with cautious eyes.*"

    # 2. trust (clamp 0-100)
    try:
        trust_val = int(data.get("trust", st.session_state.get("trust", 40)))
        trust = max(0, min(100, trust_val))
    except (ValueError, TypeError):
        trust = st.session_state.get("trust", 40)

    # 3. stress (clamp 0-100)
    try:
        stress_val = int(data.get("stress", st.session_state.get("stress", 30)))
        stress = max(0, min(100, stress_val))
    except (ValueError, TypeError):
        stress = st.session_state.get("stress", 30)

    # 4. clues_found
    raw_clues = data.get("clues_found", [])
    if isinstance(raw_clues, list):
        clues = [str(c).strip() for c in raw_clues if str(c).strip()]
    else:
        clues = [str(raw_clues).strip()] if str(raw_clues).strip() else []

    # 5. questions_left
    try:
        q_left_val = int(data.get("questions_left", current_questions))
        questions_left = max(0, q_left_val)
    except (ValueError, TypeError):
        questions_left = max(0, current_questions)

    # 6. game_status
    raw_status = str(data.get("game_status", "ongoing")).strip().lower()
    if raw_status in {"won", "lost", "ongoing"}:
        game_status = raw_status
    else:
        game_status = "ongoing"

    # 7. debrief
    debrief = str(data.get("debrief", "")).strip()

    return {
        "character_reply": reply,
        "trust": trust,
        "stress": stress,
        "clues_found": clues,
        "questions_left": questions_left,
        "game_status": game_status,
        "debrief": debrief,
    }


def execute_llm_turn_with_retry(
    system_prompt: str,
    messages: List[Dict[str, str]],
    fallback_questions: int,
) -> Tuple[Dict[str, Any], str]:
    """Execute LLM call and parse JSON, retrying once if parsing fails.

    Args:
        system_prompt: Game system instructions.
        messages: Conversation history.
        fallback_questions: Fallback count for questions remaining.

    Returns:
        Tuple[Dict[str, Any], str]: (Parsed data dictionary, Raw valid JSON string).

    Raises:
        llm_client.LLMError: If network or provider fails.
        ValueError: If both attempts produce unparseable JSON.
    """
    raw_output = llm_client.call_llm(system_prompt=system_prompt, messages=messages)

    try:
        parsed = parse_llm_json(raw_output, current_questions=fallback_questions)
        return parsed, raw_output
    except Exception:
        # Retry once with a direct correction prompt
        retry_messages = list(messages)
        retry_messages.append({"role": "assistant", "content": raw_output})
        retry_messages.append({"role": "user", "content": prompts.JSON_RETRY_PROMPT})

        second_attempt = llm_client.call_llm(
            system_prompt=system_prompt,
            messages=retry_messages,
            temperature=0.4,
        )

        try:
            parsed = parse_llm_json(second_attempt, current_questions=fallback_questions)
            return parsed, second_attempt
        except Exception as exc:
            raise ValueError(
                "The suspect's response was garbled and could not be interpreted. "
                "Please retry the interrogation turn."
            ) from exc


# ==============================================================================
# CLUE MERGING & STATE HELPERS
# ==============================================================================

def merge_clues(existing_clues: List[str], new_clues: List[str]) -> List[str]:
    """Merge new clues with existing clues while avoiding duplicates."""
    seen = {c.lower(): c for c in existing_clues}
    for clue in new_clues:
        key = clue.lower().strip()
        if key and key not in seen:
            seen[key] = clue
    return list(seen.values())


def get_timestamp() -> str:
    """Return formatted current time string."""
    return datetime.datetime.now().strftime("%I:%M %p")


def calculate_detective_score(
    won: bool,
    questions_left: int,
    max_questions: int,
    clues_count: int,
    trust: int,
    difficulty: str,
    attempts: int,
) -> int:
    """Calculate an objective performance score out of 100."""
    if not won:
        # Consolation points based on clues discovered and rapport
        base = 20 + min(25, clues_count * 5) + int(trust * 0.1)
        return min(55, base)

    # Base win score
    score = 65

    # Efficiency bonus: up to 15 points
    efficiency_ratio = questions_left / max(1, max_questions)
    score += int(efficiency_ratio * 15)

    # Investigation thoroughness: up to 15 points
    score += min(15, clues_count * 3)

    # Rapport bonus: up to 5 points
    if trust >= 60:
        score += 5

    # First attempt bonus
    if attempts <= 1:
        score += 5

    # Difficulty multiplier
    if difficulty.lower() == "hard":
        score += 5
    elif difficulty.lower() == "easy":
        score -= 5

    return max(60, min(100, score))


# ==============================================================================
# GAME ACTIONS
# ==============================================================================

def start_new_game(
    detective_name: str,
    setting: str,
    difficulty: str,
    max_questions: int,
) -> None:
    """Initialize and launch a new mystery investigation."""
    reset_game()

    # Store user settings
    st.session_state.settings = {
        "detective_name": detective_name.strip() or "Detective Vance",
        "setting": setting,
        "difficulty": difficulty,
        "max_questions": int(max_questions),
    }
    st.session_state.questions_left = int(max_questions)
    st.session_state.max_questions = int(max_questions)

    # Construct system prompt with placeholders filled
    system_prompt = (
        prompts.SYSTEM_PROMPT
        .replace("{{setting}}", setting)
        .replace("{{difficulty}}", difficulty)
        .replace("{{max_questions}}", str(max_questions))
    )
    st.session_state.system_prompt = system_prompt

    # Initial start message
    initial_user_msg = prompts.START_GAME_TEMPLATE.format(
        detective_name=st.session_state.settings["detective_name"],
        setting=setting,
        difficulty=difficulty,
        max_questions=max_questions,
    )

    api_msgs = [{"role": "user", "content": initial_user_msg}]

    # Call LLM
    try:
        parsed, raw_json = execute_llm_turn_with_retry(
            system_prompt=system_prompt,
            messages=api_msgs,
            fallback_questions=int(max_questions),
        )

        # Update state
        st.session_state.api_messages = [
            {"role": "user", "content": initial_user_msg},
            {"role": "assistant", "content": raw_json},
        ]
        st.session_state.trust = parsed["trust"]
        st.session_state.stress = parsed["stress"]
        st.session_state.clues_found = parsed["clues_found"]
        st.session_state.questions_left = parsed["questions_left"]
        st.session_state.game_status = parsed["game_status"]

        # Display message
        st.session_state.chat_history.append({
            "role": "suspect",
            "content": parsed["character_reply"],
            "timestamp": get_timestamp(),
        })

        st.session_state.screen = "interrogation"
        st.session_state.last_error = None
        st.session_state.last_failed_action = None

    except Exception as exc:
        st.session_state.last_error = str(exc)
        st.session_state.last_failed_action = ("start_game", {
            "detective_name": detective_name,
            "setting": setting,
            "difficulty": difficulty,
            "max_questions": max_questions,
        })
        raise


def process_question(question_text: str) -> None:
    """Process a detective question during the interrogation turn."""
    if st.session_state.questions_left <= 0:
        return

    question_clean = question_text.strip()
    if not question_clean:
        return

    # Decrement question counter before turn
    current_q = st.session_state.questions_left
    next_q = max(0, current_q - 1)

    # Format user prompt
    clues_summary = ", ".join(st.session_state.clues_found) or "None yet discovered."
    turn_prompt = prompts.QUESTION_TEMPLATE.format(
        question=question_clean,
        questions_left=next_q,
        clues_summary=clues_summary,
    )

    # Record detective message in display chat
    st.session_state.chat_history.append({
        "role": "detective",
        "content": question_clean,
        "timestamp": get_timestamp(),
    })

    # Prepare API messages
    updated_api_msgs = list(st.session_state.api_messages)
    updated_api_msgs.append({"role": "user", "content": turn_prompt})

    try:
        parsed, raw_json = execute_llm_turn_with_retry(
            system_prompt=st.session_state.system_prompt,
            messages=updated_api_msgs,
            fallback_questions=next_q,
        )

        # Update API history
        updated_api_msgs.append({"role": "assistant", "content": raw_json})
        st.session_state.api_messages = updated_api_msgs

        # Update vitals and clues
        st.session_state.trust = parsed["trust"]
        st.session_state.stress = parsed["stress"]
        st.session_state.clues_found = merge_clues(
            st.session_state.clues_found, parsed["clues_found"]
        )
        st.session_state.questions_left = min(next_q, parsed["questions_left"])
        st.session_state.game_status = parsed["game_status"]

        # Append suspect reply to display history
        st.session_state.chat_history.append({
            "role": "suspect",
            "content": parsed["character_reply"],
            "timestamp": get_timestamp(),
        })

        st.session_state.last_error = None
        st.session_state.last_failed_action = None

    except Exception as exc:
        st.session_state.last_error = str(exc)
        st.session_state.last_failed_action = ("question", {"question_text": question_text})
        raise


def process_hint() -> None:
    """Request a subtle investigative hint at the cost of 1 question (max 2 per game)."""
    if st.session_state.hints_used >= st.session_state.max_hints:
        return
    if st.session_state.questions_left <= 0:
        return

    current_q = st.session_state.questions_left
    next_q = max(0, current_q - 1)
    st.session_state.hints_used += 1

    clues_summary = ", ".join(st.session_state.clues_found) or "None yet discovered."
    hint_prompt = prompts.HINT_TEMPLATE.format(
        detective_name=st.session_state.settings["detective_name"],
        questions_left=next_q,
        clues_summary=clues_summary,
    )

    # Note in chat
    st.session_state.chat_history.append({
        "role": "detective",
        "content": "*(Presses the suspect on suspicious inconsistencies, looking for any subtle slip...)*",
        "timestamp": get_timestamp(),
    })

    updated_api_msgs = list(st.session_state.api_messages)
    updated_api_msgs.append({"role": "user", "content": hint_prompt})

    try:
        parsed, raw_json = execute_llm_turn_with_retry(
            system_prompt=st.session_state.system_prompt,
            messages=updated_api_msgs,
            fallback_questions=next_q,
        )

        updated_api_msgs.append({"role": "assistant", "content": raw_json})
        st.session_state.api_messages = updated_api_msgs

        st.session_state.trust = parsed["trust"]
        st.session_state.stress = parsed["stress"]
        st.session_state.clues_found = merge_clues(
            st.session_state.clues_found, parsed["clues_found"]
        )
        st.session_state.questions_left = min(next_q, parsed["questions_left"])

        st.session_state.chat_history.append({
            "role": "suspect",
            "content": parsed["character_reply"],
            "timestamp": get_timestamp(),
        })

        st.session_state.last_error = None
        st.session_state.last_failed_action = None

    except Exception as exc:
        st.session_state.last_error = str(exc)
        st.session_state.last_failed_action = ("hint", {})
        raise


def process_accusation(culprit: str, motive: str, method: str) -> None:
    """Evaluate final accusation submitted by the player."""
    culprit_clean = culprit.strip()
    motive_clean = motive.strip()
    method_clean = method.strip()

    st.session_state.accusation_attempts += 1
    attempt_num = st.session_state.accusation_attempts

    clues_summary = ", ".join(st.session_state.clues_found) or "None yet discovered."
    accusation_prompt = prompts.ACCUSATION_TEMPLATE.format(
        culprit=culprit_clean,
        motive=motive_clean,
        method=method_clean,
        attempt=attempt_num,
        clues_summary=clues_summary,
    )

    # Record accusation in chat
    st.session_state.chat_history.append({
        "role": "detective",
        "content": (
            f"**OFFICIAL INDICTMENT:**\n"
            f"- **Culprit:** {culprit_clean}\n"
            f"- **Motive:** {motive_clean}\n"
            f"- **Method:** {method_clean}"
        ),
        "timestamp": get_timestamp(),
    })

    updated_api_msgs = list(st.session_state.api_messages)
    updated_api_msgs.append({"role": "user", "content": accusation_prompt})

    try:
        parsed, raw_json = execute_llm_turn_with_retry(
            system_prompt=st.session_state.system_prompt,
            messages=updated_api_msgs,
            fallback_questions=st.session_state.questions_left,
        )

        updated_api_msgs.append({"role": "assistant", "content": raw_json})
        st.session_state.api_messages = updated_api_msgs

        status = parsed["game_status"]
        st.session_state.game_status = status
        st.session_state.debrief = parsed["debrief"]

        # Record suspect's response to accusation
        st.session_state.chat_history.append({
            "role": "suspect",
            "content": parsed["character_reply"],
            "timestamp": get_timestamp(),
        })

        if status == "won":
            score = calculate_detective_score(
                won=True,
                questions_left=st.session_state.questions_left,
                max_questions=st.session_state.max_questions,
                clues_count=len(st.session_state.clues_found),
                trust=st.session_state.trust,
                difficulty=st.session_state.settings["difficulty"],
                attempts=attempt_num,
            )
            st.session_state.final_score = score
            save_high_score(
                name=st.session_state.settings["detective_name"],
                difficulty=st.session_state.settings["difficulty"],
                score=score,
                setting=st.session_state.settings["setting"],
            )
            st.session_state.screen = "end"

        elif status == "ongoing":
            # Partially correct accusation
            if attempt_num >= 2:
                # Exhausted second attempt -> Lost
                st.session_state.game_status = "lost"
                score = calculate_detective_score(
                    won=False,
                    questions_left=st.session_state.questions_left,
                    max_questions=st.session_state.max_questions,
                    clues_count=len(st.session_state.clues_found),
                    trust=st.session_state.trust,
                    difficulty=st.session_state.settings["difficulty"],
                    attempts=attempt_num,
                )
                st.session_state.final_score = score
                st.session_state.screen = "end"
            else:
                # Store partial feedback and return to interrogation
                st.session_state.partial_feedback = (
                    parsed["debrief"]
                    or "Your accusation was partially accurate, but key motives or methods remain unproven. You have 1 final attempt remaining!"
                )
                st.session_state.screen = "interrogation"

        else:
            # Lost
            score = calculate_detective_score(
                won=False,
                questions_left=st.session_state.questions_left,
                max_questions=st.session_state.max_questions,
                clues_count=len(st.session_state.clues_found),
                trust=st.session_state.trust,
                difficulty=st.session_state.settings["difficulty"],
                attempts=attempt_num,
            )
            st.session_state.final_score = score
            st.session_state.screen = "end"

        st.session_state.last_error = None
        st.session_state.last_failed_action = None

    except Exception as exc:
        st.session_state.last_error = str(exc)
        st.session_state.last_failed_action = ("accusation", {
            "culprit": culprit,
            "motive": motive,
            "method": method,
        })
        raise


def retry_last_action() -> None:
    """Retry the last failed action if an API error occurred."""
    if not st.session_state.last_failed_action:
        return

    action_name, kwargs = st.session_state.last_failed_action
    st.session_state.last_error = None

    if action_name == "start_game":
        start_new_game(**kwargs)
    elif action_name == "question":
        process_question(**kwargs)
    elif action_name == "hint":
        process_hint()
    elif action_name == "accusation":
        process_accusation(**kwargs)


# ==============================================================================
# HIGH SCORES
# ==============================================================================

def load_high_scores() -> List[Dict[str, Any]]:
    """Load and return high scores from scores.json, sorted by score descending."""
    if not os.path.exists(SCORES_FILE):
        return []

    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as file:
            scores = json.load(file)
            if isinstance(scores, list):
                # Sort descending by score
                scores.sort(key=lambda s: int(s.get("score", 0)), reverse=True)
                return scores[:5]
    except Exception:
        pass
    return []


def save_high_score(name: str, difficulty: str, score: int, setting: str) -> None:
    """Save a new score entry to scores.json."""
    scores: List[Dict[str, Any]] = []
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as file:
                loaded = json.load(file)
                if isinstance(loaded, list):
                    scores = loaded
        except Exception:
            scores = []

    new_entry = {
        "name": name.strip() or "Detective Vance",
        "difficulty": difficulty,
        "score": int(score),
        "setting": setting,
        "date": datetime.date.today().strftime("%Y-%m-%d"),
    }
    scores.append(new_entry)
    scores.sort(key=lambda s: int(s.get("score", 0)), reverse=True)

    try:
        with open(SCORES_FILE, "w", encoding="utf-8") as file:
            json.dump(scores[:20], file, indent=2)
    except Exception:
        pass


# ==============================================================================
# TRANSCRIPT EXPORT
# ==============================================================================

def generate_transcript() -> str:
    """Compile the complete investigation into a clean text transcript."""
    settings = st.session_state.get("settings", {})
    detective_name = settings.get("detective_name", "Detective Vance")
    setting = settings.get("setting", "Unknown")
    difficulty = settings.get("difficulty", "Medium")
    max_q = settings.get("max_questions", 20)
    q_left = st.session_state.get("questions_left", 0)
    status = st.session_state.get("game_status", "ongoing").upper()
    score = st.session_state.get("final_score", 0)

    lines: List[str] = [
        "=" * 72,
        "         MYSTERY WORD & CLUE DETECTIVE - OFFICIAL CASE DOSSIER",
        "=" * 72,
        f"Date:           {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Lead Detective: {detective_name}",
        f"Case Setting:   {setting}",
        f"Difficulty:     {difficulty}",
        f"Final Status:   {status}",
        f"Final Score:    {score} / 100",
        f"Questions Used: {max_q - q_left} of {max_q}",
        "-" * 72,
        "",
        "--- EVIDENCE LOGGED & CLUES UNCOVERED ---",
    ]

    clues = st.session_state.get("clues_found", [])
    if clues:
        for idx, clue in enumerate(clues, 1):
            lines.append(f"  [{idx}] {clue}")
    else:
        lines.append("  (No conclusive physical evidence logged)")

    lines.append("")
    lines.append("--- DETECTIVE'S FIELD NOTEBOOK ---")
    notebook = st.session_state.get("notebook", "").strip()
    if notebook:
        for line in notebook.splitlines():
            lines.append(f"  > {line}")
    else:
        lines.append("  (Notebook was blank)")

    lines.append("")
    lines.append("=" * 72)
    lines.append("                  RECORDED INTERROGATION DIALOGUE")
    lines.append("=" * 72)
    lines.append("")

    chat_history = st.session_state.get("chat_history", [])
    for msg in chat_history:
        role_label = detective_name.upper() if msg["role"] == "detective" else "SUSPECT/WITNESS"
        time_str = msg.get("timestamp", "")
        lines.append(f"[{time_str}] {role_label}:")
        for text_line in str(msg["content"]).splitlines():
            lines.append(f"    {text_line}")
        lines.append("")

    lines.append("=" * 72)
    lines.append("                   FINAL DEBRIEF & REVEALED TRUTH")
    lines.append("=" * 72)
    debrief = st.session_state.get("debrief", "").strip()
    if debrief:
        for debrief_line in debrief.splitlines():
            lines.append(f"  {debrief_line}")
    else:
        lines.append("  (Investigation closed without debrief statement)")

    lines.append("")
    lines.append("=" * 72)
    lines.append("                          END OF FILE")
    lines.append("=" * 72)

    return "\n".join(lines)

# 🕵️ Mystery Word & Clue Detective

An AI-powered noir detective interrogation game built with **Python**, **Streamlit**, and the **Anthropic Claude API**. 

Take on the role of a lead detective interrogating a virtual suspect or witness played by Claude. Sift through lies and half-truths, monitor the suspect's psychological vitals (Trust & Stress), collect tangible clues, and bring down a final indictment before your questions run out.

---

## 🌟 Key Features

- **Atmospheric 1940s Noir Aesthetic**: Deep charcoal palette, vintage serif headers, warm brass accents, and custom dossier card layouts.
- **Dynamic Virtual Suspect**: Powered by Claude with vivid in-character dialogue and atmospheric physical action cues (e.g., `*fidgets with cigarette*`, `*eyes dart to the mantelpiece*`).
- **Psychological Vitals**: Real-time **Trust** and **Stress** meters that react dynamically to your interrogation style (aggressive pressure vs. empathetic rapport).
- **Evidence Management**: Automatically logs newly uncovered clues in the sidebar dossier and keeps an in-session **Detective Notebook**.
- **Hint System**: Request up to 2 subtle in-character clues per case at the cost of 1 question.
- **Two-Stage Accusation System**: Submit your formal indictment specifying **Culprit**, **Motive**, and **Method**. If you identify the right person but miss key details, the court grants one final attempt with corrective feedback.
- **Full Case Debrief & Scoring**: Unlocks the full secret truth, plot twists, performance score (out of 100), and a downloadable `.txt` case transcript.
- **Local Leaderboard**: Persists top scores locally in `scores.json`.

---

## 📂 Project Structure

```
mystery_detective/
├── app.py              # Streamlit UI, screen routing, and component rendering
├── game_engine.py      # Core game logic, state management, and robust JSON parsing
├── llm_client.py       # Isolated Anthropic Claude API provider interface
├── prompts.py          # System prompt and turn message templates
├── styles.py           # Custom noir CSS styles and vital meter renderers
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── README.md           # Setup, running instructions, and gameplay manual
```

---

## 🛠️ Prerequisites

- **Python 3.10+**
- An **Anthropic Claude API Key** ([console.anthropic.com](https://console.anthropic.com/))

---

## 🚀 Setup & Installation

### 1. Clone or Navigate to the Project Directory

```bash
cd mystery_detective
```

### 2. Create and Activate a Virtual Environment (Recommended)

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Your API Key

Create a `.env` file in the `mystery_detective/` directory (you can copy `.env.example`):

```bash
cp .env.example .env
```

Open `.env` and insert your Anthropic Claude API key:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
MODEL_NAME=claude-3-5-sonnet-20241022
```

*(Alternatively, you can place your key in `.streamlit/secrets.toml` under `ANTHROPIC_API_KEY = "sk-..."`)*.

---

## 🎮 How to Run

Launch the Streamlit web application:

```bash
streamlit run app.py
```

The app will start and automatically open in your default browser at `http://localhost:8501`.

---

## 📖 How to Play

### 1. Case Initiation (Start Screen)
- Enter your **Detective Name**.
- Choose your **Crime Scene Setting** (e.g. *Luxury Hotel*, *Train Journey*, *University Lab*, *Old Mansion*, or *Random*).
- Select your **Difficulty Level**:
  - **Easy**: Suspect is nervous, cooperative with empathetic questioning, and slips up easily (4 discoverable clues).
  - **Medium**: Suspect holds secrets and has a crafted alibi (5 discoverable clues).
  - **Hard**: Suspect is shrewd, calculating, and manipulative (6 discoverable clues).
- Set your **Question Allowance** (10–30 questions).
- Click **Start Investigation**.

### 2. Interrogation Chamber (Main Game)
- Type your questions in the interrogation chat box at the bottom.
- Observe the suspect's replies and physical cues in *italics*.
- **Monitor the Vitals:**
  - **🤝 Trust**: Increases when you approach with empathy or validate their emotions. High trust encourages willing revelations.
  - **⚡ Stress**: Increases when you confront them with contradictions, timestamps, or physical evidence. High stress triggers slips and panicked admissions.
- Keep personal notes in the **Detective's Field Notebook** in the sidebar.
- If you're stuck, use the **💡 Request Hint** button (max 2 per game, costs 1 question).

### 3. The Final Indictment (Accusation Screen)
- When you have pieced together the puzzle (or when questions reach 0), click **Make Final Accusation**.
- Fill in:
  1. **The Culprit** (*Who did it?*)
  2. **The Motive** (*Why did they do it?*)
  3. **The Method** (*How was it executed?*)
- If partially correct, you will receive judicial feedback and return to the interrogation with 1 final attempt remaining!

### 4. Case Closure (End Screen)
- View the dramatic outcome and suspect's final confession or exit.
- Uncover the **Full Revealed Truth**, the secret **Plot Twist**, and your final score out of 100.
- Click **📥 Download Case Transcript** to export the entire investigation log as a `.txt` file.
- View your ranking on the high-score leaderboard.

---

## 🔒 Security & Code Standards

- **No Hard-coded Secrets**: Credentials are strictly loaded from `.env` or Streamlit secrets.
- **Provider Isolation**: `llm_client.py` is completely decoupled; you can swap LLM providers without touching UI or game logic.
- **Robust Output Handling**: Defensively extracts and validates JSON structures, with automated single-turn recovery if the model ever outputs malformed formatting.
- **Pure Session Isolation**: All gameplay state is isolated per user session in `st.session_state`.


"""styles.py - Custom dark noir detective styling for Streamlit.

Injects tailored CSS for a moody 1940s detective interrogation ambiance:
charcoal backdrop, warm amber/brass typography, case file dossiers,
custom evidence cards, and styled vital meters.
"""

import streamlit as st


NOIR_CSS = """
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;900&family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=Playfair+Display:ital,wght@0,600;0,800;1,400&family=Inter:wght@300;400;500;600&display=swap');

/* Main App Container Styling */
.stApp {
    background-color: #0d0f14;
    color: #e2ddd0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Headings with Vintage Serif / Noir Typeface */
h1, h2, h3, h4, .noir-heading {
    font-family: 'Cinzel', 'Playfair Display', Georgia, serif !important;
    color: #e5b24c !important;
    letter-spacing: 0.04em;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.7);
}

/* Sidebar Dossier Aesthetic */
section[data-testid="stSidebar"] {
    background-color: #12151c !important;
    border-right: 1px solid #2a251b !important;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Hero Banner on Start Screen */
.noir-hero-banner {
    background: linear-gradient(145deg, #161922 0%, #0d0f14 100%);
    border: 1px solid #383020;
    border-left: 6px solid #d4af37;
    padding: 2.2rem 2.5rem;
    border-radius: 8px;
    margin-bottom: 1.8rem;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
}

.noir-hero-title {
    font-family: 'Cinzel', serif;
    font-size: 2.3rem;
    font-weight: 900;
    color: #f0c353;
    letter-spacing: 0.06em;
    margin: 0;
    text-transform: uppercase;
}

.noir-hero-tagline {
    font-family: 'Playfair Display', Georgia, serif;
    font-style: italic;
    font-size: 1.15rem;
    color: #aba290;
    margin-top: 0.5rem;
    margin-bottom: 0;
}

/* Case File Card */
.case-card {
    background-color: #141720;
    border: 1px solid #2d261a;
    border-radius: 6px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.03), 0 4px 12px rgba(0, 0, 0, 0.4);
}

.case-card-header {
    font-family: 'Cinzel', serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: #e5b24c;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid #2d261a;
    padding-bottom: 0.4rem;
    margin-bottom: 0.8rem;
}

/* Clue Badges & Evidence Tags */
.evidence-badge {
    background-color: #1a1e29;
    border: 1px solid #443720;
    border-left: 3px solid #d4af37;
    color: #e8d8b8;
    padding: 0.6rem 0.8rem;
    border-radius: 4px;
    font-family: 'Courier Prime', monospace;
    font-size: 0.88rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Action cues italic styling inside messages */
.stChatMessage em, .stChatMessage i, .noir-italic {
    color: #f1c40f !important;
    font-style: italic !important;
    font-family: 'Playfair Display', Georgia, serif;
}

/* Chat Message Customizations */
div[data-testid="stChatMessage"] {
    background-color: #13161e;
    border: 1px solid #232833;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.8rem;
}

/* Custom Metric Display */
.metric-box {
    background: #141822;
    border: 1px solid #332b1d;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    text-align: center;
    margin-bottom: 0.8rem;
}

.metric-number {
    font-family: 'Cinzel', serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: #f0c353;
    line-height: 1.1;
}

.metric-label {
    font-size: 0.78rem;
    color: #9c9281;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.2rem;
}

/* Meters (Trust & Stress) */
.vital-bar-container {
    margin-bottom: 1rem;
}

.vital-bar-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.35rem;
}

.vital-bar-bg {
    background-color: #1a1e27;
    border-radius: 6px;
    height: 10px;
    overflow: hidden;
    border: 1px solid #272d3b;
}

.vital-bar-fill-trust {
    background: linear-gradient(90deg, #1b7a43 0%, #2ecc71 100%);
    height: 100%;
    transition: width 0.5s ease-in-out;
}

.vital-bar-fill-stress {
    background: linear-gradient(90deg, #b02a1b 0%, #e74c3c 100%);
    height: 100%;
    transition: width 0.5s ease-in-out;
}

/* Warning & Alerts */
.partial-alert-box {
    background-color: #291e10;
    border: 1px solid #85531b;
    border-left: 5px solid #f39c12;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin-bottom: 1.2rem;
    color: #f7d8a6;
}

.danger-alert-box {
    background-color: #2b1212;
    border: 1px solid #822222;
    border-left: 5px solid #e74c3c;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin-bottom: 1.2rem;
    color: #f5baba;
}

/* Victory / Loss Banners */
.win-banner {
    background: linear-gradient(135deg, #0e2b1b 0%, #174229 100%);
    border: 2px solid #2ecc71;
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 1.8rem;
    box-shadow: 0 8px 30px rgba(46, 204, 113, 0.2);
}

.lost-banner {
    background: linear-gradient(135deg, #2b1111 0%, #441a1a 100%);
    border: 2px solid #e74c3c;
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 1.8rem;
    box-shadow: 0 8px 30px rgba(231, 76, 60, 0.2);
}

/* Custom styled buttons */
.stButton > button {
    background-color: #1a1e28 !important;
    color: #e5b24c !important;
    border: 1px solid #524227 !important;
    border-radius: 4px !important;
    font-family: 'Cinzel', serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    transition: all 0.2s ease-in-out !important;
}

.stButton > button:hover {
    background-color: #252b3a !important;
    border-color: #f0c353 !important;
    color: #ffffff !important;
    box-shadow: 0 0 12px rgba(240, 195, 83, 0.25) !important;
}

/* Textarea styling for notebook */
.stTextArea textarea {
    background-color: #10131a !important;
    color: #e2ddd0 !important;
    border: 1px solid #2c2518 !important;
    font-family: 'Courier Prime', monospace !important;
    font-size: 0.88rem !important;
}

.stTextArea textarea:focus {
    border-color: #d4af37 !important;
    box-shadow: 0 0 8px rgba(212, 175, 55, 0.3) !important;
}

/* High Score Table */
.scores-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
    margin-top: 0.5rem;
}

.scores-table th {
    font-family: 'Cinzel', serif;
    color: #d4af37;
    text-align: left;
    padding: 0.5rem;
    border-bottom: 1px solid #332a1b;
    font-size: 0.8rem;
}

.scores-table td {
    padding: 0.5rem;
    border-bottom: 1px solid #1c202a;
    color: #c9c2b1;
}

/* Expander custom styling */
.streamlit-expanderHeader {
    background-color: #141720 !important;
    border: 1px solid #2c2518 !important;
    color: #d4af37 !important;
}
</style>
"""


def apply_custom_styles() -> None:
    """Inject custom noir CSS styles into the active Streamlit app."""
    st.markdown(NOIR_CSS, unsafe_allow_html=True)


def render_vital_meter(label: str, emoji: str, value: int, meter_type: str = "trust") -> None:
    """Render a custom styled visual progress meter for trust or stress.

    Args:
        label: Display name (e.g., 'Suspect Trust').
        emoji: Atmospheric icon.
        value: Percentage integer 0-100.
        meter_type: 'trust' (green) or 'stress' (red).
    """
    fill_class = "vital-bar-fill-trust" if meter_type == "trust" else "vital-bar-fill-stress"
    color = "#2ecc71" if meter_type == "trust" else "#e74c3c"

    html = f"""
    <div class="vital-bar-container">
        <div class="vital-bar-header">
            <span>{emoji} {label}</span>
            <span style="color: {color}; font-weight: bold;">{value}%</span>
        </div>
        <div class="vital-bar-bg">
            <div class="{fill_class}" style="width: {value}%;"></div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


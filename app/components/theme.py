"""
Theme module: injects custom CSS to give DatAInspire Task Command Center
a distinctive "mission control" identity rather than default Streamlit
styling. Supports light and dark mode via a session-state toggle.

Design language:
  - Display face: a tight, geometric sans (Space Grotesk) for headers —
    reads like instrumentation/telemetry labels.
  - Body: Inter for readability at small sizes.
  - Mono: JetBrains Mono for task codes, timestamps, IDs — reinforces the
    "system of record" feel.
  - Signature element: the colored left-edge priority rail on task cards
    (red/amber/green) echoing mission-control status lighting, plus
    radial "signal" badges on the dashboard KPIs.
"""

import streamlit as st

DARK_THEME = {
    "bg": "#0B0E14",
    "surface": "#141821",
    "surface_alt": "#1B202C",
    "border": "#262C3A",
    "text": "#E7EAF0",
    "text_muted": "#8B93A7",
    "accent": "#6C5CE7",
    "accent_soft": "#6C5CE71A",
}

LIGHT_THEME = {
    "bg": "#F6F7FB",
    "surface": "#FFFFFF",
    "surface_alt": "#F0F1F7",
    "border": "#E2E5EE",
    "text": "#1B1F2A",
    "text_muted": "#5C6478",
    "accent": "#5B4BD6",
    "accent_soft": "#5B4BD61A",
}


def get_theme():
    mode = st.session_state.get("theme_mode", "dark")
    return DARK_THEME if mode == "dark" else LIGHT_THEME


def inject_css():
    t = get_theme()
    st.html(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
        :root {{
            --bg: {t['bg']};
            --surface: {t['surface']};
            --surface-alt: {t['surface_alt']};
            --border: {t['border']};
            --text: {t['text']};
            --text-muted: {t['text_muted']};
            --accent: {t['accent']};
            --accent-soft: {t['accent_soft']};
            --red: #E63946;
            --amber: #F4A300;
            --green: #2A9D8F;
        }}

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background: var(--bg);
            color: var(--text);
        }}

        h1, h2, h3, h4 {{
            font-family: 'Space Grotesk', sans-serif !important;
            letter-spacing: -0.02em;
            color: var(--text) !important;
        }}

        code, .mono {{
            font-family: 'JetBrains Mono', monospace !important;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background: var(--surface);
            border-right: 1px solid var(--border);
        }}

        /* Top brand block */
        .dc-brand {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 4px 0 18px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 14px;
        }}
        .dc-brand-mark {{
            width: 34px; height: 34px;
            border-radius: 9px;
            background: linear-gradient(135deg, var(--accent), #8E7CFF);
            display: flex; align-items: center; justify-content: center;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700; color: white; font-size: 15px;
        }}
        .dc-brand-text {{
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700;
            font-size: 15px;
            line-height: 1.1;
            color: var(--text);
        }}
        .dc-brand-sub {{
            font-size: 11px;
            color: var(--text-muted);
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}

        /* KPI cards */
        .dc-kpi {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 18px 20px;
            position: relative;
            overflow: hidden;
        }}
        .dc-kpi::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: var(--kpi-color, var(--accent));
        }}
        .dc-kpi-label {{
            font-size: 11.5px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-muted);
            font-weight: 600;
            margin-bottom: 6px;
        }}
        .dc-kpi-value {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 30px;
            font-weight: 700;
            color: var(--text);
            line-height: 1;
        }}
        .dc-kpi-delta {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 6px;
        }}

        /* Task card */
        .dc-task-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-left: 4px solid var(--rail-color, var(--accent));
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 10px;
        }}
        .dc-task-code {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: var(--text-muted);
            letter-spacing: 0.03em;
        }}
        .dc-task-title {{
            font-weight: 600;
            font-size: 15px;
            color: var(--text);
            margin: 2px 0 6px 0;
        }}
        .dc-meta-row {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 8px;
        }}

        /* Badges */
        .dc-badge {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 11.5px;
            font-weight: 600;
            border: 1px solid var(--badge-color, var(--accent));
            color: var(--badge-color, var(--accent));
            background: color-mix(in srgb, var(--badge-color, var(--accent)) 12%, transparent);
        }}
        .dc-dot {{
            width: 7px; height: 7px;
            border-radius: 50%;
            background: var(--badge-color, var(--accent));
            display: inline-block;
        }}

        /* Section divider label */
        .dc-section-label {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--text-muted);
            margin: 6px 0 10px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .dc-section-label::after {{
            content: '';
            flex: 1;
            height: 1px;
            background: var(--border);
        }}

        /* Buttons */
        .stButton > button {{
            border-radius: 8px;
            font-weight: 600;
            border: 1px solid var(--border);
        }}
        .stButton > button[kind="primary"] {{
            background: var(--accent);
            border: none;
        }}

        /* Comment bubble */
        .dc-comment {{
            background: var(--surface-alt);
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 8px;
        }}
        .dc-comment-meta {{
            font-size: 11px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }}
        .dc-comment-author {{
            font-weight: 600;
            color: var(--text);
        }}

        /* Login screen */
        .dc-login-wrap {{
            max-width: 420px;
            margin: 6vh auto 0 auto;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 36px 32px;
        }}
        .dc-login-mark {{
            width: 52px; height: 52px;
            border-radius: 14px;
            background: linear-gradient(135deg, var(--accent), #8E7CFF);
            display: flex; align-items: center; justify-content: center;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700; color: white; font-size: 22px;
            margin-bottom: 16px;
        }}

        div[data-testid="stMetricValue"] {{
            font-family: 'Space Grotesk', sans-serif;
        }}

        hr {{ border-color: var(--border); }}
        </style>
        """
    )


def priority_badge_html(priority: str) -> str:
    colors = {"High": "var(--red)", "Medium": "var(--amber)", "Low": "var(--green)"}
    color = colors.get(priority, "var(--accent)")
    return f'<span class="dc-badge" style="--badge-color:{color}"><span class="dc-dot" style="--badge-color:{color}"></span>{priority}</span>'


def status_badge_html(status: str) -> str:
    colors = {
        "Not Started": "#94A3B8",
        "In Progress": "#3B82F6",
        "Submitted for Review": "#A855F7",
        "Approved": "var(--green)",
        "Returned for Revision": "#F97316",
    }
    color = colors.get(status, "var(--accent)")
    return f'<span class="dc-badge" style="--badge-color:{color}"><span class="dc-dot" style="--badge-color:{color}"></span>{status}</span>'
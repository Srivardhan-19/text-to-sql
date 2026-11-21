"""
CSS Styling and Layout Customization for Modern Streamlit UI.
Professional slate/indigo palette, clean card elevations, glassmorphism accents,
and refined syntax & button styling.
"""

CUSTOM_CSS = """
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Header Styling */
    .main-header-container {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.2);
    }
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        background: linear-gradient(90deg, #38BDF8, #818CF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.35rem;
        letter-spacing: -0.02em;
    }
    .sub-title {
        font-size: 1.02rem;
        color: #94A3B8;
        font-weight: 400;
        line-height: 1.5;
    }

    /* Card Panels */
    .app-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Custom Metric Badges */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.3rem 0.8rem;
        font-size: 0.82rem;
        font-weight: 600;
        border-radius: 9999px;
    }
    .badge-success {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-info {
        background-color: rgba(56, 189, 248, 0.15);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .badge-warning {
        background-color: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    /* Text Area / Code Editor enhancements */
    .stTextArea textarea {
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        font-size: 0.95rem !important;
        background-color: #0F172A !important;
        color: #38BDF8 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        line-height: 1.5 !important;
    }

    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background-color: #0B1120;
        border-right: 1px solid #1E293B;
    }

    /* Interactive Buttons */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 0.55rem 1.2rem !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3) !important;
    }
    .stButton>button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.45) !important;
    }

    /* Table styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
"""

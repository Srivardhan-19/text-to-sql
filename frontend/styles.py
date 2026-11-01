"""
CSS Styling and Layout Customization for Streamlit Application.
"""

CUSTOM_CSS = """
<style>
    /* Clean academic typography & layout */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .metric-title {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0F172A;
    }
    .badge-success {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #DEF7EC;
        color: #03543F;
    }
    .badge-warning {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #FEF08A;
        color: #854D0E;
    }
    .sql-box {
        background-color: #1E293B;
        color: #F8FAFC;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.95rem;
    }
</style>
"""


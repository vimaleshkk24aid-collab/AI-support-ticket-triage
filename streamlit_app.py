"""
Streamlit frontend for the AI Support Ticket Triage & Smart Reply System.

UI-only: it never loads the ML model or parses files itself. Every result
comes from the FastAPI backend over HTTP.

Run with:
    streamlit run frontend/streamlit_app.py

Make sure the backend is running first (uvicorn backend.main:app --reload).
"""

import json
import os
import sys

import plotly.graph_objects as go
import requests
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import API_BASE_URL, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB  # noqa: E402

st.set_page_config(page_title="AI Support Ticket Triage", page_icon="🎫", layout="wide")

st.markdown(
    """
    <style>
    .main-header {font-size: 2.2rem; font-weight: 700; color: #1f2937; margin-bottom: 0.2rem;}
    .sub-header {font-size: 1.05rem; color: #6b7280; margin-bottom: 1.5rem;}
    .pill {display: inline-block; border-radius: 999px; padding: 0.25rem 0.75rem;
           margin: 0.2rem; font-size: 0.85rem; font-weight: 600;}
    .pill-ok {background: #d1fae5; color: #065f46;}
    .pill-miss {background: #fee2e2; color: #991b1b;}
    .pill-info {background: #e0e7ff; color: #3730a3;}
    .badge {display: inline-block; border-radius: 8px; padding: 0.4rem 1rem;
            font-size: 1.3rem; font-weight: 700;}
    .badge-High {background: #fee2e2; color: #991b1b;}
    .badge-Medium {background: #fef9c3; color: #854d0e;}
    .badge-Low {background: #d1fae5; color: #065f46;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">🎫 AI Support Ticket Triage & Smart Reply</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Upload or paste a customer ticket to get its category, priority, sentiment, '
    'matching help articles and a ready-to-edit reply.</div>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def backend_status():
    try:
        resp = requests.get(f"{API_BASE_URL}/health", timeout=3)
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.RequestException:
        pass
    return None


def call_full_analysis(file=None, ticket_text: str = ""):
    files = {"file": (file.name, file.getvalue())} if file is not None else None
    data = {"ticket_text": ticket_text} if ticket_text else {}
    try:
        resp = requests.post(f"{API_BASE_URL}/full-analysis", files=files, data=data, timeout=60)
    except requests.exceptions.RequestException:
        return None, f"Could not reach the backend API. Is FastAPI running on {API_BASE_URL}?"
    if resp.status_code == 200:
        return resp.json(), None
    try:
        detail = resp.json().get("detail", "An unknown error occurred.")
    except ValueError:
        detail = "An unknown error occurred while contacting the backend."
    return None, detail


def show_chart(fig):
    """Works on both old and new Streamlit versions."""
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def pills(items, css):
    return "".join(f'<span class="pill {css}">{i}</span>' for i in items)


def gauge(score: float, title: str):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, number={"suffix": "%"}, title={"text": title},
        gauge={
            "axis": {"range": [0, 100]}, "bar": {"color": "#2563eb"},
            "steps": [
                {"range": [0, 15], "color": "#fee2e2"},
                {"range": [15, 35], "color": "#fef9c3"},
                {"range": [35, 100], "color": "#d1fae5"},
            ],
        },
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=10))
    return fig


def sentiment_gauge(score: float):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, title={"text": "Sentiment (-1 to +1)"},
        gauge={
            "axis": {"range": [-1, 1]}, "bar": {"color": "#6366f1"},
            "steps": [
                {"range": [-1, -0.2], "color": "#fee2e2"},
                {"range": [-0.2, 0.2], "color": "#f3f4f6"},
                {"range": [0.2, 1], "color": "#d1fae5"},
            ],
        },
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=10))
    return fig


def confidence_chart(probabilities: dict):
    if not probabilities:
        return None
    items = sorted(probabilities.items(), key=lambda x: x[1])
    fig = go.Figure(go.Bar(x=[round(v * 100, 1) for _, v in items], y=[k for k, _ in items],
                           orientation="h", marker_color="#6366f1"))
    fig.update_layout(title="Category Prediction Confidence", xaxis_title="Confidence (%)",
                      height=340, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def keyword_chart(counts: dict):
    if not counts:
        return None
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    fig = go.Figure(go.Bar(x=[k for k, _ in items], y=[v for _, v in items], marker_color="#f59e0b"))
    fig.update_layout(title="Issue Keyword Mentions", yaxis_title="Mentions", height=320, margin=dict(t=50))
    return fig


def report_text(r: dict) -> str:
    info = r["ticket_info"]
    lines = [
        "SUPPORT TICKET TRIAGE REPORT", "=" * 30,
        f"Customer : {info['customer_name']}", f"Email    : {info['email']}",
        f"Phone    : {info['phone']}", f"Order ID : {info['order_id']}",
        f"Subject  : {info['subject']}", "",
        f"Category : {r['category']} ({r['confidence'] * 100:.1f}% confidence)",
        f"Priority : {r['priority']['level']}  ({'; '.join(r['priority']['reasons'])})",
        f"Sentiment: {r['sentiment']['label']} ({r['sentiment']['score']})",
        f"KB match : {r['match_score']}%", "", "Recommendations:",
    ]
    lines += [f" - {x}" for x in r["recommendations"]]
    lines += ["", "Draft reply:", r["draft_reply"]]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    st.write(f"**Backend API:** `{API_BASE_URL}`")
    status = backend_status()
    if status:
        st.success("Backend is reachable ✅")
        st.caption(f"Model loaded: {'✅' if status.get('model_loaded') else '❌ run ml/train.py'}")
        st.caption(f"Knowledge base: {'✅' if status.get('knowledge_base_loaded') else '❌'}")
    else:
        st.error("Backend is NOT reachable ❌")
        st.caption("Start it with:\n\n`uvicorn backend.main:app --reload`")
    st.markdown("---")
    st.caption(f"Allowed file types: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    st.caption(f"Max file size: {MAX_FILE_SIZE_MB} MB")

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------
tab_upload, tab_paste = st.tabs(["📎 Upload ticket file", "✍️ Paste ticket text"])
with tab_upload:
    uploaded_file = st.file_uploader("Choose a PDF, DOCX or TXT file", type=["pdf", "docx", "txt"])
with tab_paste:
    pasted_text = st.text_area("Ticket text", height=200, placeholder="Paste the customer's message here...")

analyze_clicked = st.button("🔍 Analyze Ticket", type="primary")
st.markdown("---")

if analyze_clicked:
    if uploaded_file is None and not pasted_text.strip():
        st.warning("Please upload a ticket file or paste the ticket text.")
    elif uploaded_file is not None and uploaded_file.size == 0:
        st.error("The uploaded file is empty.")
    elif uploaded_file is not None and uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        st.error(f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB.")
    else:
        with st.spinner("Analyzing ticket..."):
            if uploaded_file is not None:
                result, error = call_full_analysis(file=uploaded_file)
            else:
                result, error = call_full_analysis(ticket_text=pasted_text)

        if error:
            st.error(f"⚠️ {error}")
        else:
            info = result["ticket_info"]

            st.subheader("👤 Customer & Ticket Details")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Name", info["customer_name"])
            c2.metric("Email", info["email"])
            c3.metric("Phone", info["phone"])
            c4.metric("Order ID", info["order_id"])
            st.caption(f"**Subject:** {info['subject']}  |  **Amount:** {info['amount']}  |  **Device:** {info['device']}")
            st.markdown("---")

            # Category + priority
            left, right = st.columns([1, 1])
            with left:
                st.subheader("🤖 AI Category Prediction")
                st.info(f"**Predicted Category:** {result['category']}")
                st.caption(f"Confidence: {result['confidence'] * 100:.1f}%")
                fig = confidence_chart(result["category_probabilities"])
                if fig:
                    show_chart(fig)
            with right:
                st.subheader("🚦 Priority & Sentiment")
                level = result["priority"]["level"]
                st.markdown(f'<span class="badge badge-{level}">{level} priority</span>', unsafe_allow_html=True)
                for reason in result["priority"]["reasons"]:
                    st.caption(f"• {reason}")
                st.markdown(f"**Sentiment:** {result['sentiment']['label']}")
                show_chart(sentiment_gauge(result["sentiment"]["score"]))
            st.markdown("---")

            # KB match
            st.subheader("📚 Knowledge-Base Match")
            g, a = st.columns([1, 2])
            with g:
                show_chart(gauge(result["match_score"], "Best Article Relevance"))
            with a:
                if result["suggested_articles"]:
                    for art in result["suggested_articles"]:
                        with st.expander(f"{art['article_id']} · {art['title']}  —  {art['score']}%",
                                         expanded=art is result["suggested_articles"][0]):
                            st.caption(f"Category: {art['category']}")
                            for i, step in enumerate(art["steps"], 1):
                                st.markdown(f"{i}. {step}")
                else:
                    st.caption("No relevant article found.")
            st.markdown("---")

            # Keywords + missing info
            st.subheader("🔎 Issue Keywords & Missing Information")
            k1, k2 = st.columns(2)
            with k1:
                st.markdown("**✅ Issue keywords found**")
                if result["keywords"]:
                    shared = set(result["matching_keywords"])
                    st.markdown(
                        "".join(f'<span class="pill {"pill-ok" if k in shared else "pill-info"}">{k}</span>'
                                for k in result["keywords"]),
                        unsafe_allow_html=True,
                    )
                    if shared:
                        st.caption("Green = also covered by the best matching article.")
                else:
                    st.caption("No known issue keywords detected.")
            with k2:
                st.markdown("**❌ Information to ask the customer for**")
                if result["missing_info"]:
                    st.markdown(pills(result["missing_info"], "pill-miss"), unsafe_allow_html=True)
                else:
                    st.caption("The ticket already contains everything an agent needs.")
            kfig = keyword_chart(result["keyword_counts"])
            if kfig:
                show_chart(kfig)
            st.markdown("---")

            # Recommendations + draft reply
            st.subheader("💡 Recommendations")
            for rec in result["recommendations"]:
                st.markdown(f"- {rec}")

            st.subheader("✉️ Draft Reply (editable)")
            st.text_area("Reply", value=result["draft_reply"], height=300, label_visibility="collapsed")

            with st.expander("📄 Original ticket text"):
                st.text(result["ticket_text"])

            d1, d2 = st.columns(2)
            d1.download_button("⬇️ Download report (.txt)", report_text(result), "ticket_report.txt")
            d2.download_button("⬇️ Download JSON", json.dumps(result, indent=2), "ticket_report.json")
else:
    st.info("👆 Upload a ticket file or paste the text, then click **Analyze Ticket**.")

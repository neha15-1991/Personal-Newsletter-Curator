import requests
import streamlit as st
from html import escape
import os


# ---------------------------------------------------------
# BACKEND API URL
# ---------------------------------------------------------
# Locally it will use localhost.
# On Render, it will use API_URL from Environment Variables.
API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
# IMPORTANT:
# initial_sidebar_state="expanded" helps the sidebar stay visible after login.
st.set_page_config(
    page_title="Personal Newsletter Curator",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------------------------------------------------
# CUSTOM STYLING
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #e0f2fe 100%);
    }

    /* Reduce top empty space */
    .block-container {
        padding-top: 2.2rem !important;
        padding-bottom: 2rem;
        max-width: 1120px;
    }
    /* Color Streamlit top header area but keep Deploy button visible */
    header[data-testid="stHeader"] {
        background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #e0f2fe 100%) !important;
    }

    /* Keep toolbar / Deploy button visible */
    [data-testid="stToolbar"] {
        visibility: visible !important;
        display: flex !important;
    }

    /* Remove extra top margin */
    .main .block-container {
        padding-top: 0.6rem !important;
    }

    /* ---------------- SIDEBAR STYLING ---------------- */

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        border-right: 1px solid #334155;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div {
        color: #f8fafc !important;
    }

    .sidebar-card {
        background: rgba(255, 255, 255, 0.10);
        padding: 18px;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-top: 14px;
        margin-bottom: 18px;
    }

    .sidebar-small-text {
        font-size: 13px;
        color: #cbd5e1 !important;
        margin-bottom: 6px;
    }

    .sidebar-user-name {
        font-size: 21px;
        font-weight: 850;
        color: white !important;
        margin-bottom: 4px;
    }

    .sidebar-user-email {
        font-size: 13px;
        color: #cbd5e1 !important;
        margin-bottom: 0;
        word-break: break-word;
    }

    /* Sidebar logout button */
    section[data-testid="stSidebar"] div.stButton > button {
        background: #ef4444 !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        padding: 10px 18px !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] div.stButton > button * {
        color: white !important;
    }

    section[data-testid="stSidebar"] div.stButton > button:hover {
        background: #dc2626 !important;
        color: white !important;
        border: none !important;
    }

    /* ---------------- HEADINGS ---------------- */

    h1 {
        color: #0f172a;
        font-weight: 900;
        letter-spacing: -0.5px;
        line-height: 1.25 !important;
        margin-top:0 !important;
        padding-top:0.2rem !important;
    }

    h2, h3 {
        color: #1e293b;
        font-weight: 800;
    }

    /* ---------------- LOGIN WELCOME BOX ---------------- */

    .welcome-box {
        background: linear-gradient(135deg, #1E3A8A, #2563EB);
        padding: 42px 36px;
        border-radius: 24px;
        color: white;
        min-height: 420px;
        box-shadow: 0 18px 45px rgba(30, 58, 138, 0.25);
    }

    .welcome-box h1 {
        color: white !important;
        font-size: 38px;
        font-weight: 900;
        line-height: 1.3;
        margin-bottom: 20px;
    }

    .welcome-box p {
        color: #E0ECFF !important;
        font-size: 16px;
        line-height: 1.7;
    }

    .feature-tag {
        display: inline-block;
        background: rgba(255, 255, 255, 0.18);
        padding: 9px 14px;
        border-radius: 999px;
        margin: 5px;
        font-weight: 750;
        color: white;
    }

    /* ---------------- TABS ---------------- */

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.75);
        padding: 8px;
        border-radius: 18px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
    }

    .stTabs [data-baseweb="tab"] {
        background: #ffffff;
        border-radius: 999px;
        padding: 8px 16px;
        border: 1px solid #e5e7eb;
        height: 42px;
    }

    .stTabs [data-baseweb="tab"] p {
        color: #475569 !important;
        font-weight: 700;
        font-size: 14px;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
        border: none !important;
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.25);
    }

    .stTabs [aria-selected="true"] p {
        color: white !important;
        font-weight: 800;
    }

    /* ---------------- METRIC CARDS ---------------- */

    .metric-card {
        background: rgba(255, 255, 255, 0.92);
        padding: 24px;
        border-radius: 22px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
        text-align: center;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 16px 36px rgba(15, 23, 42, 0.12);
    }

    .metric-number {
        font-size: 36px;
        font-weight: 900;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .metric-label {
        font-size: 14px;
        color: #475569;
        font-weight: 700;
        margin-top: 6px;
    }

    /* ---------------- STORY CARDS ---------------- */

    .story-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 24px;
        border-radius: 22px;
        margin-bottom: 18px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
        border: 1px solid #e2e8f0;
    }

    .story-title {
        font-size: 24px;
        font-weight: 900;
        color: #0f172a;
        margin-bottom: 12px;
    }

    .badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 999px;
        background: #dbeafe;
        color: #1d4ed8;
        font-size: 13px;
        font-weight: 800;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    .score-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 999px;
        background: #dcfce7;
        color: #166534;
        font-size: 13px;
        font-weight: 800;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    .warning-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 999px;
        background: #fef3c7;
        color: #92400e;
        font-size: 13px;
        font-weight: 800;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
# Streamlit reruns the file after every button click.
# Session state keeps login information saved during reruns.
if "token" not in st.session_state:
    st.session_state.token = None

if "user" not in st.session_state:
    st.session_state.user = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def get_headers():
    """
    Creates the Authorization header for protected backend endpoints.
    """

    return {
        "Authorization": f"Bearer {st.session_state.token}"
    }


def show_api_error(response):
    """
    Shows backend errors clearly on the Streamlit screen.
    """

    if response is None:
        st.error("No response received from backend.")
        return

    try:
        st.write(response.json())
    except Exception:
        st.write(response.text)


def clear_login_session():
    """
    Clears saved login data from Streamlit session state.
    """

    st.session_state.token = None
    st.session_state.user = None
    st.session_state.logged_in = False


def get_sources_list_from_response(response):
    """
    Handles both possible backend response styles:
    1. {"sources": [...]}
    2. [...]
    """

    if response is None or response.status_code != 200:
        return []

    data = response.json()

    if isinstance(data, dict):
        return data.get("sources", [])

    if isinstance(data, list):
        return data

    return []


def get_digests_list_from_response(response):
    """
    Handles digest response safely.
    Expected backend response:
    {"digests": [...]}
    """

    if response is None or response.status_code != 200:
        return []

    data = response.json()

    if isinstance(data, dict):
        return data.get("digests", [])

    if isinstance(data, list):
        return data

    return []


# ---------------------------------------------------------
# BACKEND API FUNCTIONS
# ---------------------------------------------------------
def signup_user(name, email, password):
    try:
        return requests.post(
            f"{API_URL}/signup",
            json={
                "name": name,
                "email": email,
                "password": password
            },
            timeout=10
        )
    except requests.exceptions.RequestException as error:
        st.error("Could not connect to backend signup endpoint.")
        st.write(str(error))
        return None


def login_user(email, password):
    try:
        return requests.post(
            f"{API_URL}/login",
            json={
                "email": email,
                "password": password
            },
            timeout=10
        )
    except requests.exceptions.RequestException as error:
        st.error("Could not connect to backend login endpoint.")
        st.write(str(error))
        return None


def get_current_user():
    try:
        return requests.get(
            f"{API_URL}/me",
            headers=get_headers(),
            timeout=10
        )
    except requests.exceptions.RequestException as error:
        st.error("Could not get current user.")
        st.write(str(error))
        return None


def update_interests(interest_text, topics):
    try:
        return requests.put(
            f"{API_URL}/interests",
            json={
                "interest_text": interest_text,
                "topics": topics
            },
            headers=get_headers(),
            timeout=15
        )
    except requests.exceptions.RequestException as error:
        st.error("Could not save interests.")
        st.write(str(error))
        return None


def embed_interests():
    try:
        return requests.post(
            f"{API_URL}/embed-interests",
            headers=get_headers(),
            timeout=30
        )
    except requests.exceptions.RequestException as error:
        st.error("Could not update interest embedding.")
        st.write(str(error))
        return None


def add_source(source_type, source_value):
    try:
        return requests.post(
            f"{API_URL}/sources",
            json={
                "source_type": source_type,
                "source_value": source_value
            },
            headers=get_headers(),
            timeout=15
        )
    except requests.exceptions.RequestException as error:
        st.error("Could not add source.")
        st.write(str(error))
        return None


def get_sources():
    try:
        return requests.get(
            f"{API_URL}/sources",
            headers=get_headers(),
            timeout=15
        )
    except requests.exceptions.RequestException as error:
        st.error("Could not load sources.")
        st.write(str(error))
        return None


def run_curator():
    try:
        return requests.post(
            f"{API_URL}/run-curator",
            headers=get_headers(),
            timeout=120
        )
    except requests.exceptions.RequestException as error:
        st.error("Could not run curator pipeline.")
        st.write(str(error))
        return None


def get_all_digests():
    try:
        return requests.get(
            f"{API_URL}/digests",
            headers=get_headers(),
            timeout=20
        )
    except requests.exceptions.RequestException as error:
        st.error("Could not load digests.")
        st.write(str(error))
        return None


def record_click(story_id):
    try:
        return requests.post(
            f"{API_URL}/clicks/{story_id}",
            headers=get_headers(),
            timeout=15
        )
    except requests.exceptions.RequestException as error:
        st.error("Could not record click.")
        st.write(str(error))
        return None


def get_clicks():
    try:
        return requests.get(
            f"{API_URL}/clicks",
            headers=get_headers(),
            timeout=15
        )
    except requests.exceptions.RequestException as error:
        st.error("Could not load click history.")
        st.write(str(error))
        return None


# ---------------------------------------------------------
# LOGIN / SIGNUP SCREEN
# ---------------------------------------------------------
# Sidebar is intentionally not shown here.
# It will show only after login.
if not st.session_state.logged_in or not st.session_state.token:

    left_col, right_col = st.columns([1.2, 0.8])

    # ---------------- LEFT WELCOME SECTION ----------------
    with left_col:
        welcome_html = (
            "<div class='welcome-box'>"
            "<h1>📰 Personal Newsletter Curator</h1>"
            "<p>"
            "Your AI-powered reading assistant that fetches stories, "
            "ranks them based on your interests, creates summaries, "
            "and builds your personal digest."
            "</p>"
            "<br>"
            "<span class='feature-tag'>AI Summaries</span>"
            "<span class='feature-tag'>Interest Ranking</span>"
            "<span class='feature-tag'>Daily Digest</span>"
            "<span class='feature-tag'>Click Tracking</span>"
            "<span class='feature-tag'>Scheduled Jobs</span>"
            "<br><br>"
            "<p>"
            "Login or create an account to manage your interests, "
            "sources, digests, and reading history."
            "</p>"
            "</div>"
        )

        st.markdown(
            welcome_html,
            unsafe_allow_html=True
        )

    # ---------------- RIGHT LOGIN / SIGNUP SECTION ----------------
    with right_col:
        st.subheader("Welcome")

        auth_mode = st.radio(
            "Choose option",
            ["Login", "Signup"],
            horizontal=True,
            key="auth_mode"
        )

        # ---------------- LOGIN FORM ----------------
        if auth_mode == "Login":

            with st.form("login_form"):
                login_email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                    key="login_email"
                )

                login_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password"
                )

                login_submitted = st.form_submit_button(
                    "Login",
                    type="primary"
                )

            if login_submitted:
                if not login_email or not login_password:
                    st.error("Please enter email and password.")

                else:
                    with st.spinner("Logging in..."):
                        response = login_user(
                            login_email,
                            login_password
                        )

                    if response is None:
                        st.stop()

                    if response.status_code == 200:
                        token = response.json()["access_token"]

                        st.session_state.token = token
                        st.session_state.logged_in = True

                        user_response = get_current_user()

                        if user_response is not None and user_response.status_code == 200:
                            st.session_state.user = user_response.json()

                        st.rerun()

                    else:
                        st.error("Login failed. Backend response:")
                        show_api_error(response)

        # ---------------- SIGNUP FORM ----------------
        else:

            with st.form("signup_form"):
                signup_name = st.text_input(
                    "Full Name",
                    placeholder="Neha Singhal",
                    key="signup_name"
                )

                signup_email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                    key="signup_email"
                )

                signup_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Minimum 8 characters",
                    key="signup_password"
                )

                signup_submitted = st.form_submit_button(
                    "Create Account",
                    type="primary"
                )

            if signup_submitted:
                if not signup_name or not signup_email or not signup_password:
                    st.error("Please fill all fields.")

                elif len(signup_password) < 8:
                    st.error("Password must be at least 8 characters.")

                else:
                    with st.spinner("Creating account..."):
                        response = signup_user(
                            signup_name,
                            signup_email,
                            signup_password
                        )

                    if response is None:
                        st.stop()

                    if response.status_code in [200, 201]:
                        st.success("Account created successfully. Now login.")
                    else:
                        st.error("Signup failed. Backend response:")
                        show_api_error(response)

    # Stop here so the main app does not load before login.
    st.stop()

# ---------------------------------------------------------
# AUTO-LOAD USER AFTER LOGIN
# ---------------------------------------------------------
# If the page reruns and token exists but user details are missing,
# this fetches the user again.
if st.session_state.logged_in and st.session_state.token and st.session_state.user is None:
    user_response = get_current_user()

    if user_response is not None and user_response.status_code == 200:
        st.session_state.user = user_response.json()
    else:
        clear_login_session()
        st.error("Your session expired. Please login again.")
        st.stop()


# ---------------------------------------------------------
# LOGGED-IN SIDEBAR
# ---------------------------------------------------------
# This was the missing part in your file.
# It must come AFTER login check and BEFORE the main app tabs.
with st.sidebar:
    st.markdown("## 📰 Curator")

    st.caption("AI-powered personalised newsletter")

    if st.session_state.user:
        user_name = st.session_state.user.get("name", "User")
        user_email = st.session_state.user.get("email", "")

        sidebar_user_card = (
            "<div class='sidebar-card'>"
            "<p class='sidebar-small-text'>Logged in as</p>"
            f"<p class='sidebar-user-name'>{user_name}</p>"
            f"<p class='sidebar-user-email'>{user_email}</p>"
            "</div>"
        )

        st.markdown(
            sidebar_user_card,
            unsafe_allow_html=True
        )

    st.markdown("### Menu")
    st.write("Use the tabs on the main page to manage your newsletter.")

    st.divider()

    if st.button(
        "Logout",
        key="logout_button",
        type="primary",
        use_container_width=True
    ):
        clear_login_session()
        st.rerun()


# ---------------------------------------------------------
# MAIN APP TITLE
# ---------------------------------------------------------
st.title("📰 Personal Newsletter Curator")

st.write(
    "A personalised newsletter app that curates stories based on your interests."
)


# ---------------------------------------------------------
# MAIN APP TABS
# ---------------------------------------------------------
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📊 Dashboard",
        "🎯 Interests",
        "🔗 Sources",
        "⚡ Curate Now",
        "📰 Digest",
        "🔥 Trending"
    ]
)


# ---------------------------------------------------------
# TAB 0: DASHBOARD
# ---------------------------------------------------------
with tab0:
    st.header("Dashboard")

    digest_response = get_all_digests()
    sources_response = get_sources()
    clicks_response = get_clicks()

    digests = get_digests_list_from_response(digest_response)
    sources = get_sources_list_from_response(sources_response)

    digest_count = len(digests)
    source_count = len(sources)
    latest_story_count = 0
    click_count = 0

    if digest_count > 0:
        latest_story_count = len(
            digests[0].get("stories", [])
        )

    if clicks_response is not None and clicks_response.status_code == 200:
        click_count = clicks_response.json().get("count", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{digest_count}</div>
                <div class="metric-label">Saved Digests</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{latest_story_count}</div>
                <div class="metric-label">Stories in Latest Digest</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{source_count}</div>
                <div class="metric-label">Saved Sources</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{click_count}</div>
                <div class="metric-label">Tracked Clicks</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    with st.expander("How to use this app"):
        st.write(
            """
            1. Go to **Interest Editor** and save your interests.
            2. Go to **Source Manager** and add an HN, RSS, or Reddit source.
            3. Click **Fetch + Curate Now** to generate your digest.
            4. Open **Daily Digest** to read personalised story cards.
            5. Use **Record Click** to track stories you liked.
            """
        )


# ---------------------------------------------------------
# TAB 1: INTEREST EDITOR
# ---------------------------------------------------------
with tab1:
    st.header("Interest Editor")

    st.write("Add your free-text interests and topic tags.")

    interest_text = st.text_area(
        "What topics do you care about?",
        placeholder=(
            "Example: I am learning Python, AI tools, "
            "software development, and clean energy."
        )
    )

    topic_input = st.text_input(
        "Topic tags",
        placeholder="Example: Python, AI, Software Development, Clean Energy"
    )

    if st.button("Save Interests", key="save_interests_button"):
        topics = []

        if topic_input:
            topics = [
                topic.strip()
                for topic in topic_input.split(",")
                if topic.strip()
            ]

        if not interest_text or len(topics) == 0:
            st.error("Please add interest text and at least one topic tag.")

        else:
            response = update_interests(
                interest_text=interest_text,
                topics=topics
            )

            if response is not None and response.status_code == 200:
                st.success("Interests saved successfully.")

                with st.spinner("Updating interest embedding..."):
                    embed_response = embed_interests()

                if embed_response is not None and embed_response.status_code == 200:
                    st.success("Interest embedding updated.")
                else:
                    st.warning("Interests saved, but embedding update failed.")
                    show_api_error(embed_response)

            else:
                st.error("Failed to save interests.")
                show_api_error(response)


# ---------------------------------------------------------
# TAB 2: SOURCE MANAGER
# ---------------------------------------------------------
with tab2:
    st.header("Source Manager")

    st.write("Add RSS feeds, Reddit subreddits, or Hacker News tags.")

    source_type = st.selectbox(
        "Source type",
        ["rss", "reddit", "hn"]
    )

    source_value = st.text_input(
        "Source value",
        placeholder="RSS URL, subreddit name, or HN tag"
    )

    if st.button("Add Source", key="add_source_button"):
        if not source_value:
            st.error("Please enter a source value.")

        else:
            with st.spinner("Adding source..."):
                response = add_source(source_type, source_value)

            if response is not None and response.status_code in [200, 201]:
                st.success("Source added successfully.")
            else:
                st.error("Failed to add source.")
                show_api_error(response)

    st.subheader("Saved Sources")

    sources_response = get_sources()

    if sources_response is not None and sources_response.status_code == 200:
        sources = get_sources_list_from_response(sources_response)

        if len(sources) > 0:
            for source in sources:
                col1, col2, col3 = st.columns([2, 6, 2])

                with col1:
                    st.write(f"**{source.get('source_type')}**")

                with col2:
                    st.write(source.get("source_value"))

                with col3:
                    if st.button("Delete", key=f"delete_source_{source.get('id')}"):
                        with st.spinner("Deleting source..."):
                            delete_response = requests.delete(
                                f"{API_URL}/sources/{source.get('id')}", headers=get_headers())
                        if delete_response.status_code == 200:
                            st.success("Source deleted successfully.")
                            st.rerun()
                        else:
                            st.error("Failed to delete source.")
                            show_api_error(delete_response)
        else:
            st.info("No sources added yet.")
    else:
        st.warning("Could not load sources.")
        show_api_error(sources_response)


# ---------------------------------------------------------
# TAB 3: FETCH + CURATE NOW
# ---------------------------------------------------------
with tab3: 
    st.header("Fetch + Curate Now") 
    st.write( "This button runs the complete newsletter pipeline: " "fetch stories, create embeddings, update your interest embedding, " "and build your personalised digest." )

    if st.button("Fetch + Curate Now", key="run_curator_button"):
        with st.spinner("Running curator pipeline, fetching stories and preparing digests... This may take a few seconds"):
            response = run_curator()

        if response is not None and response.status_code == 200:
            result = response.json()

            st.success("Curator pipeline completed successfully.")

            fetch_result = result.get("fetch_result", {})
            digest_result = result.get("digest_result", {})

            total_fetched = fetch_result.get("total_fetched", 0)
            total_saved = fetch_result.get("total_saved", 0)
            duplicates_skipped = fetch_result.get("duplicates_skipped", 0)
            failed_sources = fetch_result.get("failed_sources", [])

            st.subheader("Curation Summary")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Stories fetched", total_fetched)

            with col2:
                st.metric("New stories saved", total_saved)

            with col3:
                st.metric("Duplicates skipped", duplicates_skipped)

            if total_saved == 0 and duplicates_skipped > 0:
                st.info(
                    "No new stories were saved because the fetched stories already exist in the database."
                )

            if failed_sources:
                st.warning("Some sources could not be fetched.")

                for failed_source in failed_sources:
                    source_type = failed_source.get("source_type", "unknown")
                    source_value = failed_source.get("source_value", "unknown")
                    error_message = failed_source.get("error", "")

                    st.write(
                        f"- **{source_type}** source `{source_value}` failed: {error_message}"
                    )

            story_count = digest_result.get("story_count", 0)

            if story_count:
                st.success(
                    f"Digest created successfully with {story_count} stories. "
                    "Go to the Daily Digest tab to view it."
                )
            else:
                st.info("The curator completed, but no new digest stories were created this time.")

            with st.expander("View technical backend response"):
                st.json(result)

        else:
            st.error("Curator pipeline failed.")

            if response is None:
                st.write("No response received from backend.")
            else:
                st.write("Status code:", response.status_code)
                st.write("Response text:", response.text)

                try:
                    st.json(response.json())
                except Exception:
                    pass
# ---------------------------------------------------------
# TAB 4: DAILY DIGEST
# ---------------------------------------------------------
with tab4:
    st.header("Daily Digest")

    st.write("Your personalised newsletter cards appear here.")

    if st.button("Refresh Digest", key="refresh_digest_button"):
        st.rerun()

    digest_response = get_all_digests()

    if digest_response is not None and digest_response.status_code == 200:
        digests = get_digests_list_from_response(digest_response)

        if len(digests) == 0:
            st.info("No digest items yet. Use Fetch + Curate Now first.")

        else:
            latest_digest = digests[0]

            digest_info_html = (
                f"<span class='badge'>Digest ID: {escape(str(latest_digest.get('id')))}</span>"
                f"<span class='warning-badge'>Created: {escape(str(latest_digest.get('created_at')))}</span>"
            )

            st.markdown(
                digest_info_html,
                unsafe_allow_html=True
            )

            st.write("")

            stories = latest_digest.get("stories", [])

            for item in stories:
                title = item.get("title", "Untitled Story")
                summary = item.get("summary", "")
                why_it_matters = item.get("why_it_matters", "")
                source_type = item.get("source_type", "")
                source_name = item.get("source_name", "")
                similarity_score = item.get("similarity_score", "")
                engagement_score = item.get("engagement_score", 0)
                comment_count = item.get("comment_count", 0)
                url = item.get("url")
                story_id = item.get("story_id")

                # Escape story text before placing it inside HTML.
                # This avoids broken layouts if a title or summary contains <, >, or quotes.
                safe_title = escape(str(title))
                safe_summary = escape(str(summary))
                safe_why_it_matters = escape(str(why_it_matters))
                safe_source_type = escape(str(source_type))
                safe_source_name = escape(str(source_name))
                safe_similarity_score = escape(str(similarity_score))
                safe_engagement_score = escape(str(engagement_score))
                safe_comment_count = escape(str(comment_count))

                # IMPORTANT:
                # Do not use an indented triple-quoted HTML string here.
                # Streamlit Markdown may treat indented HTML lines as a code block.
                story_html = (
                    "<div class='story-card'>"
                    f"<div class='story-title'>{safe_title}</div>"
                    f"<span class='badge'>{safe_source_type} — {safe_source_name}</span>"
                    f"<span class='score-badge'>Relevance: {safe_similarity_score}</span>"
                    f"<span class='warning-badge'>Engagement: {safe_engagement_score}</span>"
                    f"<span class='warning-badge'>Comments: {safe_comment_count}</span>"
                    "<p><b>Summary</b></p>"
                    f"<p>{safe_summary}</p>"
                    "<p><b>Why this matters</b></p>"
                    f"<p>{safe_why_it_matters}</p>"
                    "</div>"
                )

                st.markdown(
                    story_html,
                    unsafe_allow_html=True
                )

                if url:
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        if st.button(
                            "Record Click",
                            key=f"record_click_{story_id}"
                        ):
                            click_response = record_click(story_id)

                            if click_response is not None and click_response.status_code == 200:
                                st.success("Click recorded.")
                            else:
                                st.warning("Could not record click.")
                                show_api_error(click_response)

                    with col2:
                        st.link_button(
                            "Read full story",
                            url
                        )

                st.write("")

    else:
        st.warning("Could not load latest digest.")
        show_api_error(digest_response)


# ---------------------------------------------------------
# TAB 5: TRENDING + CLICK HISTORY
# ---------------------------------------------------------
with tab5:
    st.header("🔥 Trending in Your Topics")

    st.write(
        "Top stories from your latest digest, sorted by engagement score."
    )

    digest_response = get_all_digests()

    if digest_response is not None and digest_response.status_code == 200:
        digests = get_digests_list_from_response(digest_response)

        if len(digests) == 0:
            st.info("No trending stories yet.")

        else:
            latest_digest = digests[0]
            stories = latest_digest.get("stories", [])

            sorted_stories = sorted(
                stories,
                key=lambda story: story.get("engagement_score", 0),
                reverse=True
            )

            for index, item in enumerate(sorted_stories[:5], start=1):
                title = item.get("title", "Untitled Story")
                why_it_matters = item.get("why_it_matters", "")
                engagement_score = item.get("engagement_score", 0)
                comment_count = item.get("comment_count", 0)
                url = item.get("url")

                with st.container(border=True):
                    st.subheader(f"{index}. {title}")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            label="Engagement",
                            value=engagement_score
                        )

                    with col2:
                        st.metric(
                            label="Comments",
                            value=comment_count
                        )

                    st.write("**Why this matters**")
                    st.write(why_it_matters)

                    if url:
                        st.link_button(
                            "Read story",
                            url
                        )

    else:
        st.warning("Could not load trending stories.")
        show_api_error(digest_response)

    st.divider()

    st.header("🖱️ My Click History")

    clicks_response = get_clicks()

    if clicks_response is not None and clicks_response.status_code == 200:
        clicks_data = clicks_response.json()
        clicks = clicks_data.get("clicks", [])

        if len(clicks) == 0:
            st.info("No clicked stories yet.")

        else:
            for click in clicks[:5]:
                with st.container(border=True):
                    st.write(f"**{click.get('story_title')}**")
                    st.write(f"Clicked at: {click.get('clicked_at')}")

                    if click.get("story_url"):
                        st.link_button(
                            "Open clicked story",
                            click.get("story_url")
                        )

    else:
        st.warning("Could not load click history.")
        show_api_error(clicks_response)

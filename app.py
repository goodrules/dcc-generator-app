import streamlit as st

if "role" not in st.session_state:
    st.session_state.role = None

ROLES = [None, "Chat-with-Gemini", "Generate-with-Imagen"]

def login():
    st.header("Log in")
    role = st.selectbox("Choose the activity", ROLES)
    if st.button("Log in"):
        st.session_state.role = role
        st.rerun()

def logout():
    st.session_state.role = None
    st.rerun()

role = st.session_state.role

logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
settings = st.Page("settings.py", title="Settings", icon=":material/settings:")

gemini_chat_page = st.Page(
    "chat/geminibot.py",
    title="Chat with Gemini",
    default=(role == "Chat-with-Gemini"),
)

imagen_image_page = st.Page(
    "image-generation/imagenbot.py", 
    title="Image Generator with Imagen", 
    default=(role == "Generate-with-Imagen"),
)

account_pages = [logout_page, settings]
genai_pages = [gemini_chat_page, imagen_image_page]

page_dict = {}

if st.session_state.role in ["Chat-with-Gemini"]:
    page_dict["Chat-with-Gemini"] = genai_pages
if st.session_state.role in ["Generate-with-Imagen"]:
    page_dict["Generate-with-Imagen"] = genai_pages

if len(page_dict) > 0:
    pg = st.navigation({"Account": account_pages} | page_dict)
else:
    pg = st.navigation([st.Page(login)])

pg.run()

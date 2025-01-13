import streamlit as st

if "role" not in st.session_state:
    st.session_state.role = None

ROLES = [None, "DCC-Generator"]  

actual_username = "thunderdome"
actual_password = "bookclub"

def login():
    st.header("Log in")
    # Insert a form in the container
    with st.form("login"):
        st.markdown("#### Enter your credentials")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
    
    if submit and username == actual_username and password == actual_password:
        # If the form is submitted and the email and password are correct,
        # clear the form/container and display a success message
        st.success("Login successful")
        st.session_state.role = "DCC-Generator"
        st.rerun()
        
    elif submit and username != actual_username and password != actual_password:
        st.error("Login failed")
    else:
        pass

def logout():
    st.session_state.role = None
    st.rerun()

role = st.session_state.role

logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
settings = st.Page("settings.py", title="Settings", icon=":material/settings:")

dcc_page = st.Page(
    "dccgen/dccgen.py",
    title="DCC Achievement Generator",
    default=(role == "DCC-Generator"),
)

account_pages = [logout_page, settings]
role_pages = [dcc_page]

page_dict = {}

if st.session_state.role in ["DCC-Generator"]:
    page_dict["DCC-Generator"] = role_pages

if len(page_dict) > 0:
    pg = st.navigation({"Account": account_pages} | page_dict)
else:
    pg = st.navigation([st.Page(login)])

pg.run()

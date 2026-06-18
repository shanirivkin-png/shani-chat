import streamlit as st
import json, time, hashlib, base64
from pathlib import Path

DATA = Path("shani_chat_data.json")

def load():
    if DATA.exists():
        return json.loads(DATA.read_text())
    return {"users": {}, "messages": []}

def save(data):
    DATA.write_text(json.dumps(data, indent=2))

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

data = load()

st.set_page_config(page_title="SHANI CHAT", page_icon="💬", layout="wide")

st.markdown("""
<style>
.profile-button {
    position: fixed;
    bottom: 20px;
    right: 25px;
    width: 55px;
    height: 55px;
    border-radius: 50%;
    background: #ffcc00;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    border: 3px solid black;
}
.chat-box {
    padding: 10px;
    border-radius: 15px;
    margin: 8px;
    background-color: #f1f1f1;
}
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None
if "chat_with" not in st.session_state:
    st.session_state.chat_with = None

st.title("💬 SHANI CHAT")

# ---------- LOGGED OUT ----------
if not st.session_state.user:
    tab1, tab2 = st.tabs(["Sign Up", "Log In"])

    with tab1:
        username = st.text_input("Choose username")
        password = st.text_input("Choose password", type="password")

        if st.button("Create account"):
            if not username or not password:
                st.error("Please write a username and password.")
            elif username in data["users"]:
                st.error("That username already exists.")
            else:
                data["users"][username] = {
                    "password": hash_pw(password),
                    "contacts": [],
                    "avatar": None
                }
                save(data)
                st.session_state.user = username
                st.rerun()

    with tab2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Log in"):
            if username in data["users"] and data["users"][username]["password"] == hash_pw(password):
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Wrong password. Please check if you spelled it correctly.")

    with st.expander("❕ Admin"):
        admin = st.text_input("Admin password", type="password")
        if admin == "cow":
            st.subheader("Admin Page")
            st.write("Users:")
            st.write(sorted(data["users"].keys()))
            st.write("Total messages:", len(data["messages"]))
            st.warning("Passwords are hidden for safety.")

    st.stop()

me = st.session_state.user
user_data = data["users"][me]

# ---------- SIDEBAR ----------
st.sidebar.title("Contacts")

if not user_data["contacts"]:
    st.sidebar.write("No contacts yet.")

for contact in sorted(user_data["contacts"]):
    if st.sidebar.button(contact, key="contact_" + contact):
        st.session_state.chat_with = contact
        st.rerun()

st.sidebar.divider()

with st.sidebar.expander("➕ Add contact"):
    new_contact = st.text_input("Username")
    if st.button("Save contact"):
        if new_contact not in data["users"]:
            st.error("That user does not exist.")
        elif new_contact == me:
            st.error("You cannot add yourself.")
        elif new_contact in user_data["contacts"]:
            st.info("Already in contacts.")
        else:
            user_data["contacts"].append(new_contact)
            save(data)
            st.rerun()

with st.sidebar.expander("Search contacts"):
    for name in sorted(data["users"].keys()):
        if name != me:
            if st.button(name, key="search_" + name):
                st.session_state.chat_with = name

                if name not in user_data["contacts"]:
                    user_data["contacts"].append(name)
                    save(data)

                st.rerun()

st.sidebar.divider()
st.sidebar.subheader("New messages")

senders = []
for msg in data["messages"]:
    if msg["to"] == me and msg["from"] not in senders:
        senders.append(msg["from"])

if not senders:
    st.sidebar.write("No new messages.")

for sender in sorted(senders):
    if st.sidebar.button(sender, key="new_" + sender):
        st.session_state.chat_with = sender

        if sender not in user_data["contacts"]:
            user_data["contacts"].append(sender)
            save(data)

        st.rerun()

# ---------- MAIN CHAT PAGE ----------
chat_with = st.session_state.chat_with

if not chat_with:
    st.info("Pick a contact from the sidebar to start chatting.")
else:
    st.header(chat_with)

    other_avatar = data["users"][chat_with].get("avatar")
    if other_avatar:
        st.image(base64.b64decode(other_avatar), width=70)

    chat = [
        m for m in data["messages"]
        if (m["from"] == me and m["to"] == chat_with)
        or (m["from"] == chat_with and m["to"] == me)
    ]

    for msg in chat:
        if msg["from"] == me:
            st.chat_message("user").write(msg["text"])
        else:
            st.chat_message("assistant").write(msg["text"])

    text = st.chat_input("Text here...")

    if text:
        data["messages"].append({
            "from": me,
            "to": chat_with,
            "text": text,
            "time": time.time()
        })
        save(data)
        st.rerun()

# ---------- SMALL ACCOUNT BUTTON ----------
st.markdown('<div class="profile-button">👤</div>', unsafe_allow_html=True)

with st.expander("👤 Account"):
    st.write("Logged in as:", me)

    new_password = st.text_input("Change password", type="password")
    if st.button("Save new password"):
        if new_password:
            user_data["password"] = hash_pw(new_password)
            save(data)
            st.success("Password changed.")

    st.subheader("Profile picture")
    uploaded = st.file_uploader("Upload picture", type=["png", "jpg", "jpeg"])
    camera = st.camera_input("Or take picture")

    chosen = uploaded or camera

    if chosen and st.button("Save profile picture"):
        user_data["avatar"] = base64.b64encode(chosen.read()).decode()
        save(data)
        st.success("Saved!")

    if st.button("Log out"):
        st.session_state.user = None
        st.session_state.chat_with = None
        st.rerun()
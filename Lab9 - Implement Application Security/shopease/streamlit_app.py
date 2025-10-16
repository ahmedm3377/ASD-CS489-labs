import streamlit as st
import requests

# Avoid accessing st.secrets directly when no secrets file exists (Streamlit raises).
try:
    API_BASE = st.secrets.get("API_BASE", "http://127.0.0.1:8080/adsweb/api/v1")
except Exception:
    # No secrets configured; fall back to local API base
    API_BASE = "http://127.0.0.1:8080/adsweb/api/v1"


def token_request(username: str, password: str):
    url = f"{API_BASE}/token"
    data = {"username": username, "password": password}
    # OAuth2 token endpoint expects form data
    resp = requests.post(url, data=data)
    return resp


def get_tickets(token: str):
    url = f"{API_BASE}/tickets"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)


def create_ticket(token: str, customerID: int, issue: str, supportAgentID: int | None = None):
    url = f"{API_BASE}/ticket"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"customerID": customerID, "issueDescription": issue, "supportAgentID": supportAgentID}
    return requests.post(url, json=payload, headers=headers)


def main():
    st.title("ShopEase Admin UI")

    if "token" not in st.session_state:
        st.session_state.token = None

    with st.sidebar:
        st.header("Login")
        username = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            resp = token_request(username, password)
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.token = data.get("access_token")
                st.success("Logged in")
            else:
                st.error(f"Login failed: {resp.status_code} {resp.text}")

        if st.session_state.token:
            if st.button("Logout"):
                st.session_state.token = None

    if st.session_state.token:
        st.subheader("Tickets")
        resp = get_tickets(st.session_state.token)
        if resp.status_code == 200:
            tickets = resp.json()
            for t in tickets:
                st.markdown(f"**Ticket {t['ticketID']}** - {t['status']}")
                st.write(t['issueDescription'])
                st.write(t['customer'])
                st.write('---')
        else:
            st.error(f"Failed to load tickets: {resp.status_code}")

        st.subheader("Create Ticket")
        with st.form("create_ticket"):
            cid = st.number_input("Customer ID", min_value=1, value=1)
            issue = st.text_area("Issue description")
            agent = st.text_input("Support Agent ID (optional)")
            submitted = st.form_submit_button("Create")
            if submitted:
                agent_id = int(agent) if agent.strip().isdigit() else None
                r = create_ticket(st.session_state.token, cid, issue, agent_id)
                if r.status_code in (200, 201):
                    st.success("Ticket created")
                else:
                    st.error(f"Failed to create ticket: {r.status_code} {r.text}")
    else:
        st.info("Please log in using the sidebar to view and create tickets.")


if __name__ == "__main__":
    main()

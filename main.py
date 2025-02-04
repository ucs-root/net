import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Urafiki Captive Portal",
    page_icon="🎫",
    layout="centered"
)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    if not os.path.exists('data'):
        os.makedirs('data')

    # Initialize vouchers.csv if it doesn't exist
    if not os.path.exists('data/vouchers.csv'):
        pd.DataFrame(columns=['voucher_code', 'assigned']).to_csv('data/vouchers.csv', index=False)

    # Initialize mappings.csv if it doesn't exist
    if not os.path.exists('data/mappings.csv'):
        pd.DataFrame(columns=['timestamp', 'full_name', 'voucher_code']).to_csv('data/mappings.csv', index=False)

    # Initialize authorized_users.csv if it doesn't exist
    if not os.path.exists('data/authorized_users.csv'):
        pd.DataFrame(columns=['full_name']).to_csv('data/authorized_users.csv', index=False)

def load_vouchers():
    """Load vouchers from CSV file"""
    try:
        return pd.read_csv('data/vouchers.csv')
    except:
        return pd.DataFrame(columns=['voucher_code', 'assigned'])

def load_mappings():
    """Load user-voucher mappings from CSV file"""
    try:
        return pd.read_csv('data/mappings.csv')
    except:
        return pd.DataFrame(columns=['timestamp', 'full_name', 'voucher_code'])

def load_authorized_users():
    """Load authorized users from CSV file"""
    try:
        return pd.read_csv('data/authorized_users.csv')
    except:
        return pd.DataFrame(columns=['full_name'])

def is_user_authorized(full_name):
    """Check if a user is authorized to receive a voucher"""
    authorized_users = load_authorized_users()
    # Convert full name to lowercase for case-insensitive comparison
    full_name_lower = full_name.lower()

    # Check if any part of the user's name matches an authorized user's name
    for auth_name in authorized_users['full_name']:
        auth_name_lower = str(auth_name).lower()
        # Split names into parts and check if any part matches
        user_name_parts = full_name_lower.split()
        auth_name_parts = auth_name_lower.split()

        # Check for any matching parts between the names
        if any(part in auth_name_parts for part in user_name_parts):
            return True

    return False

def assign_voucher(full_name):
    """Assign a voucher to a user"""
    # First check if user is authorized
    if not is_user_authorized(full_name):
        return False, "You are not authorized to receive a voucher. Please contact the administrator."

    vouchers_df = load_vouchers()
    mappings_df = load_mappings()

    # Check if user already has a voucher
    existing_mapping = mappings_df[mappings_df['full_name'] == full_name]
    if len(existing_mapping) > 0:
        return True, existing_mapping.iloc[0]['voucher_code']

    # Check if there are available vouchers
    available_vouchers = vouchers_df[vouchers_df['assigned'] == False]

    if len(available_vouchers) == 0:
        return False, "No vouchers available"

    # Get the first available voucher
    voucher_code = available_vouchers.iloc[0]['voucher_code']

    # Mark voucher as assigned
    vouchers_df.loc[vouchers_df['voucher_code'] == voucher_code, 'assigned'] = True
    vouchers_df.to_csv('data/vouchers.csv', index=False)

    # Record the mapping
    new_mapping = pd.DataFrame({
        'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        'full_name': [full_name],
        'voucher_code': [voucher_code]
    })
    mappings_df = pd.concat([mappings_df, new_mapping], ignore_index=True)
    mappings_df.to_csv('data/mappings.csv', index=False)

    return True, voucher_code

# Initialize admin password in session state
if 'admin_password' not in st.session_state:
    st.session_state.admin_password = 'ucs.ke'  # Modified admin password

# Header
st.title("🎫 Urafiki Captive Portal")
st.markdown("---")

# Admin login in sidebar
with st.sidebar:
    st.title("Admin Login")
    password_input = st.text_input("Admin Password", type="password")
    is_admin = password_input == st.session_state.admin_password

# Only show admin section if correct password is entered
if is_admin:
    st.subheader("Admin Section")

    # Tab for different admin functions
    admin_tab1, admin_tab2 = st.tabs(["Upload Vouchers", "Upload Users"])

    with admin_tab1:
        uploaded_vouchers = st.file_uploader("Upload CSV file with voucher codes", type=['csv'], key="voucher_uploader")
        if uploaded_vouchers is not None:
            try:
                new_vouchers = pd.read_csv(uploaded_vouchers)
                if 'voucher_code' not in new_vouchers.columns:
                    st.error("CSV must contain a 'voucher_code' column")
                else:
                    new_vouchers['assigned'] = False
                    new_vouchers.to_csv('data/vouchers.csv', index=False)
                    st.success(f"Successfully uploaded {len(new_vouchers)} vouchers")
            except Exception as e:
                st.error(f"Error uploading file: {str(e)}")

    with admin_tab2:
        uploaded_users = st.file_uploader("Upload CSV file with authorized users", type=['csv'], key="user_uploader")
        if uploaded_users is not None:
            try:
                new_users = pd.read_csv(uploaded_users)
                if 'full_name' not in new_users.columns:
                    st.error("CSV must contain a 'full_name' column")
                else:
                    new_users.to_csv('data/authorized_users.csv', index=False)
                    st.success(f"Successfully uploaded {len(new_users)} authorized users")
            except Exception as e:
                st.error(f"Error uploading file: {str(e)}")

    # Display statistics
    st.markdown("---")
    st.subheader("System Statistics")
    col1, col2 = st.columns(2)

    vouchers_df = load_vouchers()
    mappings_df = load_mappings()
    authorized_users_df = load_authorized_users()

    with col1:
        st.metric("Total Vouchers", len(vouchers_df))
        st.metric("Available Vouchers", len(vouchers_df[vouchers_df['assigned'] == False]))
        st.metric("Authorized Users", len(authorized_users_df))

    with col2:
        st.metric("Assigned Vouchers", len(vouchers_df[vouchers_df['assigned'] == True]))
        st.metric("Total Users", len(mappings_df))

    # Recent assignments
    if len(mappings_df) > 0:
        st.subheader("Recent Assignments")
        st.dataframe(
            mappings_df.tail(5)[['timestamp', 'full_name', 'voucher_code']],
            hide_index=True
        )

# User section (always visible)
if not is_admin:
    st.subheader("Get Your Voucher")
    st.markdown("Enter your full name to receive a unique voucher code.")

    with st.form("voucher_form"):
        full_name = st.text_input("Full Name")
        submit_button = st.form_submit_button("Get Voucher")

        if submit_button:
            if not full_name.strip():
                st.error("Please enter your full name")
            else:
                success, result = assign_voucher(full_name.strip())
                if success:
                    st.success("Congratulations! Your voucher has been assigned.")
                    st.markdown("### Your Voucher Code:")
                    st.code(result, language="text")
                    st.info("Click the copy button in the top-right corner of the code box to copy your voucher.")
                else:
                    st.error(result)
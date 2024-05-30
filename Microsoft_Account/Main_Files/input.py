import streamlit as st
import requests
from bs4 import BeautifulSoup
import re


st.title("Email Automation")

# Define the URL for updating email content and handling webhook
BACKEND_URL = "http://localhost:5000/api/update_email"

# Input fields for subject line and body
form_id = st.text_input("Enter Form ID:")
subject_line = st.text_input("Enter Subject Line:")
body_text = st.text_area("Enter Body Text:")

def convert_to_html(text):
    # Convert URLs to clickable links with custom link name
    text_with_links = re.sub(r'(https?://\S+)', r'<a href="\1">Click here</a>', text)
    # Convert newlines to <br> tags
    text_with_br = text_with_links.replace('\n', '<br>')
    # Add space between elements to preserve text spacing
    soup = BeautifulSoup(text_with_br, 'html.parser')
    html_body = ' '.join(str(tag) for tag in soup.contents)
    # Add line break after completing the body
    html_body += '<br>'
    return html_body

if st.button("Update Email Content"):
    if subject_line and body_text:
        # Convert plain text body to HTML format
        html_body = convert_to_html(body_text)

        # Prepare data to send to Flask API
        data = {
            "form_id": form_id,  # Ensure form_id is without quotes
            "subject": subject_line,
            "body": html_body
        }

        try:
            # Make a POST request to update email content
            response = requests.post(BACKEND_URL, json=data)
            
            if response.status_code == 200:
                st.success("Email content updated successfully. Text converted to HTML format.")
            else:
                st.error("Failed to update email content. Backend server may not be running.")
        except requests.exceptions.RequestException as e:
            st.error("Failed to connect to the backend server. Please make sure it's running.")
    else:
        st.warning("Please fill in both subject line and body text.")

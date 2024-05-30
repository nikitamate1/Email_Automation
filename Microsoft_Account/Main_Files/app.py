import os
import smtplib
import hmac
import hashlib
import base64
import re
import logging
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Enable debugging
app.config['DEBUG'] = True
# Secret key for session
app.secret_key = os.urandom(24)

# Load environment variables from the .env file
load_dotenv()

# Define email credentials
SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
NOREPLY_EMAIL = os.environ.get("NOREPLY_EMAIL")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
TYPEFORM_SECRET = os.environ.get("TYPEFORM_SECRET")

# Default values for email content
DEFAULT_SUBJECT = os.environ.get("DEFAULT_SUBJECT", "Thank you for your interest")
DEFAULT_BODY = os.environ.get("DEFAULT_BODY", "This email confirms your recent submission. We will get back to you within the next 24 hours. (72 hours if it’s a weekend) \nThank you,\n Nikita Mate")

# Log settings
LOG_FILENAME = 'app.log'
LOG_LEVEL = logging.INFO
logging.basicConfig(filename=LOG_FILENAME, level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

def send_automated_emails(email_addresses, subject, body, first_name, bcc_emails=None, is_html=False):
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp_server:
            smtp_server.starttls()
            smtp_server.login(NOREPLY_EMAIL, EMAIL_PASSWORD)

            for email in email_addresses:
                try:
                    msg = MIMEMultipart()
                    msg["From"] = NOREPLY_EMAIL
                    msg["To"] = email
                    msg["Subject"] = subject

                    if is_html:
                        # Create HTML content with logo and signature
                        html_content = f"""
                        <html>
                        <head>
                            <style>
                                .logo-container {{
                                    position: absolute;
                                    top: 10px;
                                    right: 10px;
                                }}
                                .logo {{
                                    max-width: 100px; /* Adjust the size as needed */
                                    height: auto;
                                }}
                                .signature {{
                                    color: #807F85; /* Default color for signature */
                                }}
                                .name {{
                                    color: #FF8100; /* Ambar Gosavi color */
                                    font-weight: bold; /* Bold text */
                                    font-size: 16px; /* Larger font size */
                                }}
                                .position {{
                                    color: #020067; /* Sales & Marketing position color */
                                    font-size: 14px; /* Smaller font size */
                                }}
                                .email {{
                                    color: #1b1b1b; /* Email color */
                                }}
                                .linkedin {{
                                    color: #0077B5; /* LinkedIn blue color */
                                    text-decoration: none; /* Remove underline */
                                    font-size: 12px; /* Smaller font size */
                                    margin-top: 0; /* Remove top margin */
                                }}
                            </style>
                        </head>
                        <body>
                            <p>{body}</p>
                            <p class="signature">
                                <span class="name"><b>Nikita Mate</b></span><br>
                                <span class="position"><span style="font-size: 12px;"><b>Artificial Intelligence</b></span><br>
                                <span class="email">nikitamate012@gmail.com |</span>
                                <span class="linkedin"> <a href="https://www.linkedin.com/in/nikita-mate1/" class="linkedin"><b> LinkedIn</b></a>
                            </p>
                        </body>
                        </html>
                        """
                        msg.attach(MIMEText(html_content, 'html'))
                    else:
                        msg.attach(MIMEText(body, 'plain'))

                    # Add BCC emails if provided
                    if bcc_emails:
                        msg["Bcc"] = ", ".join(bcc_emails)

                    # Send the email with BCC recipients
                    smtp_server.sendmail(NOREPLY_EMAIL, [email] + (bcc_emails or []), msg.as_string())
                    logging.info(f"Email sent successfully to {email}")
                except smtplib.SMTPException as smtp_error:
                    logging.error(f"Error sending email to {email}: {smtp_error}")

    except Exception as e:
        logging.error("SMTP server connection error: %s", str(e))
def verify_signature(received_signature, payload):
    secret = TYPEFORM_SECRET.encode('utf-8')
    payload_str = payload.decode('utf-8')
    expected_signature = calculate_signature(payload_str.encode('utf-8'))
    return hmac.compare_digest(expected_signature, received_signature)

def load_updated_content(form_id):
    with open('data.txt', 'r') as file:
        content = file.read()
        # Split the content by single newline characters to separate each line
        lines = content.split('\n')
        
        # Initialize variables to store form ID, subject, and body
        stored_form_id = None
        updated_subject = None
        updated_body = None
        
        # Iterate through the lines to extract the form ID, subject, and body
        for line in lines:
            if line.startswith("form_id:"):
                if stored_form_id:  # Check if we already have data for a previous entry
                    # If so, check if the form ID matches the received one
                    if stored_form_id == form_id:
                        return updated_subject, updated_body
                    else:
                        # Reset variables for the next entry
                        stored_form_id = None
                        updated_subject = None
                        updated_body = None
                
                # Extract the form ID for the current entry
                stored_form_id = line.split(":")[1].strip()[1:-1]
            elif line.startswith("Subject:"):
                # Extract the subject for the current entry
                updated_subject = line.split(":")[1].strip()
            elif line.startswith("Body:"):
                # Extract the body for the current entry
                updated_body = line.split(":")[1].strip()
        
        # Check if the last entry matches the received form ID
        if stored_form_id == form_id:
            return updated_subject, updated_body
        
        # If no matching form ID is found
        return None, None



@app.route('/api/webhook', methods=['POST'])
def handle_email():
    logging.info("Received a request to handle webhook.")

    # Extract the signature from the request header
    received_signature = request.headers.get("Typeform-Signature")
    logging.debug(f"Received signature: {received_signature}")

    # Extract the raw payload from the request body
    raw_payload = request.data
    logging.debug(f"Received raw payload: {raw_payload}")

    # Calculate the expected signature
    expected_signature = calculate_signature(raw_payload)
    logging.debug(f"Calculated expected signature: {expected_signature}")

    # Verify the signature
    if not verify_signature(received_signature, raw_payload):
        logging.error("Invalid signature.")
        return jsonify({"message": "Invalid signature. Permission denied."}), 403

    # If the signature is valid, process the payload
    data = request.json
    logging.debug(f"Received JSON data: {data}")

    # Extract email content from the request data
    form_id = data["form_response"]["form_id"]

    # Check if form_id is present in the payload
    if form_id:
        updated_subject, updated_body = load_updated_content(form_id)
        if updated_subject and updated_body:
            # List of BCC email addresses
            bcc_emails = ["nikitamate343@gmail.com"]

            # Extract email addresses from the data
            email_addresses = [
                item["email"]
                for item in data["form_response"]["answers"]
                if item["field"]["type"] == "email"
            ]

            # Extract first name from the form response
            first_name = None
            for item in data["form_response"]["answers"]:
                if item["field"]["type"] == "short_text":
                    first_name = item["text"]
                    break

            # Modify email body to include first name if available
            updated_body_with_name = updated_body.replace("{first_name}", first_name or "")

            # Call the function with is_html=True to send HTML content
            send_automated_emails(email_addresses, updated_subject, updated_body_with_name, first_name, bcc_emails, is_html=True)
            logging.info("Emails sent successfully")
            return jsonify({"message": "Emails sent successfully"}), 200
        else:
            logging.error(f"No content found for form_id: {form_id}")
            return jsonify({"message": f"No content found for form_id: {form_id}"}), 404
    else:
        logging.error("No form_id found in the payload.")
        return jsonify({"message": "No form_id found in the payload."}), 400


@app.route('/api/update_email', methods=['POST'])
def update_email_content():
    data = request.json
    
    # Extract email content from the request data
    form_id = data.get('form_id').strip()  # Remove leading and trailing spaces
    updated_subject = data.get('subject')
    updated_body = data.get('body')

    logging.debug(f"Received update request for form_id: {form_id}")

    if not form_id or not updated_subject or not updated_body:
        logging.error("Incomplete data provided")
        return jsonify({"error": "Incomplete data provided"}), 400

    try:
        # Read the current content from the data.txt file
        with open('data.txt', 'r') as file:
            lines = file.readlines()

        # Check if the form_id already exists in the file
        form_exists = False
        for i in range(0, len(lines), 3):
            if lines[i].strip().startswith("form_id:"):
                existing_form_id = lines[i].strip().split(":")[1].strip()
                existing_form_id = existing_form_id.strip('"')  # Remove quotes
                logging.debug(f"Found form_id in data.txt: {existing_form_id}")
                if existing_form_id == form_id:
                    # Update existing content
                    lines[i+1] = f'Subject: {updated_subject}\n'
                    lines[i+2] = f'Body: {updated_body}\n'
                    form_exists = True
                    logging.debug("Updated existing content")
                    break

        # If the form_id does not exist, add new content
        if not form_exists:
            lines.append(f'form_id: "{form_id}"\n')
            lines.append(f'Subject: {updated_subject}\n')
            lines.append(f'Body: {updated_body}\n')
            logging.debug("Added new content")

        # Write the updated content back to the file
        with open('data.txt', 'w') as file:
            file.writelines(lines)

        logging.debug("Email content updated successfully")
        return jsonify({"message": "Email content updated successfully"}), 200
    except Exception as e:
        logging.error(f"Error updating email content: {str(e)}")
        return jsonify({"error": "Failed to update email content"}), 500



def calculate_signature(payload):
    secret = TYPEFORM_SECRET.encode('utf-8')
    expected_signature = hmac.new(secret, payload, hashlib.sha256).digest()
    encoded_expected_signature = base64.b64encode(expected_signature).decode()
    return "sha256="+ encoded_expected_signature

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
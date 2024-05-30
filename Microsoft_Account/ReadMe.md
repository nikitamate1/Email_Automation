# Email Automation System
This project is an email automation system built using Flask and Streamlit. It handles incoming webhook requests to send automated emails and allows updating email content via a Streamlit interface. The email system supports both plain text and HTML emails, integrating with Brevo (formerly known as SendinBlue) for sending emails.

## Features
* Automated Email Sending: Send automated emails in response to webhook events.
* HTML Email Support: Emails can be formatted in HTML, including clickable links.
* Dynamic Email Content: Update email subjects and bodies based on form IDs.
* BCC Support: Emails can include BCC recipients.
* Secure Communication: HMAC signature verification ensures that only legitimate webhook events are processed.


## Prerequisites
Download prerequisites by using following command:
``` pip install -r requirements.txt ```

## Installation
1. Clone the repository:

```git clone https://github.com/yourusername/email-automation-system.git```
```cd Main_Files```

2. Install dependencies:

* ```pip install -r requirements.txt```
* Set up environment variables:
* Create a .env file in the root directory and add the following environment variables:

3. Environment Variables(.env)

* SMTP_SERVER=smtp.brevo.com
* SMTP_PORT=587
* NOREPLY_EMAIL=your-email@domain.com
* EMAIL_PASSWORD=your-email-password
* TYPEFORM_SECRET=your-typeform-secret*

## Running the Application
* Start the Flask server:

```python app.py```

* Start the ngrok server:

```ngrok http 5000```

* Start the Streamlit interface in another terminal:

```streamlit run input.py```

## Usage
1. Sending Automated Emails
Emails are sent in response to webhook events from Typeform. The webhook payload includes a form_id, which is used to determine the subject and body of the email. The email content is loaded from a data.txt file that stores the subject and body for each form ID.

2. Updating Email Content
The Streamlit interface allows updating the email content for different form IDs.

Open the Streamlit interface:
Go to ``` http://localhost:8501 ``` in your web browser.

3. Enter Form ID, Subject, and Body:

* Enter the Form ID for which you want to update the content.
* Enter the Subject Line.
* Enter the Body Text.

4. Update Content:
Click the "Update Email Content" button. The content will be converted to HTML and updated in the data.txt file.

## How Emails are Sent

### Webhook Handling:

* The /api/webhook endpoint receives webhook events from Typeform.
* The payload includes the form_id and responses, including email addresses.
* The signature of the payload is verified using HMAC to ensure it’s from a legitimate source.
* Content Loading: The form_id from the payload is used to load the corresponding subject and body from the data.txt file.
If a match is found, the email content is prepared and personalized.
Email Sending:

* Emails are sent using the SMTP server of Brevo.
* The send_automated_emails function sends the emails, supporting both plain text and HTML formats.


### File Structure
```
email-automation-system/
│
├── app.py              # Flask application to handle webhooks and send emails
├── input.py            # Streamlit application to update email content
├── requirements.txt    # Python dependencies
├── data.txt            # Stores email content for different form IDs
├── .env                # Environment variables
└── README.md           # Project documentation
```

* Logging
Logs are stored in app.log and include information about received webhooks, email sending status, and errors.



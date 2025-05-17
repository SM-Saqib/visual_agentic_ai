import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders  # Import encoders for encoding attachments


def send_email(
    sender_email,
    sender_password,
    receiver_email,
    subject,
    body,
    attachment_path=None,
    email_service_provider="outlook",
):
    """
    Sends an email with optional attachment.

    Args:
        sender_email (str): The sender's email address.
        sender_password (str): The sender's email password or app password.
        receiver_email (str): The recipient's email address.
        subject (str): The subject of the email.
        body (str): The body of the email.
        attachment_path (str, optional): Path to the file to attach. Defaults to None.
    """
    try:
        # Create a multipart message object
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        # Attach the body of the email
        message.attach(MIMEText(body, "plain"))  # Use 'html' for HTML content

        # Attach a file if provided
        if attachment_path:
            try:
                with open(attachment_path, "rb") as attachment:
                    # Add the attachment to the message
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                # Encode the payload in base64
                encoders.encode_base64(part)

                # Add header as key/value pair to attachment part
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={attachment_path.split('/')[-1]}",
                )

                # Attach the part to the message
                message.attach(part)
            except FileNotFoundError:
                print(f"Attachment file not found: {attachment_path}")
                return

        # Connect to the SMTP server
        if email_service_provider == "gmail":
            # Use Gmail's SMTP server
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:  # Gmail SMTP server
                print("Connecting to the SMTP server with ", sender_email)

                server.login(sender_email, sender_password)

                print("Logged in successfully")
                # Send the email
                server.sendmail(sender_email, receiver_email, message.as_string())
                print("Email sent successfully!")

        if email_service_provider == "outlook":
            # with smtplib.SMTP("smtp.office365.com", 587) as server:
            #     # server.ehlo()
            #     print("Connecting to the SMTP server with ", sender_email)
            #     server.starttls()

            #     print("start tls")
            #     server.login(sender_email, sender_password)

            #     print("Logged in successfully")
            #     # Send the email
            #     server.send_message(sender_email, receiver_email, message.as_string())
            #     print("Email sent successfully!")
            with smtplib.SMTP_SSL("smtp.office365.com", 465) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, receiver_email, message.as_string())

        print(f"Email sent successfully to {receiver_email}")

    except smtplib.SMTPAuthenticationError:
        print("Authentication error: Please check your email and password.")
    except Exception as e:
        print(f"Error sending email: {e}")


def send_email_via_godaddy_office365(
    sender_email, sender_password, receiver_email, subject, body
):
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.office365.com", 587) as server:
            server.set_debuglevel(1)
            # Use a valid FQDN instead of the default hostname.
            server.ehlo("getsmooth.ai")
            if "starttls" in server.esmtp_features:
                server.starttls()
                server.ehlo("getsmooth.ai")
            else:
                print(
                    "STARTTLS not supported by server; cannot proceed with secure login."
                )
                return
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            print("Email sent successfully!")
    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")


if __name__ == "__main__":
    # Replace with your actual email credentials and recipient details
    sender_email = "sophie@getsmooth.ai"  # Your Gmail address
    sender_password = (
        "SmoothAI2025$"  # Your Gmail app password (recommended) or regular password
    )
    receiver_email = "saqibfarooq125@gmail.com"  # The recipient's email address
    subject = "Test Email from Python"
    body = "This is a test email sent using Python's smtplib library."
    attachment_file = "example.txt"  # Optional: Path to a file you want to attach

    # Create a dummy attachment file for testing
    with open(attachment_file, "w") as f:
        f.write("This is the content of the example attachment file.")

    # send_email(
    #     sender_email, sender_password, receiver_email, subject, body, attachment_file
    # )
    # To send without attachment, just omit the attachment_file argument:
    # send_email(sender_email, sender_password, receiver_email, subject, body)

    send_email_via_godaddy_office365(
        sender_email, sender_password, receiver_email, subject, body
    )

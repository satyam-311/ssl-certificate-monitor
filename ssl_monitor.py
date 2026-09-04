import os
import ssl
import socket
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage


# =========================
# Configuration
# =========================

DOMAIN = "popinandplay.twigstylehub.com"
PORT = 443

# Send warning when certificate has this many days or less remaining
WARNING_DAYS = 15


# =========================
# Get SSL Certificate
# =========================

def get_certificate_expiry(domain):
    context = ssl.create_default_context()

    with socket.create_connection((domain, PORT), timeout=15) as sock:
        with context.wrap_socket(
            sock,
            server_hostname=domain
        ) as ssl_socket:

            certificate = ssl_socket.getpeercert()

    expiry_string = certificate["notAfter"]

    expiry_date = datetime.strptime(
        expiry_string,
        "%b %d %H:%M:%S %Y %Z"
    ).replace(tzinfo=timezone.utc)

    return expiry_date


# =========================
# Get Email Recipients
# =========================

def get_recipients():

    alert_email = os.environ["ALERT_EMAIL"]

    # Support multiple recipients separated by commas
    recipients = [
        email.strip()
        for email in alert_email.split(",")
        if email.strip()
    ]

    return recipients


# =========================
# Send SSL Alert Email
# =========================

def send_email(days_left, expiry_date):

    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_username = os.environ["SMTP_USERNAME"]
    smtp_password = os.environ["SMTP_PASSWORD"]

    recipients = get_recipients()

    message = EmailMessage()

    message["Subject"] = (
        f"SSL Certificate Warning - {DOMAIN} "
        f"expires in {days_left} days"
    )

    message["From"] = smtp_username
    message["To"] = ", ".join(recipients)

    message.set_content(
        f"""
SSL Certificate Expiry Warning

Domain:
{DOMAIN}

Certificate expires:
{expiry_date.strftime("%Y-%m-%d %H:%M:%S UTC")}

Days remaining:
{days_left} days

Please renew/check the SSL certificate before it expires.

This is an automated monitoring alert.
"""
    )

    # Port 465 uses SSL directly
    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:

        server.login(
            smtp_username,
            smtp_password
        )

        server.send_message(
            message,
            to_addrs=recipients
        )

    print("Alert email sent successfully.")
    print("Recipients:")
    for recipient in recipients:
        print(f"  - {recipient}")


# =========================
# Send Test Email
# =========================

def send_test_email():

    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_username = os.environ["SMTP_USERNAME"]
    smtp_password = os.environ["SMTP_PASSWORD"]

    recipients = get_recipients()

    message = EmailMessage()

    message["Subject"] = (
        f"SSL Monitor TEST - {DOMAIN}"
    )

    message["From"] = smtp_username
    message["To"] = ", ".join(recipients)

    message.set_content(
        f"""
SSL Certificate Monitor - TEST EMAIL

This is a test email to verify that the SSL
certificate monitoring alert system is working.

Domain:
{DOMAIN}

Test status:
Email configuration is working successfully.

Recipients:
{", ".join(recipients)}

IMPORTANT:
This is only a test email.
No actual SSL expiry warning is being reported.

This is an automated monitoring test.
"""
    )

    # Port 465 uses SSL directly
    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:

        server.login(
            smtp_username,
            smtp_password
        )

        server.send_message(
            message,
            to_addrs=recipients
        )

    print("Test email sent successfully.")

    print("Recipients:")
    for recipient in recipients:
        print(f"  - {recipient}")


# =========================
# Send Error Email
# =========================

def send_error_email(error):

    try:

        smtp_host = os.environ["SMTP_HOST"]
        smtp_port = int(os.environ.get("SMTP_PORT", "465"))
        smtp_username = os.environ["SMTP_USERNAME"]
        smtp_password = os.environ["SMTP_PASSWORD"]

        recipients = get_recipients()

        message = EmailMessage()

        message["Subject"] = (
            f"SSL Monitor ERROR - {DOMAIN}"
        )

        message["From"] = smtp_username
        message["To"] = ", ".join(recipients)

        message.set_content(
            f"""
SSL Certificate Monitor Error

The SSL monitor could not check:

{DOMAIN}

Error:
{error}

Please check the website/SSL configuration.

This is an automated monitoring alert.
"""
        )

        # Port 465 uses SSL directly
        with smtplib.SMTP_SSL(
            smtp_host,
            smtp_port
        ) as server:

            server.login(
                smtp_username,
                smtp_password
            )

            server.send_message(
                message,
                to_addrs=recipients
            )

        print("Error alert email sent successfully.")

    except Exception as email_error:

        print(
            f"Could not send error email: {email_error}"
        )


# =========================
# Main
# =========================

def main():

    # =========================
    # TEST EMAIL MODE
    # =========================
    #
    # Set TEST_EMAIL=true in GitHub Actions
    # to test email delivery.
    #
    # After testing, REMOVE TEST_EMAIL=true
    # from the workflow.
    # =========================

    if os.environ.get("TEST_EMAIL", "").lower() == "true":

        print("=================================")
        print("SSL MONITOR TEST EMAIL MODE")
        print("=================================")

        send_test_email()

        print("Test completed.")
        return


    # =========================
    # NORMAL SSL MONITORING
    # =========================

    print(
        f"Checking SSL certificate for: {DOMAIN}"
    )

    try:

        # Get certificate expiry date
        expiry_date = get_certificate_expiry(DOMAIN)

        # Current UTC time
        now = datetime.now(timezone.utc)

        # Calculate remaining time
        seconds_left = (
            expiry_date - now
        ).total_seconds()

        days_left = int(
            seconds_left / 86400
        )

        print(
            f"Certificate expiry: {expiry_date}"
        )

        print(
            f"Days remaining: {days_left}"
        )


        # =========================
        # Certificate Expired
        # =========================

        if seconds_left <= 0:

            print(
                "SSL certificate has EXPIRED."
            )

            send_email(
                days_left,
                expiry_date
            )


        # =========================
        # Certificate Near Expiry
        # =========================

        elif days_left <= WARNING_DAYS:

            print(
                "SSL certificate is approaching expiry."
            )

            send_email(
                days_left,
                expiry_date
            )


        # =========================
        # Certificate OK
        # =========================

        else:

            print(
                "SSL certificate is valid."
            )

            print(
                "No email required."
            )


    # =========================
    # SSL Check Error
    # =========================

    except Exception as error:

        print(
            f"ERROR: {error}"
        )

        # Send error alert
        send_error_email(error)


# =========================
# Program Entry Point
# =========================

if __name__ == "__main__":
    main()
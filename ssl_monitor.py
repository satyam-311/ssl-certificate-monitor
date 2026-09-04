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
        with context.wrap_socket(sock, server_hostname=domain) as ssl_socket:
            certificate = ssl_socket.getpeercert()

    expiry_string = certificate["notAfter"]

    expiry_date = datetime.strptime(
        expiry_string,
        "%b %d %H:%M:%S %Y %Z"
    ).replace(tzinfo=timezone.utc)

    return expiry_date


# =========================
# Send Email
# =========================

def send_email(days_left, expiry_date):

    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_username = os.environ["SMTP_USERNAME"]
    smtp_password = os.environ["SMTP_PASSWORD"]

    alert_email = os.environ["ALERT_EMAIL"]

    message = EmailMessage()

    message["Subject"] = (
        f"SSL Certificate Warning - {DOMAIN} expires in {days_left} days"
    )

    message["From"] = smtp_username
    message["To"] = alert_email

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

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_username, smtp_password)
        server.send_message(message)


# =========================
# Main
# =========================

def main():

    print(f"Checking SSL certificate for: {DOMAIN}")

    try:
        expiry_date = get_certificate_expiry(DOMAIN)

        now = datetime.now(timezone.utc)

        seconds_left = (expiry_date - now).total_seconds()
        days_left = int(seconds_left / 86400)

        print(f"Certificate expiry: {expiry_date}")
        print(f"Days remaining: {days_left}")

        if seconds_left <= 0:
            print("SSL certificate has EXPIRED.")
            send_email(days_left, expiry_date)

        elif days_left <= WARNING_DAYS:
            print("SSL certificate is approaching expiry.")
            send_email(days_left, expiry_date)

        else:
            print("SSL certificate is valid. No email required.")

    except Exception as error:

        print(f"ERROR: {error}")

        # Send an alert if the certificate cannot be checked
        # This can indicate an SSL/server/DNS problem.
        try:
            smtp_host = os.environ["SMTP_HOST"]
            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
            smtp_username = os.environ["SMTP_USERNAME"]
            smtp_password = os.environ["SMTP_PASSWORD"]
            alert_email = os.environ["ALERT_EMAIL"]

            message = EmailMessage()
            message["Subject"] = f"SSL Monitor ERROR - {DOMAIN}"
            message["From"] = smtp_username
            message["To"] = alert_email

            message.set_content(
                f"""
The SSL monitor could not check:

{DOMAIN}

Error:
{error}

Please check the website/SSL configuration.
"""
            )

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(message)

        except Exception as email_error:
            print(f"Could not send error email: {email_error}")


if __name__ == "__main__":
    main()
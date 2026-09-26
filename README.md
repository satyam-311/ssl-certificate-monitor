# SSL Certificate Monitor

A small Python script that checks when a website's SSL certificate expires and emails you before it does.

## Purpose

If an SSL certificate expires, visitors see a security warning. This project checks the certificate once a day and sends an email alert when:

- the certificate expires in **15 days or less**
- the certificate has **already expired**
- the check **fails** (for example, the site is down or the SSL setup is broken)

If the certificate is fine, no email is sent.

## What it uses

- **Python 3**, standard library only (`ssl`, `socket`, `smtplib`, `email`). Nothing to `pip install`.
- **GitHub Actions** to run the check every day at 04:00 UTC. You can also start it by hand from the Actions tab.
- **SMTP over SSL** (port 465 by default) to send the alert emails.

## Files

| File | What it does |
| --- | --- |
| `ssl_monitor.py` | Checks the certificate and sends the emails |
| `.github/workflows/ssl-monitor.yml` | Runs the script daily on GitHub Actions |

## Setup

1. In your GitHub repo, go to **Settings → Secrets and variables → Actions** and add these secrets:

   | Secret | Example |
   | --- | --- |
   | `SMTP_HOST` | `smtp.gmail.com` |
   | `SMTP_PORT` | `465` |
   | `SMTP_USERNAME` | the email account that sends alerts |
   | `SMTP_PASSWORD` | its password or app password |
   | `ALERT_EMAIL` | who gets alerts; use commas for more than one address |

2. To monitor a different site or change the warning window, edit these values at the top of `ssl_monitor.py`:

   ```python
   DOMAIN = "popinandplay.twigstylehub.com"
   WARNING_DAYS = 15
   ```

## Testing email

Set `TEST_EMAIL=true` in the workflow's `env` and run it. You get a test email instead of a real check. Remove it when you're done.

## Run locally

```bash
export SMTP_HOST=... SMTP_PORT=465 SMTP_USERNAME=... SMTP_PASSWORD=... ALERT_EMAIL=...
python ssl_monitor.py
```

## License

MIT

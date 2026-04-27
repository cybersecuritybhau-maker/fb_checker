# 🔥 FB OTP Trigger Tool v3.0

Facebook forgot password OTP trigger tool.
যে কোন ফরম্যাটে ফোন নাম্বার দিয়ে Facebook OTP ট্রিগার করুন।

## Features
- ✅ যেকোনো ফরম্যাটে নাম্বার নিবে (+ ছাড়া, কমা ছাড়া, স্পেস দিয়েও)
- ✅ Multi-threading (3-5 threads)
- ✅ Proxy support (HTTP/HTTPS)
- ✅ Real-time OTP trigger on Facebook forgot password
- ✅ Auto-save results
- ✅ Termux optimized

## Installation (Termux)
```bash
pkg update -y && pkg upgrade -y
pkg install python chromium -y
pip install selenium webdriver-manager phonenumbers requests beautifulsoup4
git clone https://github.com/cybersecuritybhau-maker/fb_checker.git
cd fb_checker
python fb_checker.py

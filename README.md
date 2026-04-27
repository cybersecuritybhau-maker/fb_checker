# 🔥 FB Phone Checker v2.0

Facebook phone number checker with multi-threading, proxy rotation, and OTP trigger. Works worldwide.

## Features

- ✅ Worldwide phone number support (BD, US, UK, India, etc.)
- ✅ Multi-threading (up to 20 threads)
- ✅ Proxy rotation (HTTP/HTTPS/SOCKS5)
- ✅ Automatic OTP trigger on valid accounts
- ✅ Auto-save valid accounts in real-time
- ✅ JSON + TXT export
- ✅ Termux optimized
- ✅ No Telegram dependency

## Installation

```bash
pkg update -y && pkg upgrade -y
pkg install python chromium -y
pip install selenium webdriver-manager phonenumbers
git clone https://github.com/cybersecuritybhau-maker/fb_checker.git
cd fb_checker
python fb_checker.py

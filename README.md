# Facebook OTP Trigger Tool v7.0

**Authorized Penetration Testing Tool** — Trigger Facebook password reset OTPs to verify phone number registration status.

> ⚠️ **IMPORTANT**: This tool is for **authorized security testing only**. Only use on phone numbers you own or have explicit permission to test. Unauthorized use may violate Facebook's Terms of Service and applicable laws.

---

## 📋 Features

| Feature | Description |
|---------|-------------|
| **OTP Send** | Trigger Facebook password reset SMS OTP to target number |
| **Valid Number Check** | Check if a phone number is registered on Facebook (no OTP sent) |
| **Bulk OTP** | Mass OTP triggering from a list of numbers |
| **Number Upload** | Load numbers from TXT file for batch processing |
| **Proxy Manager** | Add, delete, view, and clear proxies (format: `ip:port` or `user:pass@ip:port`) |
| **Results Storage** | View summary of all processed numbers with status categories |
| **Auto Token Refresh** | Automatically detects TOKEN_ERROR and refreshes LSD token |
| **Multi-Pattern LSD Extraction** | 8 regex patterns to extract LSD token from Facebook page structure |
| **Debug HTML Saving** | Saves HTML responses on failure for troubleshooting |

---

## 🚀 Installation (Termux / Linux / Windows)

### Termux (Android)

```bash
pkg update && pkg upgrade -y
pkg install python git -y
pip install requests

git clone https://github.com/cybersecuritybhau-maker/fb_checker.git
cd fb_checker
python fb_checker.py

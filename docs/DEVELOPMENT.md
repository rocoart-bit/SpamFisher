# SpamFisher Development Guide

## Project Status: Working Prototype

SpamFisher is a **functional prototype** that successfully detects and blocks remote access scams in real-time. It has been tested with AnyDesk and works as designed.

---

## Table of Contents
1. [How SpamFisher Works](#how-spamfisher-works)
2. [Quick Start](#quick-start)
3. [Project Structure](#project-structure)
4. [Detection Logic Explained](#detection-logic-explained)
5. [Current Limitations](#current-limitations)
6. [Troubleshooting](#troubleshooting)

---

### Core Concept

SpamFisher monitors your computer for remote access software (AnyDesk, TeamViewer, etc.) and detects when someone **actually connects** to control your computer remotely. When a connection is detected, it:

1. **Immediately shows a full-screen warning** explaining the scam
2. **Shows the attacker's country** (geolocation of remote IP)
3. **Gives the user a choice:**
   - **BLOCK** → Kills the connection instantly
   - **ALLOW** → Permits the connection (for legitimate support)

### Why This Is Important

**How remote access scams work:**
1. Victim receives fake email/popup about virus/security issue
2. Scammer directs them to call "support" or visit fake website
3. Scammer convinces them to install remote access software
4. Once connected, scammer steals banking passwords and money

**SpamFisher breaks this chain** by detecting the moment the scammer connects and giving the victim clear information about what's happening.

### The Detection Challenge

Remote access software like AnyDesk maintains multiple connections:
- **Relay servers** (Germany, France, etc.) on port 443 - these are normal background connections
- **Actual remote user** connecting IN to your computer - this is the scam

SpamFisher had to be smart enough to distinguish between these two scenarios.

---

## Quick Start

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `psutil` - Process and network monitoring
- `requests` - IP geolocation lookups
- `tkinter` - GUI (included with Python on Windows)

### 2. Run SpamFisher

```bash
python main.py
```

Or with specific Python version:
```bash
py -3.14 main.py
```

### 3. What You'll See

```
==================================================
SpamFisher - Remote Access Scam Protection
==================================================

[DEBUG] SpamFisher initialized - whitelist empty: True
SpamFisher monitoring started...
Watching for remote access threats...
```

The program runs silently in the background, printing dots occasionally. **Only alerts when actual remote connection detected.**

---

## Project Structure

```
SpamFisher/
├── src/
│   ├── main.py          # Application controller, whitelist management
│   ├── monitor.py       # Detection engine, network analysis
│   ├── ui.py           # Full-screen warning interface
│   └── config.py       # Settings, remote software database, messages
├── docs/
│   └── DEVELOPMENT.md  # This file
├── resources/          # For icons/images (future use)
├── requirements.txt    # Python dependencies
├── README.md          # Project overview
└── .gitignore        # Git ignore rules
```

### Key Files

**config.py** - Database and Settings
- List of 7 remote access software to monitor (AnyDesk, TeamViewer, VNC, etc.)
- Warning messages in English and Romanian
- Settings: language, scan interval, logging

**monitor.py** - Detection Engine
- Scans running processes every 2 seconds
- Identifies remote access software
- Analyzes network connections
- Distinguishes relay servers from actual remote users
- Returns threat information when scam detected

**ui.py** - Warning Interface
- Full-screen overlay (cannot be minimized)
- Shows geolocation of attacker
- Explains how the scam works (educational)
- Two buttons: BLOCK (red, prominent) and ALLOW (gray, small)

**main.py** - Application Controller
- Manages monitoring loop
- Handles user decisions (block/allow)
- Maintains whitelist of allowed connections
- Coordinates between detection and UI

---

## Detection Logic

### Smart Detection Algorithm

SpamFisher uses a multi-layered approach to detect actual remote sessions while ignoring false positives:

#### Step 1: Find Running Remote Access Software

```python
Scan all processes → Match against known software list → Track PIDs
```

Currently monitors:
- AnyDesk (AnyDesk.exe)
- TeamViewer (TeamViewer.exe, TeamViewer_Service.exe)
- UltraViewer (UltraViewer_Desktop.exe)
- SupRemo (Supremo.exe)
- Chrome Remote Desktop (remoting_host.exe)
- VNC (vncviewer.exe, winvnc.exe)
- RDP (mstsc.exe)

#### Step 2: Identify Listening Ports

```python
For each remote software process → Find which ports it's LISTENING on
```

**Why this matters:** Remote access software listens on specific ports to accept incoming connections. These can be:
- **Standard ports:** 6568 (AnyDesk), 5938 (TeamViewer), 3389 (RDP)
- **Dynamic ports:** Random high ports like 52048 if standard ports are blocked

#### Step 3: Analyze External Connections

```python
For each process → Get all ESTABLISHED connections → Filter to external IPs only
```

**External IP definition:** Not localhost (127.x), not LAN (192.168.x, 10.x, 172.16-31.x)

#### Step 4: Smart Threat Detection (Priority Order)

**PRIORITY 1: Incoming connections on known remote desktop ports**
```
If connection uses port 6568, 5938, 3389, etc. on local side
→ Someone is connecting TO this computer
→ ALERT!
```

**PRIORITY 2: Incoming connections on listening ports (excluding relay servers)**
```
If connection is on a port the software is LISTENING on
AND remote port is NOT 443 (relay servers use 443)
→ Actual remote user connecting
→ ALERT!
```

**PRIORITY 3: Multiple connections with remote desktop protocols**
```
If 3+ external connections AND at least one uses remote desktop port
→ Unusual pattern, likely active session
→ ALERT!
```

**Otherwise:** Ignore (just background relay server connections)


**Works with any port** - Doesn't rely on specific port numbers  
**Catches portable versions** - Detects by behavior, not installation  
**Filters relay servers** - Ignores normal background connections  
**Universal approach** - Works for all remote desktop software  
**No false positives** - Only alerts on actual incoming remote sessions  

---

## Current Limitations

### Technical Limitations

1. **Windows Only**
   - Uses Windows-specific APIs (psutil on Windows)
   - GUI built with tkinter
   - **Solution:** Linux/Mac support possible but needs separate implementation

2. **Requires Admin Rights for Full Blocking**
   - Process termination works without admin
   - Windows Firewall rules need admin privileges (not yet implemented)
   - **Current state:** Kills process only, doesn't add firewall rules

3. **No Installer**
   - Must run from Python directly
   - No system tray icon
   - Doesn't auto-start with Windows
   - **Impact:** Not user-friendly for non-technical users

4. **Debug Mode Enabled**
   - Prints verbose logging to console
   - **Impact:** Can be noisy, but useful for troubleshooting

5. **Antivirus Will Flag It**
   - PyInstaller executables are commonly flagged as malware
   - Process monitoring behavior looks suspicious to AVs
   - **Critical blocker for distribution**

### Feature Limitations

1. **No Persistent Whitelist**
   - Allowed connections only remembered during current session
   - **Impact:** Must re-allow legitimate connections after restart

2. **No Configuration UI**
   - Settings must be edited in config.py
   - **Impact:** Users can't easily change language or add custom software

3. **Single Language at Runtime**
   - Must choose English or Romanian before starting
   - **Impact:** Can't switch language without editing config file

4. **No Notification System**
   - No email/SMS alerts to family members
   - **Impact:** Relies entirely on victim seeing and understanding the warning

5. **Limited Software Database**
   - Only 7 remote access tools monitored
   - Scammers could use obscure software
   - **Impact:** Not comprehensive protection

---

## Troubleshooting

### Common Issues

**"Module not found: psutil"**
```bash
# Solution: Install dependencies
pip install psutil requests
# Or with specific Python version:
py -3.14 -m pip install psutil requests
```

**"Permission denied when killing process"**
```bash
# Solution: Run as Administrator
# Right-click Command Prompt → "Run as administrator"
# Then run: py -3.14 main.py
```

**Warning screen doesn't appear**
```bash
# Check if tkinter is installed:
python -c "import tkinter"
# If error, reinstall Python with tkinter option checked
```

**False positive: Alert on relay servers**
```bash
# Check debug output for:
# "Skipping connection on port 443 - likely relay server"
# If not seeing this, the detection needs adjustment
```

**No alert when actually connected**
```bash
# Check if:
# 1. You're connecting from EXTERNAL network (not same LAN)
# 2. Connection is actually established (not just pending)
# 3. Remote access software is in the database (config.py)
```

**Geolocation shows "Unknown"**
```bash
# Check internet connection
# IP-API might be rate-limited (free tier = 45 requests/minute)
# Wait a minute and try again
```

### Debug Mode

To see detailed detection information:

```bash
# Debug output is currently enabled by default
# Shows:
# - Which processes are being checked
# - All connections found
# - Why alerts are triggered or ignored
# - Whitelist status
```

To disable debug output (for production use):
- Remove `print("[DEBUG]...")` statements from monitor.py and main.py


## Contributing

Open-source, contributions welcome for:

- Adding support for new remote access software
- Improving detection algorithms
- Translations to more languages
- UI/UX improvements
- Testing on different Windows versions
- Documentation improvements

---

## License

GPL v3.

---

## Contact & Support

**Creator:** Robert Costea 
**Motivation:** Protecting vulnerable people from remote access scams

---

## Final Notes

SpamFisher is a **working prototype that successfully protects against remote access scams.** The core detection logic is solid and tested. 

SpamFisher could help thousands of vulnerable people avoid losing money to scammers.

**The mission is: Make scam attempts visible to victims at the critical moment.**

SpamFisher achieves this mission. Now it needs the polish and distribution infrastructure to reach the people who need it most.

---

*Last updated: December 2025*  
*Status: Working Prototype*  

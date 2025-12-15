# SpamFisher Development & Security Guide

## Project Status: Working Prototype with Security Enhancements

SpamFisher is a **functional, security-enhanced prototype** that successfully detects and blocks remote access scams in real-time. It has been tested with AnyDesk and includes enterprise-grade security features.

---

## Table of Contents
1. [How SpamFisher Works](#how-spamfisher-works)
2. [Security Architecture](#security-architecture)
3. [Quick Start](#quick-start)
4. [Project Structure](#project-structure)
5. [Detection Logic Explained](#detection-logic-explained)
6. [Security Features](#security-features)
7. [Current Limitations](#current-limitations)
10. [Troubleshooting](#troubleshooting)

---

## Core Concept

SpamFisher monitors your computer for remote access software (AnyDesk, TeamViewer, etc.) and detects when someone **actually connects** to control your computer remotely. When a connection is detected, it:

1. **Immediately shows a full-screen warning** explaining the scam
2. **Shows the attacker's country** (geolocation of remote IP)
3. **Gives the user a choice:**
   - **BLOCK** → Kills the connection instantly + adds firewall rule
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

## Security Architecture

### Multi-Layer Protection System

```
┌─────────────────────────────────────────────────┐
│                  SpamFisher                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │   Security Layer (security.py)           │  │
│  │   ✓ Admin Rights Management              │  │
│  │   ✓ Integrity Verification               │  │
│  │   ✓ Encrypted Whitelist Storage          │  │
│  │   ✓ Input Validation                     │  │
│  └──────────────────────────────────────────┘  │
│                     ↓                           │
│  ┌──────────────────────────────────────────┐  │
│  │   Detection Engine (monitor.py)          │  │
│  │   ✓ Process Monitoring                   │  │
│  │   ✓ Network Analysis                     │  │
│  │   ✓ HTTPS Geolocation                    │  │
│  │   ✓ Relay Server Filtering               │  │
│  └──────────────────────────────────────────┘  │
│                     ↓                           │
│  ┌──────────────────────────────────────────┐  │
│  │   Action Layer                           │  │
│  │   ✓ Kill Process Tree (all children)    │  │
│  │   ✓ Windows Firewall Rules              │  │
│  │   ✓ Encrypted Whitelist Storage         │  │
│  └──────────────────────────────────────────┘  │
│                     ↓                           │
│  ┌──────────────────────────────────────────┐  │
│  │   User Interface                         │  │
│  │   ✓ Full-Screen Warning                  │  │
│  │   ✓ System Tray Icon                     │  │
│  │   ✓ Educational Content                  │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Security Features Implemented

#### 1. **Administrator Rights Management**
- Checks for admin privileges on startup
- Prompts user to elevate if needed (unless already admin)
- Gracefully degrades if admin denied
- Shows admin status in system tray menu

**Why Critical:** Windows Firewall rules require admin privileges

#### 2. **Enhanced Process Termination**
- Kills parent process AND all child processes
- Uses recursive tree termination
- Forces kill if graceful termination fails
- Prevents hidden processes from continuing

**Why Critical:** Some remote access tools spawn multiple processes

#### 3. **Windows Firewall Integration** 
- Adds inbound AND outbound firewall rules
- Blocks specific executable path permanently
- Rules persist across reboots
- Prevents software from reconnecting

**Why Critical:** Stops scammer from immediately reconnecting

#### 4. **Encrypted Whitelist Storage**
- Uses Fernet symmetric encryption
- Generates unique key per installation
- Validates data structure on load
- Falls back gracefully if encryption fails

**Files:**
- `whitelist.key` - Encryption key (keep secure!)
- `whitelist.enc` - Encrypted whitelist data

**Why Critical:** Prevents scammer from adding their IP to whitelist

#### 5. **Input Validation**
- Validates JSON structure on load
- Type checking on all data
- Graceful error handling
- Prevents malicious data injection

#### 6. **Integrity Verification**
- Checks critical files exist on startup
- Warns if files are missing/modified
- Prompts before continuing if compromised

**Future:** Cryptographic hashing and signature verification

#### 7. **HTTPS for All External Calls**
- Changed from `http://` to `https://` for geolocation
- Uses `ipapi.co` API (more reliable)
- Prevents man-in-the-middle attacks
- Encrypted communication only

---

## Quick Start

### 1. Install Python Dependencies

```
pip install -r requirements.txt
```

**Required packages:**
- `psutil` - Process and network monitoring
- `requests` - IP geolocation lookups
- `pystray` - System tray icon
- `Pillow` - Icon generation
- `cryptography` - Whitelist encryption
- `tkinter` - GUI (included with Python on Windows)

### 2. Run SpamFisher

**As regular user (will prompt for admin):**
```
python main.py
```

**Already running as admin (PowerShell/CMD):**
```
python main.py
# Will detect admin rights and run with full protection
```

**With specific Python version:**
```
py -3.14 main.py
```

### 3. What You'll See

```
==================================================
SpamFisher - Remote Access Scam Protection
SECURITY ENHANCED VERSION
==================================================

[SECURITY] Integrity check passed
[DEBUG] SpamFisher initialized
[DEBUG] Admin rights: Yes
[DEBUG] Permanent whitelist loaded: 0 entries
SpamFisher monitoring started...
Watching for remote access threats...
==================================================
SpamFisher is now running in system tray
Right-click the tray icon to exit
==================================================
```

**System tray icon:** Fisherman icon (green background) = protection active

---

## Project Structure

```
SpamFisher/
├── src/
│   ├── main.py          # Application controller, security integration
│   ├── monitor.py       # Detection engine, network analysis
│   ├── ui.py           # Full-screen warning interface
│   ├── config.py       # Settings, software database, messages
│   └── security.py     # Security functions (NEW)
├── docs/
│   ├── DEVELOPMENT.md  # This file (merged)
│   └── SECURITY.md     # Standalone security doc
├── resources/          # For icons/images (future use)
├── requirements.txt    # Python dependencies (updated)
├── README.md          # Project overview
├── .gitignore        # Git ignore rules
├── whitelist.key     # Encryption key (auto-generated)
└── whitelist.enc     # Encrypted whitelist (auto-generated)
```

### Key Files

**config.py** - Database and Settings
- List of 7 remote access software to monitor
- Warning messages in English and Romanian
- Settings: language, scan interval, logging
- HTTPS geolocation API endpoint

**monitor.py** - Detection Engine
- Scans running processes every 2 seconds
- Identifies remote access software
- Analyzes network connections
- Distinguishes relay servers from actual remote users
- Returns threat information when scam detected
- **Enhanced:** Better geolocation, improved blocking

**ui.py** - Warning Interface
- Full-screen overlay (cannot be minimized)
- Shows geolocation of attacker
- Explains how the scam works (educational)
- Two buttons: BLOCK (red) and ALLOW (gray)

**main.py** - Application Controller
- **Enhanced:** Security integration
- Manages monitoring loop
- Handles user decisions (block/allow)
- Maintains encrypted whitelist
- System tray icon with fisherman graphic
- Coordinates between detection, security, and UI

**security.py** - Security Module (NEW)
- Admin rights detection and elevation
- Process tree termination
- Windows Firewall rule management
- Encrypted whitelist handling
- Integrity verification
- Input validation

---

## Detection Logic

### The Smart Detection Algorithm

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

### Why This Detection Method Works

**Works with any port** - Doesn't rely on specific port numbers  
**Catches portable versions** - Detects by behavior, not installation  
**Filters relay servers** - Ignores normal background connections  
**Universal approach** - Works for all remote desktop software  
**No false positives** - Only alerts on actual incoming remote sessions  
**Security hardened** - Firewall rules prevent reconnection

---

## Security Features

### Threat Model

#### Threats We Protect Against:

✅ **Remote access scammers** (primary threat)
- Detection: Monitors for incoming remote connections
- Protection: Blocks connection, kills process tree, adds firewall rules

✅ **Process respawning**
- Detection: Kills entire process tree
- Protection: Firewall prevents reconnection

✅ **Whitelist tampering**
- Detection: Encrypted storage with Fernet
- Protection: Can't modify without encryption key

✅ **Configuration file injection**
- Detection: Input validation on all loads
- Protection: Rejects malformed data

✅ **Man-in-the-middle attacks**
- Detection: Uses HTTPS only
- Protection: Encrypted geolocation API calls

✅ **Multiple hidden processes**
- Detection: Process tree analysis
- Protection: Recursive termination

## Current Limitations

### Technical Limitations

1. **Windows Only**
   - Uses Windows-specific APIs
   - GUI built with tkinter
   - **Solution:** Linux/Mac support possible but needs separate implementation

2. **Requires Admin Rights for Full Protection**
   - Process termination works without admin
   - Windows Firewall rules require admin privileges
   - **Current state:** Kills process only without admin, full protection with admin

3. **No Installer**
   - Must run from Python directly
   - No auto-start with Windows
   - **Impact:** Not user-friendly for non-technical users

4. **Debug Mode Enabled**
   - Prints verbose logging to console
   - **Impact:** Can be noisy, but useful for troubleshooting

5. **Antivirus Will Flag It**
   - Process monitoring looks suspicious
   - PyInstaller executables commonly flagged
   - **Critical blocker for distribution**

### Feature Limitations

1. **No Persistent Firewall Rules Management**
   - Rules added but not centrally managed
   - **Impact:** Manual cleanup needed if uninstalling

2. **No Configuration UI**
   - Settings must be edited in config.py
   - **Impact:** Users can't easily change language

3. **Single Language at Runtime**
   - Must choose English or Romanian before starting
   - **Impact:** Can't switch language without restart

4. **No Notification System**
   - No email/SMS alerts to family members
   - **Impact:** Relies entirely on victim seeing warning

5. **Limited Software Database**
   - Only 7 remote access tools monitored
   - **Impact:** Scammers could use obscure software

### Security Limitations

1. **Encryption Key Storage**
   - Key stored in plaintext file
   - **Risk:** Medium
   - **Future:** Use Windows DPAPI

2. **No Protected Mode**
   - Can be terminated by other processes
   - **Risk:** High if system compromised
   - **Future:** Run as protected Windows service

3. **Basic Integrity Check**
   - Only verifies files exist
   - **Risk:** Medium
   - **Future:** Cryptographic hashing

4. **Local Threat Database**
   - Updates require new release
   - **Risk:** Medium
   - **Future:** Cloud-based threat intelligence

---

## Troubleshooting

### Common Issues

**"Module not found: cryptography"**
```
pip install cryptography
```

**"Permission denied when adding firewall rule"**
```
# Run as Administrator
# Or: SpamFisher will prompt for elevation
```

**Warning screen doesn't appear**
```
# Check if tkinter installed:
python -c "import tkinter"
```

**Firewall rules not added**
```
# Check admin rights:
# SpamFisher shows "Admin rights: Yes" on startup
# Without admin, only process killing works
```

**False positive: Alert on relay servers**
```
# Should see in debug:
# "Skipping connection on port 443 - likely relay server"
# If not, detection logic needs adjustment
```

**No alert when actually connected**
```
# Verify:
# 1. Connecting from EXTERNAL network (not LAN)
# 2. Connection actually established
# 3. Software is in database (config.py)
```

**Encryption error**
```
# Delete whitelist.key and whitelist.enc
# SpamFisher will regenerate them
```

### Debug Mode

Debug output is currently enabled by default and shows:
- Which processes are being checked
- All connections found
- Why alerts are triggered or ignored
- Whitelist status
- Admin rights status
- Security operations

## Contact & Support

**Creator:** Robert Costea (Romania)  
**GitHub:** https://github.com/rocoart-bit/SpamFisher  
**Motivation:** Protecting mother and other vulnerable people from remote access scams

---

## Final Notes

SpamFisher is a **working, security-enhanced prototype** that successfully protects against remote access scams. The detection logic is solid, the security architecture is robust, and it has been tested in real-world scenarios.

**Current State:**
-  Core detection works perfectly
-  Security features implemented
-  Real-world tested
-  System tray integration
-  Encrypted whitelist
-  Still needs installer and code signing for distribution

**The mission is: Make scam attempts visible to victims at the critical moment.**

SpamFisher achieves this mission with enterprise-grade security. Now it needs the infrastructure to reach the people who need it most.

---

*Last Updated: December 2025*  
*Version: 1.0 Security Enhanced*  
*Status: Working Prototype - Ready for Review*  

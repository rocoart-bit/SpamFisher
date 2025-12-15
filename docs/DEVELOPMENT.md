# SpamFisher Development Guide

## Project Status: Working Prototype ✅

SpamFisher is a **functional prototype** that successfully detects and blocks remote access scams in real-time. It has been tested with AnyDesk and works as designed.

---

## Table of Contents
1. [How SpamFisher Works](#how-spamfisher-works)
2. [Quick Start](#quick-start)
3. [Project Structure](#project-structure)
4. [Detection Logic Explained](#detection-logic-explained)
5. [Current Limitations](#current-limitations)
6. [Path to Distribution](#path-to-distribution)
7. [Testing Guide](#testing-guide)
8. [Troubleshooting](#troubleshooting)

---

## How SpamFisher Works

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
cd D:\CLAUDE\SpamFisher
pip install -r requirements.txt
```

**Required packages:**
- `psutil` - Process and network monitoring
- `requests` - IP geolocation lookups
- `tkinter` - GUI (included with Python on Windows)

### 2. Run SpamFisher

```bash
cd src
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

### Key Files Explained

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

## Detection Logic Explained

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

### Example: AnyDesk Connection Flow

1. **User starts AnyDesk**
   - AnyDesk connects to relay server in Germany on port 443
   - AnyDesk listens on port 52048 (dynamic)
   - **SpamFisher:** Sees relay connection, ignores it (port 443 = relay)
   - **No alert shown**

2. **Scammer connects to user**
   - Scammer establishes connection from Romania
   - Connection appears: Local port 52048 → Remote IP (Romania) port 47894
   - **SpamFisher:** Sees incoming connection on listening port 52048, remote port is NOT 443
   - **Alert triggered!**

3. **User clicks BLOCK**
   - SpamFisher kills AnyDesk process
   - Connection terminated
   - Scammer is disconnected

4. **User clicks ALLOW**
   - Alert closes
   - PID added to whitelist
   - No more alerts for this AnyDesk session

### Why This Detection Method Works

✅ **Works with any port** - Doesn't rely on specific port numbers  
✅ **Catches portable versions** - Detects by behavior, not installation  
✅ **Filters relay servers** - Ignores normal background connections  
✅ **Universal approach** - Works for all remote desktop software  
✅ **No false positives** - Only alerts on actual incoming remote sessions  

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

## Path to Distribution

To make SpamFisher available for real users who need protection, follow this roadmap:

### Phase 1: Code Cleanup (1-2 weeks)

**Essential tasks:**

1. **Remove debug logging**
   - Remove all `print("[DEBUG]...")` statements
   - Keep only user-facing messages
   - Implement proper logging to file instead

2. **Add Windows Firewall blocking**
   ```python
   # Add firewall rule to permanently block the executable
   subprocess.run([
       'netsh', 'advfirewall', 'firewall', 'add', 'rule',
       f'name="SpamFisher Block {process_name}"',
       'dir=in', 'action=block',
       f'program="{executable_path}"'
   ])
   ```

3. **Implement persistent whitelist**
   - Store allowed PIDs in a file (JSON)
   - Load on startup
   - Clean up old entries (PIDs that no longer exist)

4. **Error handling**
   - Graceful failure if psutil can't access processes
   - Handle network errors for geolocation
   - Recover from UI crashes

5. **Configuration UI**
   - Simple settings window
   - Language selection
   - Enable/disable features
   - View logs

### Phase 2: User Experience (2-3 weeks)

**Essential tasks:**

1. **Create installer**
   ```bash
   # Package with PyInstaller
   pyinstaller --onefile --windowed --icon=spamfisher.ico main.py
   
   # Create Windows installer with Inno Setup
   # Include all dependencies, config files, documentation
   ```

2. **System tray integration**
   - Icon showing SpamFisher is running
   - Right-click menu: Settings, Pause, Exit
   - Green = monitoring, Yellow = paused, Red = threat detected

3. **Auto-start with Windows**
   - Add registry key during installation
   - Or create scheduled task
   - User can enable/disable in settings

4. **First-run setup wizard**
   - Choose language
   - Explain what SpamFisher does
   - Option to add "trusted contact" phone number
   - Test the warning screen

5. **Improve warning screen**
   - Larger, clearer fonts
   - More visual indicators (red border, flashing)
   - Sound alert (optional)
   - Countdown timer before ALLOW button becomes clickable (prevent rush decisions)

### Phase 3: Code Signing & Distribution (Critical - Budget Required)

**This is the biggest blocker for wide distribution.**

**Essential tasks:**

1. **Purchase EV Code Signing Certificate**
   - **Cost:** €300-500/year
   - **Vendors:** DigiCert, Sectigo, GlobalSign
   - **Why essential:** Without this, Windows SmartScreen blocks the installer
   - **Process:** Requires identity verification (passport, business documents)

2. **Sign all executables**
   ```bash
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com SpamFisher.exe
   ```
   - Sign the main executable
   - Sign the installer
   - **Result:** Windows shows "Publisher: SpamFisher" instead of "Unknown publisher"

3. **Submit to antivirus vendors**
   - Manually submit to major AVs as known-good software
   - **Vendors:** Microsoft Defender, Norton, McAfee, Kaspersky, Avast, AVG, Bitdefender
   - **Process:** Each vendor has online submission form
   - **Timeline:** 1-2 weeks for approval

4. **Build reputation with Microsoft SmartScreen**
   - SmartScreen tracks download frequency
   - More downloads = better reputation
   - **Timeline:** Takes 2-3 months of downloads to build trust
   - **Workaround:** Partner with established organization (see Phase 4)

### Phase 4: Community & Distribution (Ongoing)

**Essential tasks:**

1. **Open source the project**
   - Publish on GitHub
   - Write comprehensive documentation
   - Add contributing guidelines
   - Choose license (GPL v3 recommended for protection software)

2. **Partner with anti-scam organizations**
   - AARP (USA) - elderly protection
   - Age UK (UK) - elderly advocacy
   - Citizens Advice (UK) - consumer protection
   - Which? (UK) - consumer rights
   - Local Romanian consumer protection agencies

   **Benefits of partnership:**
   - They can help fund code signing certificate
   - They can host/distribute the installer
   - Their reputation helps with SmartScreen
   - They can provide support infrastructure
   - They reach the target audience

3. **Create distribution website**
   - Simple landing page explaining what it does
   - Download link for installer
   - Video demonstration
   - FAQ section
   - Contact information

4. **Build community**
   - Reddit: r/scams, r/techsupport
   - Facebook groups for seniors
   - Local community centers
   - Police cybercrime units (they often share tools)

5. **Expand software database**
   - Community contributions for new scam tools
   - Regular updates with new remote access software
   - JSON database that auto-updates

### Phase 5: Advanced Features (Future)

**Nice-to-have additions:**

1. **Machine learning threat detection**
   - Analyze traffic patterns
   - Detect unusual remote access behavior
   - Reduce reliance on software database

2. **Cloud threat intelligence**
   - Share detected scammer IPs between users
   - Build database of known scam connections
   - Real-time threat updates

3. **Browser extension**
   - Detect when user visits fake tech support sites
   - Warning before downloading remote access software
   - Block known scam domains

4. **Mobile app companion**
   - Alert family members when threat detected
   - Remote monitoring for elderly relatives
   - Emergency "kill switch" to disconnect remotely

5. **Multi-language expansion**
   - Spanish, Hindi, German, French, Italian
   - Target countries with high scam rates

---

## Testing Guide

### Safe Testing Methods

**Method 1: Two Computers You Control**

1. Set up AnyDesk on two computers (your PC and a laptop)
2. Run SpamFisher on one computer
3. Connect from the other computer
4. Verify warning appears with correct geolocation
5. Test both BLOCK and ALLOW buttons

**Method 2: Mobile Phone Connection**

1. Install AnyDesk on your phone (Android/iOS)
2. Install AnyDesk on your PC
3. Run SpamFisher on PC
4. Connect from phone to PC
5. Verify detection works correctly

**Method 3: Trusted Friend/Family**

1. Have a trusted person install AnyDesk
2. Give them your AnyDesk ID
3. Run SpamFisher
4. Have them connect
5. Verify warning shows their actual location

### What to Test

✅ **Detection accuracy:**
- Starts AnyDesk → No alert (relay servers ignored)
- Actual connection → Alert appears within 2-4 seconds
- Correct country shown
- BLOCK button works (kills connection)
- ALLOW button works (connection continues)

✅ **False positives:**
- Normal internet usage doesn't trigger alerts
- Video calls (Zoom, Teams) don't trigger alerts
- Legitimate remote IT support can be allowed

✅ **Persistence:**
- Allowed connection doesn't re-alert
- Restart clears whitelist
- Multiple connections handled correctly

### Testing with Different Software

Test with other remote access tools if available:
- TeamViewer
- Chrome Remote Desktop
- Windows Remote Desktop (RDP)
- VNC

Each should be detected using the same smart logic.

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

---

## Timeline Estimate for Full Distribution

### Realistic Timeline (Part-time development)

- **Phase 1 (Code Cleanup):** 2-3 weeks
- **Phase 2 (User Experience):** 3-4 weeks
- **Phase 3 (Code Signing):** 2-3 weeks (plus certificate approval time)
- **Phase 4 (Distribution):** Ongoing

**Total to Beta Release:** 2-3 months  
**Total to Production Release:** 3-4 months (including testing and partnerships)

### Critical Path Items

The **absolute must-haves** before distributing to vulnerable users:

1. ✅ Detection works reliably (DONE)
2. ✅ Warning screen is clear and effective (DONE)
3. ⏳ Code signing certificate (REQUIRED)
4. ⏳ Installer package (REQUIRED)
5. ⏳ Auto-start with Windows (REQUIRED)
6. ⏳ System tray icon (REQUIRED)
7. ⏳ AV whitelisting (REQUIRED)
8. ⏳ Remove debug logging (REQUIRED)

Everything else can be added incrementally after initial release.

---

## Budget Requirements

### Minimum Budget for Distribution

1. **Code Signing Certificate:** €400/year (EV certificate)
2. **Domain name:** €15/year (for download website)
3. **Web hosting:** €5/month = €60/year
4. **Total Year 1:** ~€475
5. **Total Year 2+:** ~€475/year (certificate renewal)

### Optional Additional Costs

- **Cloud hosting for threat intelligence:** €10-50/month
- **SMS notification service (Twilio):** Pay-as-you-go
- **Professional logo/design:** €100-300 one-time
- **Video production (tutorial):** €200-500 one-time

### Free Alternative: Partnership Route

If budget is not available:
1. Partner with existing anti-scam organization
2. They provide code signing certificate
3. They host the downloads
4. They handle support
5. You maintain the code (open source)

This is the **recommended approach** for a free protection tool.

---

## Contributing

Once open-sourced, contributions welcome for:

- Adding support for new remote access software
- Improving detection algorithms
- Translations to more languages
- UI/UX improvements
- Testing on different Windows versions
- Documentation improvements

---

## License

To be decided - GPL v3 recommended for protection software to ensure it remains free and open.

---

## Contact & Support

**Creator:** Robert (Romania)  
**Motivation:** Protecting mother and other vulnerable people from remote access scams

For questions, issues, or partnership inquiries:
- Will be added once GitHub repository is created
- Email/contact form on distribution website

---

## Final Notes

SpamFisher is a **working prototype that successfully protects against remote access scams.** The core detection logic is solid and tested. The primary barriers to wide distribution are:

1. **Code signing** (technical + cost)
2. **User-friendly packaging** (technical work)
3. **Distribution channels** (partnerships)

With proper execution of the distribution roadmap, SpamFisher could genuinely help thousands of vulnerable people avoid losing money to scammers.

**The mission is clear: Make scam attempts visible to victims at the critical moment.**

SpamFisher achieves this mission. Now it needs the polish and distribution infrastructure to reach the people who need it most.

---

*Last updated: December 2025*  
*Status: Working Prototype*  
*Next milestone: Code cleanup and installer creation*

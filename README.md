# SpamFisher

**Protect vulnerable users from remote access scams**

SpamFisher detects when scammers establish remote connections to your computer and automatically blocks them with a full-screen warning.

## What It Does

- Monitors for remote access software (AnyDesk, TeamViewer, etc.)
- Detects when external connections are established
- Immediately blocks the connection
- Shows full-screen warning explaining the scam
- Gives user choice to block or allow (for legitimate support)

## Who It's For

- Elderly family members vulnerable to tech support scams
- Non-technical users who might fall for fake support calls
- Anyone who wants protection from remote access fraud

## How Scams Work

1. Victim receives fake email/pop-up about virus or security issue
2. Scammer directs them to call "support" or visit fake website
3. Scammer convinces them to install remote access software
4. Once connected, scammer steals banking credentials and money

**SpamFisher breaks this chain by detecting and blocking the remote connection.**

## Features

 Zero configuration - works immediately after install  
 Automatic blocking at moment of connection  
 Educational warnings teach users to recognize scams  
 Geolocation shows attacker's country  
 Open source and free  

## Status

**Currently in development** - Python prototype phase

## Technical Details

- **Language**: Python 3.x
- **Platform**: Windows 10/11
- **Detection**: Process monitoring + network connection analysis
- **Action**: Process termination + Windows Firewall blocking

## Installation

*Coming soon - prototype testing phase*

## License

Open source - GPL v3 (to be confirmed)

## Contributing

This project aims to help protect vulnerable people from financial fraud. Contributions welcome once prototype is complete.

## Contact

Created by Robert - protecting one mother at a time, then everyone else.

---

*"The best defense against scammers is making their tactics visible to their victims."*

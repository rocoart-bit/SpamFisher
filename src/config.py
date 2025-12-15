"""
SpamFisher Configuration
Database of known remote access software and their characteristics
"""

# Known remote access software to monitor
REMOTE_ACCESS_SOFTWARE = {
    'anydesk': {
        'process_names': ['AnyDesk.exe', 'anydesk.exe'],
        'ports': [6568, 7070, 80, 443],
        'display_name': 'AnyDesk'
    },
    'teamviewer': {
        'process_names': ['TeamViewer.exe', 'teamviewer.exe', 'TeamViewer_Service.exe'],
        'ports': [5938, 443],
        'display_name': 'TeamViewer'
    },
    'ultraviewer': {
        'process_names': ['UltraViewer_Desktop.exe', 'UltraViewer_Service.exe'],
        'ports': [443],
        'display_name': 'UltraViewer'
    },
    'supremo': {
        'process_names': ['Supremo.exe', 'SupremoService.exe'],
        'ports': [8099, 443],
        'display_name': 'SupRemo'
    },
    'chrome_remote': {
        'process_names': ['remoting_host.exe'],
        'ports': [443],
        'display_name': 'Chrome Remote Desktop'
    },
    'vnc': {
        'process_names': ['vncviewer.exe', 'winvnc.exe', 'tvnserver.exe'],
        'ports': [5900, 5901, 5902, 5903],
        'display_name': 'VNC'
    },
    'rdp': {
        'process_names': ['mstsc.exe'],
        'ports': [3389],
        'display_name': 'Remote Desktop'
    }
}

# Warning messages in different languages
WARNING_MESSAGES = {
    'en': {
        'title': '⚠️ REMOTE ACCESS DETECTED',
        'connection_from': 'Connection from: {country}',
        'how_scam_works': 'HOW THIS SCAM WORKS:',
        'step1': '1. You get a fake email or pop-up warning about a virus or problem',
        'step2': '2. They tell you to call a "support" number or visit a fake website',
        'step3': '3. They convince you to install remote access software',
        'step4': '4. Once connected, they steal your banking passwords and money',
        'warning1': 'Real tech support will NEVER ask you to install remote control software.',
        'warning2': 'If someone called YOU about a computer problem, it is 100% a scam.',
        'advice': 'Not sure? Call a family member or friend you trust before allowing.',
        'block_button': 'BLOCK THIS CONNECTION',
        'allow_button': 'I trust this - Allow'
    },
    'ro': {
        'title': '⚠️ ACCES LA DISTANȚĂ DETECTAT',
        'connection_from': 'Conexiune din: {country}',
        'how_scam_works': 'CUM FUNCȚIONEAZĂ ACEASTĂ ÎNȘELĂTORIE:',
        'step1': '1. Primiți un email fals sau fereastră pop-up despre un virus',
        'step2': '2. Vă spun să sunați la un număr de "suport" sau să vizitați un site fals',
        'step3': '3. Vă convinge să instalați software de acces la distanță',
        'step4': '4. Odată conectați, vă fură parolele bancare și banii',
        'warning1': 'Suportul tehnic real nu vă va cere NICIODATĂ să instalați software de control la distanță.',
        'warning2': 'Dacă cineva v-a sunat DESPRE o problemă cu computerul, este 100% înșelătorie.',
        'advice': 'Nu sunteți sigur? Sunați un membru al familiei sau prieten de încredere înainte de a permite.',
        'block_button': 'BLOCHEAZĂ CONEXIUNEA',
        'allow_button': 'Am încredere - Permite'
    }
}

# Settings
SETTINGS = {
    'default_language': 'en',  # Can be changed to 'ro' for Romanian
    'check_interval': 2,  # Seconds between checks
    'log_events': True,
    'log_file': 'spamfisher.log'
}

# Geolocation API (free tier)
GEOLOCATION_API = 'http://ip-api.com/json/{ip}'

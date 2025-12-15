"""
SpamFisher - Main Application
Combines monitoring and UI to protect against remote access scams
SECURITY ENHANCED VERSION
"""

import time
import threading
import os
import sys
import signal
from monitor import ConnectionMonitor
from ui import WarningScreen
from config import SETTINGS
from security import (
    request_admin_rights, 
    verify_integrity, 
    SecureWhitelist,
    SecureBlocklist,
    is_admin
)
import pystray
from PIL import Image, ImageDraw


class SpamFisher:
    """Main application controller with security features"""
    
    def __init__(self):
        # Security check
        if not verify_integrity():
            print("[SECURITY] Integrity check failed - some files may be compromised")
            response = input("Continue anyway? (yes/no): ")
            if response.lower() != 'yes':
                sys.exit(1)
        
        self.monitor = ConnectionMonitor()
        self.running = True
        self.warning_active = False
        self.allowed_pids = set()  # PIDs that user has allowed (temporary, session-only)
        self.alerted_connections = {}  # Track which connections we've already alerted on
        
        # Use encrypted whitelist
        self.secure_whitelist = SecureWhitelist()
        self.permanent_whitelist = self.secure_whitelist.load()
        self.clean_whitelist()  # Remove stale entries
        
        # Use encrypted blocklist
        self.secure_blocklist = SecureBlocklist()
        self.permanent_blocklist = self.secure_blocklist.load()
        
        self.tray_icon = None
        
        print(f"[DEBUG] SpamFisher initialized")
        print(f"[DEBUG] Admin rights: {'Yes' if is_admin() else 'No (limited protection)'}")
        print(f"[DEBUG] Permanent whitelist loaded: {len(self.permanent_whitelist)} entries")
        print(f"[DEBUG] Permanent blocklist loaded: {len(self.permanent_blocklist)} entries")
    
    def clean_whitelist(self):
        """Remove entries for processes that no longer exist"""
        import psutil
        cleaned = {}
        
        for key, value in self.permanent_whitelist.items():
            try:
                pid = value.get('pid')
                if pid and psutil.pid_exists(pid):
                    cleaned[key] = value
                else:
                    print(f"[DEBUG] Removing stale whitelist entry: {key}")
            except:
                pass
        
        if len(cleaned) != len(self.permanent_whitelist):
            self.permanent_whitelist = cleaned
            self.secure_whitelist.save(self.permanent_whitelist)
    
    def add_to_permanent_whitelist(self, threat_info):
        """Add connection to permanent whitelist"""
        key = f"{threat_info['software_name']}_{threat_info['remote_ip']}"
        
        self.permanent_whitelist[key] = {
            'software': threat_info['software_name'],
            'remote_ip': threat_info['remote_ip'],
            'country': threat_info['country'],
            'pid': threat_info['pid'],
            'process_name': threat_info['process_name'],
            'first_allowed': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.secure_whitelist.save(self.permanent_whitelist)
        print(f"[DEBUG] Added to permanent whitelist: {key}")
    
    def add_to_permanent_blocklist(self, threat_info):
        """Add connection to permanent blocklist"""
        key = f"{threat_info['software_name']}_{threat_info['remote_ip']}"
        
        self.permanent_blocklist[key] = {
            'software': threat_info['software_name'],
            'remote_ip': threat_info['remote_ip'],
            'country': threat_info['country'],
            'process_name': threat_info['process_name'],
            'blocked_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.secure_blocklist.save(self.permanent_blocklist)
        print(f"[DEBUG] Added to permanent blocklist: {key}")
    
    def is_whitelisted(self, threat_info):
        """Check if connection is in permanent whitelist"""
        key = f"{threat_info['software_name']}_{threat_info['remote_ip']}"
        return key in self.permanent_whitelist
    
    def is_blocklisted(self, threat_info):
        """Check if connection is in permanent blocklist"""
        key = f"{threat_info['software_name']}_{threat_info['remote_ip']}"
        return key in self.permanent_blocklist
        
    def create_tray_icon(self):
        """Create a simple system tray icon"""
        # Create a fisherman icon
        def create_image():
            # Create a 64x64 image
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), (46, 125, 50))  # Green background
            draw = ImageDraw.Draw(image)
            
            # Draw fisherman silhouette in white
            # Head (circle)
            draw.ellipse([26, 10, 38, 22], fill='white')
            
            # Body (rectangle)
            draw.rectangle([28, 22, 36, 38], fill='white')
            
            # Arms - left arm holding fishing rod
            draw.line([28, 26, 18, 24], fill='white', width=3)
            
            # Fishing rod
            draw.line([18, 24, 12, 8], fill='#8B4513', width=2)  # Brown rod
            
            # Fishing line
            draw.line([12, 8, 45, 35], fill='white', width=1)
            
            # Hook at end of line
            draw.arc([43, 33, 47, 40], start=0, end=270, fill='white', width=2)
            
            # Legs
            draw.line([30, 38, 26, 50], fill='white', width=3)
            draw.line([34, 38, 38, 50], fill='white', width=3)
            
            # Water line at bottom (blue waves)
            draw.arc([0, 48, 20, 58], start=0, end=180, fill='#2196F3', width=2)
            draw.arc([18, 48, 38, 58], start=0, end=180, fill='#2196F3', width=2)
            draw.arc([36, 48, 56, 58], start=0, end=180, fill='#2196F3', width=2)
            draw.arc([54, 48, 74, 58], start=0, end=180, fill='#2196F3', width=2)
            
            return image
        
        # Create menu
        admin_status = "Admin rights: Yes ✓" if is_admin() else "Admin rights: No (limited protection)"
        
        menu = pystray.Menu(
            pystray.MenuItem('SpamFisher - Protecting...', lambda: None, enabled=False),
            pystray.MenuItem(admin_status, lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', self.exit_application)
        )
        
        # Create tray icon
        self.tray_icon = pystray.Icon(
            "SpamFisher",
            create_image(),
            "SpamFisher - Remote Access Protection Active",
            menu
        )
        
        return self.tray_icon
    
    def exit_application(self):
        """Exit the application"""
        print("\nShutting down SpamFisher...")
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
        
    def handle_block(self, threat_info):
        """User chose to block the connection"""
        print(f"Blocking connection from {threat_info['country']}...")
        
        # Kill the process and add firewall rule
        success = self.monitor.block_connection(
            threat_info['pid'],
            threat_info['process_name']
        )
        
        if success:
            print("✅ Connection blocked and firewalled successfully!")
            # Add to permanent blocklist
            self.add_to_permanent_blocklist(threat_info)
            print(f"✅ Added {threat_info['software_name']} from {threat_info['country']} to permanent blocklist")
        else:
            print("❌ Failed to block connection (may need admin rights)")
        
        self.warning_active = False
    
    def handle_allow(self, threat_info):
        """User chose to allow the connection"""
        print(f"User allowed connection from {threat_info['country']}")
        print("⚠️ Connection remains active - user accepted the risk")
        
        # Add to BOTH temporary and permanent whitelists
        # Temporary: for this session
        self.allowed_pids.add(threat_info['pid'])
        print(f"Added PID {threat_info['pid']} to session whitelist")
        
        # Permanent: saved to encrypted file, persists across restarts
        self.add_to_permanent_whitelist(threat_info)
        print(f"Added {threat_info['software_name']} from {threat_info['country']} to permanent whitelist")
        
        self.warning_active = False
    
    def monitoring_loop(self):
        """Background monitoring thread"""
        print("SpamFisher monitoring started...")
        print("Watching for remote access threats...")
        
        while self.running:
            # Skip if warning is already shown
            if self.warning_active:
                time.sleep(1)
                continue
            
            # Scan for threats
            threat = self.monitor.scan_for_threats()
            
            if threat:
                print(f"[DEBUG] Threat detected - checking whitelists and blocklists...")
                print(f"[DEBUG] Current allowed_pids: {self.allowed_pids}")
                print(f"[DEBUG] Current alerted_connections: {list(self.alerted_connections.keys())}")
                print(f"[DEBUG] Threat PID: {threat['pid']}")
                
                # Check blocklist FIRST - auto-block if previously blocked
                if self.is_blocklisted(threat):
                    print(f"[DEBUG] Connection is in permanent blocklist - auto-blocking")
                    print(f"🚨 BLOCKED: Previously blocked connection from {threat['country']} detected!")
                    # Auto-block without showing warning
                    self.monitor.block_connection(threat['pid'], threat['process_name'])
                    time.sleep(SETTINGS['check_interval'])
                    continue
                
                # Check permanent whitelist
                if self.is_whitelisted(threat):
                    print(f"[DEBUG] Skipping alert - connection is in permanent whitelist")
                    time.sleep(SETTINGS['check_interval'])
                    continue
                
                # Skip if user already allowed this PID in this session
                if threat['pid'] in self.allowed_pids:
                    print(f"[DEBUG] Skipping alert - PID {threat['pid']} was previously allowed in this session")
                    time.sleep(SETTINGS['check_interval'])
                    continue
                
                # Create a unique key for this connection
                connection_key = f"{threat['pid']}_{threat['remote_ip']}"
                print(f"[DEBUG] Connection key: {connection_key}")
                
                # Skip if we've already alerted on this exact connection
                if connection_key in self.alerted_connections:
                    print(f"[DEBUG] Skipping alert - already alerted on this connection")
                    time.sleep(SETTINGS['check_interval'])
                    continue
                
                print(f"\n🚨 THREAT DETECTED!")
                print(f"Software: {threat['software_name']}")
                print(f"Remote IP: {threat['remote_ip']}")
                print(f"Country: {threat['country']}")
                
                # Mark this connection as alerted
                self.alerted_connections[connection_key] = True
                
                # Show warning screen
                self.warning_active = True
                self.show_warning(threat)
            
            time.sleep(SETTINGS['check_interval'])
    
    def show_warning(self, threat_info):
        """Display warning in main thread"""
        # Create and show warning in a way that doesn't block monitoring
        import threading
        
        def show_warning_thread():
            warning = WarningScreen(
                threat_info,
                self.handle_block,
                self.handle_allow
            )
            warning.show()
        
        # Show warning in separate thread so monitoring can continue
        warning_thread = threading.Thread(target=show_warning_thread)
        warning_thread.start()
    
    def run(self):
        """Start the application"""
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        monitor_thread.start()
        
        # Create tray icon
        icon = self.create_tray_icon()
        
        print("=" * 50)
        print("SpamFisher is now running in system tray")
        print("Right-click the tray icon to exit")
        print("Or press Ctrl+C in this window to stop")
        print("=" * 50)
        
        # Run tray icon in a thread so we can handle Ctrl+C
        import signal
        
        def run_tray():
            icon.run()
        
        tray_thread = threading.Thread(target=run_tray, daemon=True)
        tray_thread.start()
        
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            print("\n[SpamFisher] Ctrl+C detected, shutting down...")
            self.running = False
            if self.tray_icon:
                self.tray_icon.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Keep main thread alive and responsive to Ctrl+C
        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n[SpamFisher] Keyboard interrupt, shutting down...")
            self.running = False
            if self.tray_icon:
                self.tray_icon.stop()


def main():
    """Entry point"""
    print("=" * 50)
    print("SpamFisher - Remote Access Scam Protection")
    print("SECURITY ENHANCED VERSION")
    print("=" * 50)
    print()
    
    # Request admin rights for full protection
    if not is_admin():
        print("[SECURITY] Administrator rights required for full protection")
        print("[SECURITY] - Process termination: Available without admin")
        print("[SECURITY] - Firewall blocking: Requires admin (prevents restart)")
        print()
        response = input("Request admin rights now? (yes/no): ")
        if response.lower() == 'yes':
            request_admin_rights()
        else:
            print("[SECURITY] Running with limited protection (no firewall blocking)")
            print()
    
    app = SpamFisher()
    app.run()


if __name__ == '__main__':
    main()

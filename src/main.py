"""
SpamFisher - Main Application
Combines monitoring and UI to protect against remote access scams
"""

import time
import threading
import json
import os
from monitor import ConnectionMonitor
from ui import WarningScreen
from config import SETTINGS
import pystray
from PIL import Image, ImageDraw


class SpamFisher:
    """Main application controller"""
    
    def __init__(self):
        self.monitor = ConnectionMonitor()
        self.running = True
        self.warning_active = False
        self.allowed_pids = set()  # PIDs that user has allowed (temporary, session-only)
        self.alerted_connections = {}  # Track which connections we've already alerted on
        self.whitelist_file = 'whitelist.json'  # Persistent whitelist storage
        self.permanent_whitelist = self.load_whitelist()  # Load saved whitelist
        self.tray_icon = None
        print(f"[DEBUG] SpamFisher initialized - whitelist empty: {len(self.allowed_pids) == 0}")
        print(f"[DEBUG] Permanent whitelist loaded: {len(self.permanent_whitelist)} entries")
    
    def load_whitelist(self):
        """Load permanent whitelist from JSON file"""
        try:
            if os.path.exists(self.whitelist_file):
                with open(self.whitelist_file, 'r') as f:
                    data = json.load(f)
                    # Clean up entries for PIDs that no longer exist
                    cleaned_data = self.clean_whitelist(data)
                    return cleaned_data
        except Exception as e:
            print(f"[DEBUG] Error loading whitelist: {e}")
        
        return {}
    
    def clean_whitelist(self, whitelist):
        """Remove entries for processes that no longer exist"""
        import psutil
        cleaned = {}
        
        for key, value in whitelist.items():
            # Check if process still exists
            try:
                pid = value.get('pid')
                if pid and psutil.pid_exists(pid):
                    # Process still exists, keep it
                    cleaned[key] = value
                else:
                    print(f"[DEBUG] Removing stale whitelist entry: {key} (PID {pid} no longer exists)")
            except:
                # If there's any error checking, skip this entry
                pass
        
        return cleaned
    
    def save_whitelist(self):
        """Save permanent whitelist to JSON file"""
        try:
            with open(self.whitelist_file, 'w') as f:
                json.dump(self.permanent_whitelist, f, indent=2)
            print(f"[DEBUG] Whitelist saved: {len(self.permanent_whitelist)} entries")
        except Exception as e:
            print(f"[DEBUG] Error saving whitelist: {e}")
    
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
        
        self.save_whitelist()
        print(f"[DEBUG] Added to permanent whitelist: {key}")
    
    def is_whitelisted(self, threat_info):
        """Check if connection is in permanent whitelist"""
        key = f"{threat_info['software_name']}_{threat_info['remote_ip']}"
        return key in self.permanent_whitelist
        
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
        menu = pystray.Menu(
            pystray.MenuItem('SpamFisher - Protecting...', lambda: None, enabled=False),
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
        
        # Kill the process and block it
        success = self.monitor.block_connection(
            threat_info['pid'],
            threat_info['process_name']
        )
        
        if success:
            print("✅ Connection blocked successfully!")
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
        
        # Permanent: saved to file, persists across restarts
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
                print(f"[DEBUG] Threat detected - checking whitelists...")
                print(f"[DEBUG] Current allowed_pids: {self.allowed_pids}")
                print(f"[DEBUG] Current alerted_connections: {list(self.alerted_connections.keys())}")
                print(f"[DEBUG] Threat PID: {threat['pid']}")
                
                # Check permanent whitelist FIRST
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
        warning = WarningScreen(
            threat_info,
            self.handle_block,
            self.handle_allow
        )
        warning.show()
    
    def run(self):
        """Start the application"""
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        monitor_thread.start()
        
        # Create and run system tray icon
        icon = self.create_tray_icon()
        
        print("=" * 50)
        print("SpamFisher is now running in system tray")
        print("Right-click the tray icon to exit")
        print("=" * 50)
        
        # Run the tray icon (this blocks until icon is stopped)
        icon.run()


def main():
    """Entry point"""
    print("=" * 50)
    print("SpamFisher - Remote Access Scam Protection")
    print("=" * 50)
    print()
    
    app = SpamFisher()
    app.run()


if __name__ == '__main__':
    main()

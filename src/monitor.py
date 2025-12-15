"""
SpamFisher Monitor
Detects remote access software and active external connections
"""

import psutil
import time
import logging
from typing import Optional, Dict, List
import requests
from config import REMOTE_ACCESS_SOFTWARE, SETTINGS, GEOLOCATION_API


class ConnectionMonitor:
    """Monitors for remote access software with active external connections"""
    
    def __init__(self):
        self.setup_logging()
        self.monitored_processes = []
        
    def setup_logging(self):
        """Setup logging if enabled"""
        if SETTINGS['log_events']:
            logging.basicConfig(
                filename=SETTINGS['log_file'],
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
    
    def get_running_remote_software(self) -> List[Dict]:
        """Check if any known remote access software is running"""
        running_software = []
        
        for process in psutil.process_iter(['name', 'pid']):
            try:
                process_name = process.info['name']
                
                # Check against known remote access software
                for software_key, software_info in REMOTE_ACCESS_SOFTWARE.items():
                    if process_name in software_info['process_names']:
                        running_software.append({
                            'name': software_info['display_name'],
                            'process_name': process_name,
                            'pid': process.info['pid'],
                            'ports': software_info['ports']
                        })
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        return running_software
    
    def check_external_connections(self, pid: int, ports: List[int]) -> Optional[Dict]:
        """Check if process has active external connections (actual remote sessions, not just service connections)"""
        try:
            connections = psutil.net_connections(kind='inet')
            
            # First, find all ports this process is LISTENING on
            listening_ports = []
            for conn in connections:
                if conn.pid != pid:
                    continue
                if conn.status == 'LISTEN' and hasattr(conn, 'laddr'):
                    listening_ports.append(conn.laddr.port)
            
            print(f"\n[DEBUG] Checking PID {pid}, known ports: {ports}, listening ports: {listening_ports}")
            
            # Count established external connections for this process
            external_connections = []
            
            for conn in connections:
                # Check if connection belongs to our process
                if conn.pid != pid:
                    continue
                
                # DEBUG: Found a connection for our process
                print(f"[DEBUG] Found connection: Status={conn.status}, Local={conn.laddr}, Remote={getattr(conn, 'raddr', 'None')}")
                    
                # Check if it's an established connection
                if conn.status != 'ESTABLISHED':
                    continue
                
                # Check if remote address exists (some connections might not have it)
                if not hasattr(conn, 'raddr') or not conn.raddr:
                    print(f"[DEBUG] Skipping - no remote address")
                    continue
                
                # Check if it's an external connection (not local/LAN)
                remote_ip = conn.raddr.ip
                is_external = self.is_external_ip(remote_ip)
                print(f"[DEBUG] Remote IP: {remote_ip}, External: {is_external}")
                
                if is_external:
                    external_connections.append({
                        'remote_ip': remote_ip,
                        'remote_port': conn.raddr.port,
                        'local_port': conn.laddr.port
                    })
                    print(f"[DEBUG] Added to external connections: Local port {conn.laddr.port}, Remote port {conn.raddr.port}")
            
            print(f"[DEBUG] Total external connections: {len(external_connections)}")
            
            # PRIORITY 1: Check for INCOMING connections on known remote desktop ports
            incoming_connections = []
            for conn in external_connections:
                if conn['local_port'] in ports:
                    incoming_connections.append(conn)
                    print(f"[DEBUG] Found INCOMING connection on KNOWN port {conn['local_port']} from {conn['remote_ip']}")
            
            if incoming_connections:
                print(f"[DEBUG] ALERT: Incoming connection on known port detected - triggering warning")
                return incoming_connections[0]
            
            # PRIORITY 2: Check for incoming connections on LISTENING ports (dynamic ports)
            # If the process is listening on a port AND has an external connection on that port = active session
            # BUT filter out relay server connections (port 443)
            for conn in external_connections:
                if conn['local_port'] in listening_ports:
                    # Skip if remote is using port 443 (likely a relay server, not actual user)
                    if conn['remote_port'] == 443:
                        print(f"[DEBUG] Skipping connection on port 443 - likely relay server: {conn['remote_ip']}")
                        continue
                    
                    print(f"[DEBUG] Found INCOMING connection on LISTENING port {conn['local_port']} from {conn['remote_ip']}")
                    incoming_connections.append(conn)
            
            if incoming_connections:
                print(f"[DEBUG] ALERT: Incoming connection on listening port detected - triggering warning")
                return incoming_connections[0]
            
            # PRIORITY 3: Check for connections using remote desktop ports on the REMOTE side
            # But ONLY if we have 3+ connections (to avoid relay server false positives)
            if len(external_connections) >= 3:
                for conn in external_connections:
                    if conn['remote_port'] in ports:
                        print(f"[DEBUG] ALERT: Multiple connections with remote desktop port usage - triggering warning")
                        return conn
            
            print(f"[DEBUG] No threat detected - connections appear to be relay/service connections")
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
        return None
    
    def is_external_ip(self, ip: str) -> bool:
        """Check if IP is external (not local network)"""
        # Skip localhost
        if ip.startswith('127.'):
            return False
        
        # Skip local network ranges
        local_ranges = [
            '10.',
            '172.16.', '172.17.', '172.18.', '172.19.',
            '172.20.', '172.21.', '172.22.', '172.23.',
            '172.24.', '172.25.', '172.26.', '172.27.',
            '172.28.', '172.29.', '172.30.', '172.31.',
            '192.168.'
        ]
        
        for local_range in local_ranges:
            if ip.startswith(local_range):
                return False
                
        return True
    
    def get_ip_geolocation(self, ip: str) -> str:
        """Get country for IP address using HTTPS with multiple fallbacks"""
        
        # Try multiple services in order
        services = [
            {
                'url': f'https://ipapi.co/{ip}/json/',
                'key': 'country_name',
                'name': 'ipapi.co'
            },
            {
                'url': f'https://ip-api.com/json/{ip}',
                'key': 'country',
                'name': 'ip-api.com'
            },
            {
                'url': f'https://ipwho.is/{ip}',
                'key': 'country',
                'name': 'ipwho.is'
            }
        ]
        
        for service in services:
            try:
                print(f"[DEBUG] Trying geolocation service: {service['name']}")
                response = requests.get(service['url'], timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[DEBUG] Response from {service['name']}: {data}")
                    
                    country = data.get(service['key'], None)
                    if country:
                        print(f"[DEBUG] Got country from {service['name']}: {country}")
                        return country
                else:
                    print(f"[DEBUG] {service['name']} returned status {response.status_code}")
                    
            except Exception as e:
                print(f"[DEBUG] {service['name']} error: {e}")
                continue
        
        print(f"[DEBUG] All geolocation services failed, returning Unknown")
        return 'Unknown'
    
    def scan_for_threats(self) -> Optional[Dict]:
        """Main scanning function - returns threat info if detected"""
        running_software = self.get_running_remote_software()
        
        if not running_software:
            return None
        
        # Check each running remote access software for external connections
        for software in running_software:
            connection = self.check_external_connections(
                software['pid'], 
                software['ports']
            )
            
            if connection:
                # Threat detected!
                country = self.get_ip_geolocation(connection['remote_ip'])
                
                threat_info = {
                    'software_name': software['name'],
                    'process_name': software['process_name'],
                    'pid': software['pid'],
                    'remote_ip': connection['remote_ip'],
                    'remote_port': connection['remote_port'],
                    'country': country
                }
                
                if SETTINGS['log_events']:
                    logging.warning(f"Threat detected: {threat_info}")
                
                return threat_info
        
        return None
    
    def block_connection(self, pid: int, process_name: str) -> bool:
        """Block the connection by killing process tree and adding firewall rule"""
        try:
            from security import kill_process_tree, get_process_executable_path, add_firewall_block
            
            # Get executable path before killing process
            executable_path = get_process_executable_path(pid)
            
            # Kill the process and all children
            success = kill_process_tree(pid)
            
            if not success:
                if SETTINGS['log_events']:
                    logging.error(f"Failed to kill process tree for PID {pid}")
                return False
            
            # Add firewall rule to prevent restart
            if executable_path:
                firewall_success = add_firewall_block(executable_path, process_name)
                if firewall_success:
                    if SETTINGS['log_events']:
                        logging.info(f"Blocked and firewalled: {process_name} (PID: {pid})")
                else:
                    if SETTINGS['log_events']:
                        logging.warning(f"Killed process but firewall block failed: {process_name}")
            
            return True
            
        except Exception as e:
            if SETTINGS['log_events']:
                logging.error(f"Failed to block connection: {e}")
            return False


def main():
    """Testing function"""
    print("SpamFisher Monitor - Testing mode")
    print("Scanning for remote access software...")
    
    monitor = ConnectionMonitor()
    
    while True:
        threat = monitor.scan_for_threats()
        
        if threat:
            print(f"\n🚨 THREAT DETECTED!")
            print(f"Software: {threat['software_name']}")
            print(f"Remote IP: {threat['remote_ip']}")
            print(f"Country: {threat['country']}")
            print("\nIn production, full-screen warning would appear here.")
            break
        else:
            print(".", end="", flush=True)
            
        time.sleep(SETTINGS['check_interval'])


if __name__ == '__main__':
    main()

"""
SpamFisher Security Module
Handles admin rights, firewall blocking, and whitelist encryption
"""

import ctypes
import sys
import subprocess
import os
from cryptography.fernet import Fernet
import json


def is_admin():
    """Check if running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def request_admin_rights():
    """Request administrator privileges if not already running as admin"""
    if not is_admin():
        print("SpamFisher requires administrator privileges for full protection.")
        print("Requesting elevation...")
        
        try:
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                " ".join(sys.argv), 
                None, 
                1
            )
        except Exception as e:
            print(f"Failed to obtain admin rights: {e}")
            print("SpamFisher will run with limited protection.")
            return False
        
        # Exit this non-admin instance
        sys.exit()
    
    return True


def add_firewall_block(executable_path, process_name):
    """
    Add Windows Firewall rule to block an executable
    Requires administrator privileges
    """
    if not is_admin():
        print("[SECURITY] Cannot add firewall rule - not running as admin")
        return False
    
    try:
        rule_name = f"SpamFisher_Block_{process_name}"
        
        # Remove existing rule if present
        subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'delete', 'rule', 
             f'name={rule_name}'],
            capture_output=True,
            check=False  # Don't raise error if rule doesn't exist
        )
        
        # Add new blocking rule (inbound)
        result_in = subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'add', 'rule',
             f'name={rule_name}_IN',
             'dir=in',
             'action=block',
             f'program={executable_path}',
             'enable=yes'],
            capture_output=True,
            text=True
        )
        
        # Add new blocking rule (outbound)
        result_out = subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'add', 'rule',
             f'name={rule_name}_OUT',
             'dir=out',
             'action=block',
             f'program={executable_path}',
             'enable=yes'],
            capture_output=True,
            text=True
        )
        
        if result_in.returncode == 0 and result_out.returncode == 0:
            print(f"[SECURITY] Firewall rules added for {process_name}")
            return True
        else:
            print(f"[SECURITY] Failed to add firewall rules:")
            print(f"  Inbound: {result_in.stderr}")
            print(f"  Outbound: {result_out.stderr}")
            return False
            
    except Exception as e:
        print(f"[SECURITY] Error adding firewall rule: {e}")
        return False


def get_process_executable_path(pid):
    """Get the full path to the executable for a given PID"""
    try:
        import psutil
        process = psutil.Process(pid)
        return process.exe()
    except Exception as e:
        print(f"[SECURITY] Could not get executable path for PID {pid}: {e}")
        return None


def kill_process_tree(pid):
    """
    Kill a process and all its child processes
    More thorough than just killing the main process
    """
    try:
        import psutil
        
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # Kill children first
        for child in children:
            try:
                print(f"[SECURITY] Terminating child process: {child.name()} (PID: {child.pid})")
                child.terminate()
            except:
                pass
        
        # Kill parent
        print(f"[SECURITY] Terminating parent process: {parent.name()} (PID: {pid})")
        parent.terminate()
        
        # Wait for termination
        gone, alive = psutil.wait_procs([parent] + children, timeout=3)
        
        # Force kill if still alive
        for p in alive:
            try:
                print(f"[SECURITY] Force killing: {p.name()} (PID: {p.pid})")
                p.kill()
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"[SECURITY] Error killing process tree: {e}")
        return False


class SecureBlocklist:
    """
    Handles encrypted storage of the blocklist (permanently blocked IPs)
    """
    
    def __init__(self, key_file='blocklist.key', data_file='blocklist.enc'):
        self.key_file = key_file
        self.data_file = data_file
        self.cipher = self._load_or_create_key()
    
    def _load_or_create_key(self):
        """Load existing encryption key or create new one"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                print("[SECURITY] Generated new encryption key for blocklist")
            
            return Fernet(key)
        except Exception as e:
            print(f"[SECURITY] Error with encryption key: {e}")
            # Fall back to unencrypted if encryption fails
            return None
    
    def save(self, data):
        """Save blocklist data (encrypted)"""
        try:
            if self.cipher is None:
                # Fall back to unencrypted JSON
                with open(self.data_file.replace('.enc', '.json'), 'w') as f:
                    json.dump(data, f, indent=2)
                return
            
            # Encrypt and save
            json_data = json.dumps(data)
            encrypted = self.cipher.encrypt(json_data.encode())
            
            with open(self.data_file, 'wb') as f:
                f.write(encrypted)
            
            print("[SECURITY] Blocklist saved (encrypted)")
            
        except Exception as e:
            print(f"[SECURITY] Error saving encrypted blocklist: {e}")
    
    def load(self):
        """Load blocklist data (decrypt)"""
        try:
            if self.cipher is None:
                # Try loading unencrypted JSON
                json_file = self.data_file.replace('.enc', '.json')
                if os.path.exists(json_file):
                    with open(json_file, 'r') as f:
                        return json.load(f)
                return {}
            
            if not os.path.exists(self.data_file):
                return {}
            
            # Decrypt and load
            with open(self.data_file, 'rb') as f:
                encrypted = f.read()
            
            decrypted = self.cipher.decrypt(encrypted)
            data = json.loads(decrypted.decode())
            
            # Validate structure
            if not isinstance(data, dict):
                raise ValueError("Invalid blocklist format")
            
            # Validate each entry
            for key, value in data.items():
                if not isinstance(value, dict):
                    raise ValueError(f"Invalid entry format: {key}")
                
                required_keys = ['software', 'remote_ip', 'country']
                if not all(k in value for k in required_keys):
                    raise ValueError(f"Missing required fields in entry: {key}")
            
            print(f"[SECURITY] Blocklist loaded (encrypted): {len(data)} entries")
            return data
            
        except Exception as e:
            print(f"[SECURITY] Error loading encrypted blocklist: {e}")
            return {}


class SecureWhitelist:
    """
    Handles encrypted storage of the whitelist
    """
    
    def __init__(self, key_file='whitelist.key', data_file='whitelist.enc'):
        self.key_file = key_file
        self.data_file = data_file
        self.cipher = self._load_or_create_key()
    
    def _load_or_create_key(self):
        """Load existing encryption key or create new one"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                print("[SECURITY] Generated new encryption key for whitelist")
            
            return Fernet(key)
        except Exception as e:
            print(f"[SECURITY] Error with encryption key: {e}")
            # Fall back to unencrypted if encryption fails
            return None
    
    def save(self, data):
        """Save whitelist data (encrypted)"""
        try:
            if self.cipher is None:
                # Fall back to unencrypted JSON
                with open(self.data_file.replace('.enc', '.json'), 'w') as f:
                    json.dump(data, f, indent=2)
                return
            
            # Encrypt and save
            json_data = json.dumps(data)
            encrypted = self.cipher.encrypt(json_data.encode())
            
            with open(self.data_file, 'wb') as f:
                f.write(encrypted)
            
            print("[SECURITY] Whitelist saved (encrypted)")
            
        except Exception as e:
            print(f"[SECURITY] Error saving encrypted whitelist: {e}")
    
    def load(self):
        """Load whitelist data (decrypt)"""
        try:
            if self.cipher is None:
                # Try loading unencrypted JSON
                json_file = self.data_file.replace('.enc', '.json')
                if os.path.exists(json_file):
                    with open(json_file, 'r') as f:
                        return json.load(f)
                return {}
            
            if not os.path.exists(self.data_file):
                return {}
            
            # Decrypt and load
            with open(self.data_file, 'rb') as f:
                encrypted = f.read()
            
            decrypted = self.cipher.decrypt(encrypted)
            data = json.loads(decrypted.decode())
            
            # Validate structure
            if not isinstance(data, dict):
                raise ValueError("Invalid whitelist format")
            
            # Validate each entry
            for key, value in data.items():
                if not isinstance(value, dict):
                    raise ValueError(f"Invalid entry format: {key}")
                
                required_keys = ['software', 'remote_ip', 'pid']
                if not all(k in value for k in required_keys):
                    raise ValueError(f"Missing required fields in entry: {key}")
            
            print(f"[SECURITY] Whitelist loaded (encrypted): {len(data)} entries")
            return data
            
        except Exception as e:
            print(f"[SECURITY] Error loading encrypted whitelist: {e}")
            return {}


def verify_integrity():
    """
    Basic self-integrity check
    In production, this would hash critical files and verify signatures
    """
    critical_files = [
        'main.py',
        'monitor.py',
        'ui.py',
        'config.py',
        'security.py'
    ]
    
    missing_files = []
    for file in critical_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"[SECURITY] WARNING: Critical files missing: {missing_files}")
        return False
    
    print("[SECURITY] Integrity check passed")
    return True

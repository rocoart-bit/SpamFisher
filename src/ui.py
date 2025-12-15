"""
SpamFisher Warning UI
Full-screen warning interface shown when threat is detected
"""

import tkinter as tk
from tkinter import font
from typing import Callable, Dict
from config import WARNING_MESSAGES, SETTINGS


class WarningScreen:
    """Full-screen warning overlay"""
    
    def __init__(self, threat_info: Dict, on_block: Callable, on_allow: Callable):
        self.threat_info = threat_info
        self.on_block = on_block
        self.on_allow = on_allow
        self.language = SETTINGS['default_language']
        self.root = None
        
    def show(self):
        """Display the full-screen warning"""
        self.root = tk.Tk()
        
        # Make it full-screen and topmost
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#1a1a1a')
        
        # Prevent closing with Alt+F4
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Get messages for current language
        messages = WARNING_MESSAGES[self.language]
        
        # Main container
        container = tk.Frame(self.root, bg='#1a1a1a')
        container.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_font = font.Font(family='Arial', size=32, weight='bold')
        title = tk.Label(
            container,
            text=messages['title'],
            font=title_font,
            bg='#1a1a1a',
            fg='#ff4444',
            pady=20
        )
        title.pack()
        
        # Connection info
        info_font = font.Font(family='Arial', size=18, weight='bold')
        connection_info = tk.Label(
            container,
            text=messages['connection_from'].format(country=self.threat_info['country']),
            font=info_font,
            bg='#1a1a1a',
            fg='#ffaa00',
            pady=10
        )
        connection_info.pack()
        
        # Separator
        separator = tk.Frame(container, bg='#444444', height=2)
        separator.pack(fill='x', padx=50, pady=20)
        
        # How scam works section
        scam_font = font.Font(family='Arial', size=16, weight='bold')
        scam_title = tk.Label(
            container,
            text=messages['how_scam_works'],
            font=scam_font,
            bg='#1a1a1a',
            fg='#ffffff',
            pady=10
        )
        scam_title.pack()
        
        # Steps
        steps_font = font.Font(family='Arial', size=14)
        steps_text = f"{messages['step1']}\n\n{messages['step2']}\n\n{messages['step3']}\n\n{messages['step4']}"
        steps = tk.Label(
            container,
            text=steps_text,
            font=steps_font,
            bg='#1a1a1a',
            fg='#cccccc',
            justify='left',
            pady=10
        )
        steps.pack()
        
        # Warnings
        warning_font = font.Font(family='Arial', size=15, weight='bold')
        warning1 = tk.Label(
            container,
            text=messages['warning1'],
            font=warning_font,
            bg='#1a1a1a',
            fg='#ff6666',
            pady=10,
            wraplength=800
        )
        warning1.pack()
        
        warning2 = tk.Label(
            container,
            text=messages['warning2'],
            font=warning_font,
            bg='#1a1a1a',
            fg='#ff6666',
            pady=5,
            wraplength=800
        )
        warning2.pack()
        
        # Separator
        separator2 = tk.Frame(container, bg='#444444', height=2)
        separator2.pack(fill='x', padx=50, pady=20)
        
        # Buttons frame
        buttons_frame = tk.Frame(container, bg='#1a1a1a')
        buttons_frame.pack(pady=20)
        
        # Block button (large and prominent)
        button_font = font.Font(family='Arial', size=20, weight='bold')
        block_btn = tk.Button(
            buttons_frame,
            text=messages['block_button'],
            font=button_font,
            bg='#ff4444',
            fg='#ffffff',
            activebackground='#cc0000',
            activeforeground='#ffffff',
            command=self.handle_block,
            padx=40,
            pady=20,
            cursor='hand2',
            relief='raised',
            bd=5
        )
        block_btn.pack(pady=10)
        
        # Allow button (smaller, less prominent)
        allow_font = font.Font(family='Arial', size=14)
        allow_btn = tk.Button(
            buttons_frame,
            text=messages['allow_button'],
            font=allow_font,
            bg='#333333',
            fg='#999999',
            activebackground='#444444',
            activeforeground='#ffffff',
            command=self.handle_allow,
            padx=20,
            pady=10,
            cursor='hand2',
            relief='flat'
        )
        allow_btn.pack(pady=10)
        
        # Advice
        advice_font = font.Font(family='Arial', size=13)
        advice = tk.Label(
            container,
            text=messages['advice'],
            font=advice_font,
            bg='#1a1a1a',
            fg='#888888',
            pady=20,
            wraplength=800
        )
        advice.pack()
        
        # Start the GUI
        self.root.mainloop()
    
    def handle_block(self):
        """User clicked BLOCK"""
        self.root.destroy()
        self.on_block(self.threat_info)
    
    def handle_allow(self):
        """User clicked ALLOW"""
        self.root.destroy()
        self.on_allow(self.threat_info)


def test_ui():
    """Test the warning UI"""
    threat_info = {
        'software_name': 'AnyDesk',
        'remote_ip': '192.168.1.100',
        'country': 'India',
        'pid': 1234
    }
    
    def on_block(info):
        print(f"User chose to BLOCK: {info}")
    
    def on_allow(info):
        print(f"User chose to ALLOW: {info}")
    
    warning = WarningScreen(threat_info, on_block, on_allow)
    warning.show()


if __name__ == '__main__':
    test_ui()

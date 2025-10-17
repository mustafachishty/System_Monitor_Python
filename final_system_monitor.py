import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import psutil
import datetime
import json
import os
import subprocess
import platform
import collections

class FinalSystemMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("System Monitor")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        self.cpu_history = collections.deque(maxlen=600)
        self.cpu_log_file = "cpu_history.json"
        self.last_shutdown = None
        
        self.setup_ui()
        self.load_cpu_history()
        self.get_shutdown_data()
        self.update_system_info()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        title_label = ttk.Label(main_frame, text="System Monitor", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # System Events
        boot_frame = ttk.LabelFrame(main_frame, text="System Events", padding="15")
        boot_frame.pack(fill='x', pady=(0, 15))
        
        self.boot_label = ttk.Label(boot_frame, text="Last Boot: Ready", font=("Arial", 10))
        self.boot_label.pack(anchor='w', pady=2)
        
        self.shutdown_label = ttk.Label(boot_frame, text="Last Shutdown: Ready", font=("Arial", 10))
        self.shutdown_label.pack(anchor='w', pady=2)
        
        self.uptime_label = ttk.Label(boot_frame, text="Uptime: Ready", font=("Arial", 10))
        self.uptime_label.pack(anchor='w', pady=2)
        
        # CPU Performance
        cpu_frame = ttk.LabelFrame(main_frame, text="CPU Performance", padding="15")
        cpu_frame.pack(fill='x', pady=(0, 15))
        
        self.current_cpu_label = ttk.Label(cpu_frame, text="Current CPU: Ready", font=("Arial", 12, "bold"))
        self.current_cpu_label.pack(anchor='w', pady=2)
        
        self.past_cpu_label = ttk.Label(cpu_frame, text="10 minutes ago: Ready", font=("Arial", 10))
        self.past_cpu_label.pack(anchor='w', pady=2)
        
        self.cpu_change_label = ttk.Label(cpu_frame, text="Change: Ready", font=("Arial", 10))
        self.cpu_change_label.pack(anchor='w', pady=2)
        
        # Network Status
        network_frame = ttk.LabelFrame(main_frame, text="Network Status", padding="15")
        network_frame.pack(fill='x', pady=(0, 15))
        
        self.network_label = ttk.Label(network_frame, text="Connection: Ready", font=("Arial", 10))
        self.network_label.pack(anchor='w', pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(15, 0))
        
        refresh_btn = ttk.Button(button_frame, text="Refresh All", command=self.refresh_all)
        refresh_btn.pack(side='left', padx=(0, 10))
        
        export_btn = ttk.Button(button_frame, text="Export Report", command=self.export_report)
        export_btn.pack(side='left')
        
        self.status_label = ttk.Label(main_frame, text="Status: Ready", font=("Arial", 9), foreground="green")
        self.status_label.pack(pady=(10, 0))
    
    def get_shutdown_data(self):
        """Get last shutdown time"""
        try:
            self.status_label.config(text="Status: Getting shutdown data...", foreground="blue")
            self.root.update()
            
            cmd = ["powershell", "-Command", 
                   "Get-WinEvent -FilterHashtable @{LogName='System'; ID=6006} -MaxEvents 1 | Select-Object TimeCreated -ExpandProperty TimeCreated"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0 and result.stdout.strip():
                time_str = result.stdout.strip()
                try:
                    dt = datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    self.last_shutdown = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    self.last_shutdown = time_str
            else:
                self.last_shutdown = "Not available"
                
        except:
            self.last_shutdown = "Not available"
    
    def get_wifi_ssid(self):
        """Get WiFi SSID"""
        try:
            cmd = ["netsh", "wlan", "show", "interfaces"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3, creationflags=subprocess.CREATE_NO_WINDOW)
            
            for line in result.stdout.splitlines():
                if "SSID" in line and ":" in line and "BSSID" not in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        ssid = parts[1].strip()
                        if ssid and ssid.lower() != "ssid":
                            return ssid
        except:
            pass
        return None
    
    def load_cpu_history(self):
        """Load CPU history"""
        try:
            if os.path.exists(self.cpu_log_file):
                with open(self.cpu_log_file, 'r') as f:
                    data = json.load(f)
                
                current_time = datetime.datetime.now()
                for entry in data.get("cpu_data", []):
                    entry_time = datetime.datetime.fromisoformat(entry["timestamp"])
                    if (current_time - entry_time).total_seconds() <= 600:
                        self.cpu_history.append(entry["cpu_percent"])
        except:
            pass
    
    def save_cpu_history(self):
        """Save CPU history"""
        try:
            current_time = datetime.datetime.now()
            cpu_data = []
            
            for i, cpu_val in enumerate(self.cpu_history):
                timestamp = current_time - datetime.timedelta(seconds=(len(self.cpu_history) - 1 - i))
                cpu_data.append({
                    "timestamp": timestamp.isoformat(),
                    "cpu_percent": cpu_val
                })
            
            data = {
                "last_updated": current_time.isoformat(),
                "cpu_data": cpu_data
            }
            
            with open(self.cpu_log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
    
    def update_system_info(self):
        """Update system information"""
        try:
            current_cpu = psutil.cpu_percent(interval=None)
            self.cpu_history.append(current_cpu)
            
            self.current_cpu_label.config(text=f"Current CPU: {current_cpu:.1f}%")
            
            if len(self.cpu_history) >= 600:
                past_cpu = self.cpu_history[0]
                change = current_cpu - past_cpu
                
                self.past_cpu_label.config(text=f"10 minutes ago: {past_cpu:.1f}%")
                
                if change > 5:
                    change_text = f"Change: +{change:.1f}% (Much Higher)"
                    color = "red"
                elif change > 0:
                    change_text = f"Change: +{change:.1f}% (Higher)"
                    color = "orange"
                elif change < -5:
                    change_text = f"Change: {change:.1f}% (Much Lower)"
                    color = "green"
                elif change < 0:
                    change_text = f"Change: {change:.1f}% (Lower)"
                    color = "blue"
                else:
                    change_text = "Change: Stable"
                    color = "black"
                
                self.cpu_change_label.config(text=change_text, foreground=color)
            else:
                remaining = 600 - len(self.cpu_history)
                self.past_cpu_label.config(text=f"Collecting data... ({remaining}s left)")
                self.cpu_change_label.config(text="Change: Please wait...")
            
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            self.boot_label.config(text=f"Last Boot: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            uptime = datetime.datetime.now() - boot_time
            uptime_str = str(uptime).split('.')[0]
            self.uptime_label.config(text=f"Uptime: {uptime_str}")
            
            if self.last_shutdown:
                self.shutdown_label.config(text=f"Last Shutdown: {self.last_shutdown}")
            
            wifi_ssid = self.get_wifi_ssid()
            if wifi_ssid:
                self.network_label.config(text=f"WiFi: {wifi_ssid}")
            else:
                self.network_label.config(text="Connection: Ethernet/No WiFi")
            
            if len(self.cpu_history) % 60 == 0:
                self.save_cpu_history()
            
        except Exception as e:
            self.status_label.config(text=f"Status: Error - {str(e)}", foreground="red")
        
        self.root.after(1000, self.update_system_info)
    
    def refresh_all(self):
        """Refresh all data"""
        self.status_label.config(text="Status: Refreshing all data...", foreground="blue")
        self.root.update()
        
        self.get_shutdown_data()
        
        self.status_label.config(text="Status: All data refreshed", foreground="green")
    
    def export_report(self):
        """Export system report to text file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save System Report"
            )
            
            if file_path:
                self.status_label.config(text="Status: Generating report...", foreground="blue")
                self.root.update()
                
                report = self.generate_report()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                self.status_label.config(text=f"Status: Report saved to {os.path.basename(file_path)}", foreground="green")
                messagebox.showinfo("Export Complete", f"System report saved to:\n{file_path}")
        
        except Exception as e:
            self.status_label.config(text=f"Status: Export failed - {str(e)}", foreground="red")
            messagebox.showerror("Export Error", f"Failed to export report:\n{str(e)}")
    
    def generate_report(self):
        """Generate system report"""
        current_time = datetime.datetime.now()
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = current_time - boot_time
        
        current_cpu = self.cpu_history[-1] if self.cpu_history else 0
        past_cpu = self.cpu_history[0] if len(self.cpu_history) >= 600 else None
        
        memory = psutil.virtual_memory()
        wifi_ssid = self.get_wifi_ssid()
        
        report = f"""SYSTEM MONITOR REPORT
Generated: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

SYSTEM EVENTS:
- Last Boot: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
- Last Shutdown: {self.last_shutdown or 'Not available'}
- Current Uptime: {str(uptime).split('.')[0]}

CPU PERFORMANCE:
- Current CPU Usage: {current_cpu:.1f}%"""

        if past_cpu is not None:
            change = current_cpu - past_cpu
            report += f"""
- CPU Usage 10 min ago: {past_cpu:.1f}%
- Change: {change:+.1f}%"""
        else:
            report += f"""
- CPU Usage 10 min ago: Still collecting data
- Change: Not available yet"""

        report += f"""

MEMORY INFORMATION:
- Total RAM: {memory.total / (1024**3):.2f} GB
- Used RAM: {memory.used / (1024**3):.2f} GB
- Available RAM: {memory.available / (1024**3):.2f} GB
- Memory Usage: {memory.percent:.1f}%

NETWORK STATUS:
- Connection Type: {'WiFi' if wifi_ssid else 'Ethernet/No WiFi'}"""

        if wifi_ssid:
            report += f"""
- WiFi Network: {wifi_ssid}"""

        report += f"""

SYSTEM INFORMATION:
- Hostname: {platform.node()}
- Operating System: {platform.system()} {platform.release()}
- Platform: {platform.platform()}
- Processor: {platform.processor()}
- CPU Cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical

DATA COLLECTION:
- CPU History Points: {len(self.cpu_history)}/600
- Monitoring Duration: {len(self.cpu_history)} seconds
- Report Generated By: System Monitor v1.0

{'='*50}
End of Report"""

        return report
    
    def on_closing(self):
        """Handle application closing"""
        self.save_cpu_history()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FinalSystemMonitor(root)
    root.mainloop()
#!/usr/bin/env python3
"""
Network Monitor MVP
A lightweight, cross-platform network monitoring tool.
"""
import os
import platform
import re
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from queue import Queue
from threading import Thread, Event
from typing import Dict, List, Optional, Tuple

import netifaces
import nmap
from rich.console import Console
from rich.live import Live
from rich.table import Table

# Constants
PING_COUNT = 1  # Number of pings per check
UPDATE_INTERVAL = 5  # Seconds between updates
TIMEOUT = 2  # Seconds to wait for ping response

@dataclass
class HostStatus:
    """Track status and statistics for a single host."""
    ip: str
    hostname: str = ""
    is_up: bool = False
    last_seen: Optional[datetime] = None
    response_times: List[float] = field(default_factory=list)
    packet_loss: int = 0
    total_checks: int = 0
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time in ms."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @property
    def packet_loss_percent(self) -> float:
        """Calculate packet loss percentage."""
        if self.total_checks == 0:
            return 0.0
        return (self.packet_loss / self.total_checks) * 100

class NetworkMonitor:
    """Main network monitoring class."""
    
    def __init__(self):
        self.console = Console()
        self.hosts: Dict[str, HostStatus] = {}
        self.running = Event()
        self.scan_thread: Optional[Thread] = None
        self.ui_thread: Optional[Thread] = None
        self.nm = nmap.PortScanner()
        
    def get_local_networks(self) -> List[str]:
        """Get list of local networks from available interfaces."""
        networks = []
        try:
            for iface in netifaces.interfaces():
                try:
                    addrs = netifaces.ifaddresses(iface)
                    if netifaces.AF_INET in addrs:
                        for addr in addrs[netifaces.AF_INET]:
                            try:
                                if 'addr' in addr and 'netmask' in addr:
                                    ip = addr['addr']
                                    netmask = addr['netmask']
                                    # Skip localhost and invalid addresses
                                    if (ip != '127.0.0.1' and 
                                        ip != '0.0.0.0' and 
                                        not ip.startswith('169.254.') and  # Link-local
                                        netmask != '255.255.255.255'):  # Skip point-to-point
                                        network = self.ip_to_network(ip, netmask)
                                        if network not in networks:  # Avoid duplicates
                                            networks.append(network)
                            except (KeyError, ValueError) as e:
                                self.console.print(f"[yellow]Warning: Could not process address on {iface}: {e}[/]")
                                continue
                except ValueError as e:
                    self.console.print(f"[yellow]Warning: Could not get addresses for {iface}: {e}[/]")
                    continue
        except Exception as e:
            self.console.print(f"[red]Error getting network interfaces: {e}[/]")
        
        # If no networks found, try a fallback method
        if not networks:
            self.console.print("[yellow]No networks found, trying fallback method...[/]")
            try:
                # Try to get the default gateway's network
                gateways = netifaces.gateways()
                if 'default' in gateways and netifaces.AF_INET in gateways['default']:
                    gateway_ip = gateways['default'][netifaces.AF_INET][0]
                    # Assume a common subnet mask for the gateway
                    networks.append(f"{gateway_ip.rsplit('.', 1)[0]}.0/24")
            except Exception as e:
                self.console.print(f"[red]Fallback method failed: {e}[/]")
        
        return networks
    
    @staticmethod
    def ip_to_network(ip: str, netmask: str) -> str:
        """Convert IP and netmask to network CIDR notation."""
        ip_parts = [int(part) for part in ip.split('.')]
        mask_parts = [int(part) for part in netmask.split('.')]
        
        network_parts = []
        for ip_byte, mask_byte in zip(ip_parts, mask_parts):
            network_parts.append(str(ip_byte & mask_byte))
        
        # Calculate prefix length
        prefix = sum([bin(int(x)).count('1') for x in netmask.split('.')])
        return f'{".".join(network_parts)}/{prefix}'
    
    def discover_hosts(self, network: str) -> List[str]:
        """Discover active hosts in the given network using nmap."""
        try:
            self.console.print(f"[blue]Scanning {network} for active hosts...[/]")
            self.nm.scan(hosts=network, arguments='-sn')
            
            found_hosts = []
            for host in self.nm.all_hosts():
                try:
                    if 'status' in self.nm[host] and self.nm[host]['status']['state'] == 'up':
                        found_hosts.append(host)
                except (KeyError, AttributeError):
                    continue
            
            return found_hosts
            
        except Exception as e:
            self.console.print(f"[red]Error scanning network: {e}[/]")
            return []
    
    def ping_host(self, host: str) -> Tuple[bool, float]:
        """Ping a host and return (success, response_time_ms)."""
        is_windows = platform.system().lower() == 'windows'
        
        if is_windows:
            command = ['ping', '-n', str(PING_COUNT), '-w', str(TIMEOUT * 1000), host]
        else:
            command = ['ping', '-c', str(PING_COUNT), '-W', str(TIMEOUT), host]
        
        try:
            # Run command with raw bytes output to avoid encoding issues
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=TIMEOUT + 1,
                creationflags=subprocess.CREATE_NO_WINDOW if is_windows else 0
            )
            
            # Try different encodings to decode the output
            encodings = ['utf-8', 'cp850', 'cp1252', 'latin-1']
            output = None
            
            for encoding in encodings:
                try:
                    output = result.stdout.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if output is None:
                # If all encodings fail, use replace to handle errors
                output = result.stdout.decode('utf-8', errors='replace')
            
            if result.returncode == 0:
                # Extract time from ping output
                if is_windows:
                    # Windows format: time=12ms or time<1ms or Zeit=<1ms (German Windows)
                    time_match = re.search(r'(?:Zeit|time)[=<>](\d+)', output, re.IGNORECASE)
                else:
                    # Linux format: time=1.23 ms
                    time_match = re.search(r'time=([\d.]+)\s*ms', output)
                
                if time_match:
                    try:
                        response_time = float(time_match.group(1))
                        return True, response_time
                    except (ValueError, IndexError):
                        pass
                return True, 0.0  # Success but couldn't parse time
            return False, 0.0
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, Exception) as e:
            return False, 0.0
    
    def resolve_hostname(self, ip: str) -> str:
        """Resolve IP address to hostname."""
        try:
            return socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror):
            return ip
    
    def monitor_loop(self):
        """Main monitoring loop."""
        while self.running.is_set():
            for ip, status in list(self.hosts.items()):
                # Don't use console.status here to avoid conflicts with the UI thread
                is_up, response_time = self.ping_host(ip)
                
                status.total_checks += 1
                status.is_up = is_up
                
                if is_up:
                    status.last_seen = datetime.now()
                    status.response_times.append(response_time)
                    # Keep only last 10 measurements
                    status.response_times = status.response_times[-10:]
                else:
                    status.packet_loss += 1
                
                # Resolve hostname if not done yet
                if not status.hostname or status.hostname == ip:
                    try:
                        status.hostname = self.resolve_hostname(ip)
                    except Exception:
                        status.hostname = ip
                
                time.sleep(0.1)  # Small delay between pings
            
            time.sleep(UPDATE_INTERVAL)
    
    def update_ui(self):
        """Update the console UI."""
        with Live(refresh_per_second=4, console=self.console) as live:
            while self.running.is_set():
                # Create a grid for better layout
                grid = Table.grid(expand=True)
                grid.add_column()
                
                # Add title and status
                grid.add_row("[bold blue]Network Monitor MVP[/]")
                grid.add_row(f"[dim]Monitoring {len(self.hosts)} hosts | Press Ctrl+C to exit[/]")
                grid.add_row("")
                
                # Create the main table
                table = Table(show_header=True, header_style="bold magenta", expand=True)
                table.add_column("IP", style="cyan", width=15)
                table.add_column("Hostname", style="green", width=30)
                table.add_column("Status", width=10)
                table.add_column("Last Seen", width=20)
                table.add_column("Avg. RTT (ms)", justify="right")
                table.add_column("Packet Loss %", justify="right")
                
                # Add rows for each host
                any_host_up = False
                for ip, status in sorted(self.hosts.items()):
                    status_text = "[green]UP" if status.is_up else "[red]DOWN"
                    if status.is_up:
                        any_host_up = True
                    last_seen = status.last_seen.strftime("%H:%M:%S") if status.last_seen else "Never"
                    
                    table.add_row(
                        ip,
                        status.hostname[:30] + ('...' if len(status.hostname) > 30 else ''),
                        status_text,
                        last_seen,
                        f"{status.avg_response_time:.1f}" if status.response_times else "-",
                        f"{status.packet_loss_percent:.1f}%" if status.total_checks > 0 else "0.0%"
                    )
                
                # Add the table to the grid
                grid.add_row(table)
                
                # Add a footer with stats
                up_count = sum(1 for status in self.hosts.values() if status.is_up)
                grid.add_row("")
                grid.add_row(f"[dim]Hosts: [green]{up_count} up[/], [red]{len(self.hosts) - up_count} down[/] | "
                            f"Last update: {datetime.now().strftime('%H:%M:%S')}[/]")
                
                # Update the live display
                live.update(grid)
                time.sleep(0.5)
    
    def start(self):
        """Start the network monitor."""
        self.console.print("[bold blue]Network Monitor MVP[/]")
        self.console.print("Press Ctrl+C to exit\n")
        
        # Get local networks and discover hosts
        networks = self.get_local_networks()
        if not networks:
            self.console.print("[yellow]No local networks found. Please check your network connection.[/]")
            return
        
        self.console.print(f"[blue]Found networks: {', '.join(networks)}[/]")
        
        # Discover hosts in each network
        for network in networks:
            hosts = self.discover_hosts(network)
            for host in hosts:
                if host not in self.hosts:
                    self.hosts[host] = HostStatus(ip=host)
        
        if not self.hosts:
            self.console.print("[yellow]No hosts found in the network.[/]")
            return
        
        self.console.print(f"[green]Monitoring {len(self.hosts)} hosts...\n[/]")
        
        # Start monitoring threads
        self.running.set()
        self.scan_thread = Thread(target=self.monitor_loop, daemon=True)
        self.ui_thread = Thread(target=self.update_ui, daemon=True)
        
        self.scan_thread.start()
        self.ui_thread.start()
        
        try:
            while self.running.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.console.print("\n[blue]Shutting down...[/]")
            self.running.clear()
            
            if self.scan_thread:
                self.scan_thread.join(timeout=2)
            if self.ui_thread:
                self.ui_thread.join(timeout=1)
            
            self.console.print("[green]Done![/]")

def main():
    """Entry point."""
    # Check if running as root/administrator (required for some operations)
    if os.name != 'nt' and os.geteuid() != 0:
        print("This script requires root/administrator privileges for network scanning.")
        print("Please run with sudo on Linux or as Administrator on Windows.")
        sys.exit(1)
    
    monitor = NetworkMonitor()
    monitor.start()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
PingMaster - Network Monitoring Tool
A powerful, cross-platform network monitoring tool with ping monitoring, host discovery, 
configuration and logging support for network administrators.
"""
import concurrent.futures
import os
import platform
import re
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Thread, Event, Lock
from typing import Dict, List, Optional, Tuple, Any, Set

import psutil
import nmap
from rich.console import Console
from rich.live import Live
from rich.table import Table

# Local imports
from config_manager import ConfigManager
from logger import setup_logging, HostLogger

# Default configuration
DEFAULT_CONFIG = {
    'network': {
        'network': 'auto',  # 'auto' to detect automatically
        'scan_interval': '300',  # 5 minutes
        'timeout': '2',
    },
    'logging': {
        'level': 'INFO',
        'file': 'pingmaster.log',
    },
    'monitoring': {
        'ping_count': '1',
        'update_interval': '5',  # seconds between UI updates
        'max_history': '10',  # number of measurements to keep
    },
    'ports': {
        'common_ports': '21,22,23,80,443,3389,5900',
    },
}

# Initialize configuration
config = ConfigManager('config.ini')

# Apply default configuration if not set
for section, options in DEFAULT_CONFIG.items():
    if not config.config.has_section(section):
        config.config.add_section(section)
    for key, value in options.items():
        if not config.config.has_option(section, key):
            config.set(section, key, value)

# Setup logging
log_file = config.get('logging', 'file', fallback='pingmaster.log')
log_level = config.get('logging', 'level', fallback='INFO')
logger = setup_logging(level=log_level, log_file=log_file)

# Constants
PING_COUNT = config.getint('monitoring', 'ping_count', fallback=1)
UPDATE_INTERVAL = config.getfloat('monitoring', 'update_interval', fallback=5.0)
TIMEOUT = config.getfloat('network', 'timeout', fallback=2.0)
MAX_HISTORY = config.getint('monitoring', 'max_history', fallback=10)
COMMON_PORTS = [int(p) for p in config.get('ports', 'common_ports', fallback='').split(',') if p.strip()]

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
    ports: Dict[int, bool] = field(default_factory=dict)  # Port: is_open
    last_port_scan: Optional[datetime] = None
    logger: Any = None
    
    def __post_init__(self):
        """Initialize the logger for this host."""
        if self.logger is None:
            self.logger = HostLogger(logger, self.ip)
    
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
    
    def update_status(self, is_up: bool, response_time: float = 0.0) -> bool:
        """Update host status and log changes.
        
        Args:
            is_up: Whether the host is up.
            response_time: Response time in ms if host is up.
            
        Returns:
            bool: True if status changed, False otherwise.
        """
        old_status = "UP" if self.is_up else "DOWN"
        self.total_checks += 1
        
        # Update status
        status_changed = self.is_up != is_up
        self.is_up = is_up
        
        if is_up:
            self.last_seen = datetime.now()
            self.response_times.append(response_time)
            self.response_times = self.response_times[-MAX_HISTORY:]
            
            # Log status change if needed
            if status_changed:
                self.logger.status_change(old_status, "UP", f"Response time: {response_time:.1f}ms")
        else:
            self.packet_loss += 1
            if status_changed:
                self.logger.status_change(old_status, "DOWN")
        
        return status_changed

class NetworkMonitor:
    """Main network monitoring class."""
    
    def __init__(self):
        """Initialize the network monitor with configuration."""
        self.console = Console()
        self.hosts: Dict[str, HostStatus] = {}
        self.running = Event()
        self.scan_thread: Optional[Thread] = None
        self.ui_thread: Optional[Thread] = None
        self.port_scan_thread: Optional[Thread] = None
        self.nm = nmap.PortScanner()
        
        # Load configuration
        self.scan_interval = config.getint('network', 'scan_interval', fallback=300)
        self.last_network_scan = datetime.min
        
        logger.info("Network Monitor initialized")
        logger.debug(f"Configuration: {dict(config.config.items())}")
        
    def get_local_networks(self) -> List[str]:
        """Get list of local networks from available interfaces using psutil."""
        networks = []
        try:
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        try:
                            ip = addr.address
                            netmask = addr.netmask
                            # Skip localhost and invalid addresses
                            if (ip != '127.0.0.1' and 
                                ip != '0.0.0.0' and 
                                not ip.startswith('169.254.') and  # Link-local
                                netmask != '255.255.255.255'):  # Skip point-to-point
                                network = self.ip_to_network(ip, netmask)
                                if network not in networks:  # Avoid duplicates
                                    networks.append(network)
                        except (KeyError, ValueError, AttributeError) as e:
                            self.console.print(f"[yellow]Warning: Could not process address on {iface}: {e}[/]")
                            continue
        except Exception as e:
            self.console.print(f"[red]Error getting network interfaces: {e}[/]")
        
        # If no networks found, try a fallback method
        if not networks:
            self.console.print("[yellow]No networks found, trying fallback method...[/]")
            try:
                # Try to get the default gateway's network using psutil
                gateways = psutil.net_if_stats()
                for iface, stats in gateways.items():
                    if stats.isup:
                        # Try to get a reasonable network from the interface
                        for addr in psutil.net_if_addrs().get(iface, []):
                            if addr.family == socket.AF_INET and addr.address != '127.0.0.1':
                                gateway_ip = addr.address
                                # Assume a common subnet mask for the gateway
                                networks.append(f"{gateway_ip.rsplit('.', 1)[0]}.0/24")
                                break
                        if networks:
                            break
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
    
    def _ping_host_worker(self, ip: str, results: Dict[str, bool], lock: Lock):
        """Worker function for parallel pinging with optimized timeout."""
        try:
            # Use system ping with very aggressive timeouts for initial scan
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            timeout = '500' if platform.system().lower() == 'windows' else '0.5'  # 500ms timeout
            count = '1'
            
            if platform.system().lower() == 'windows':
                command = ['ping', param, count, '-w', timeout, '-l', '1', ip]
            else:
                command = ['ping', param, count, '-W', timeout, '-s', '1', ip]
            
            # Use Popen with faster timeouts
            startupinfo = None
            if platform.system().lower() == 'windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system().lower() == 'windows' else 0
            )
            
            try:
                # Use a timeout to prevent hanging on unresponsive hosts
                _, _ = process.communicate(timeout=1.0)
                is_up = process.returncode == 0
            except subprocess.TimeoutExpired:
                process.kill()
                is_up = False
            
            with lock:
                results[ip] = is_up
                
        except Exception as e:
            with lock:
                results[ip] = False
            logger.debug(f"Ping to {ip} failed: {e}")

    def discover_hosts(self, network: str) -> List[str]:
        """Discover active hosts in the given network using optimized parallel pinging."""
        try:
            # Remove the scanning message to prevent screen jumping
            # Skip nmap for now as direct pinging is faster for local networks
            base_ip = '.'.join(network.split('.')[:3])
            
            # Only scan common IP ranges that are likely to be used
            common_ips = []
            for i in range(1, 255):
                # Prioritize common DHCP ranges first
                if 1 <= i <= 30 or 100 <= i <= 200 or i == 1 or i == 254:
                    common_ips.append(f"{base_ip}.{i}")
            
            results = {}
            lock = Lock()
            
            # First pass: Quick scan of common IPs with aggressive timeouts
            with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
                futures = [
                    executor.submit(self._ping_host_worker, ip, results, lock)
                    for ip in common_ips
                ]
                # Wait for all pings to complete or timeout after 2 seconds
                concurrent.futures.wait(futures, timeout=2.0)
            
            # Get responsive hosts from first pass
            responsive_hosts = [ip for ip, is_up in results.items() if is_up]
            
            # Second pass: If we found responsive hosts, scan the rest of the range
            if responsive_hosts:
                remaining_ips = [f"{base_ip}.{i}" for i in range(1, 255) 
                               if f"{base_ip}.{i}" not in common_ips]
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
                    futures = [
                        executor.submit(self._ping_host_worker, ip, results, lock)
                        for ip in remaining_ips
                    ]
                    # Give it a bit more time for the full scan
                    concurrent.futures.wait(futures, timeout=3.0)
                
                # Add any newly found responsive hosts
                responsive_hosts.extend([ip for ip, is_up in results.items() 
                                      if is_up and ip not in responsive_hosts])
            
            return responsive_hosts if responsive_hosts else list(results.keys())
            
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
    
    def _monitor_host(self, ip: str, status: HostStatus):
        """Monitor a single host and update its status."""
        try:
            is_up, response_time = self.ping_host(ip)
            status_changed = status.update_status(is_up, response_time)
            
            # Only resolve hostname if host is up and we don't have it yet
            if is_up and (not status.hostname or status.hostname == ip):
                try:
                    status.hostname = self.resolve_hostname(ip)
                except Exception as e:
                    status.logger.warning(f"Could not resolve hostname: {e}")
            
            return status_changed
            
        except Exception as e:
            status.logger.error(f"Error monitoring host: {e}")
            return False

    def monitor_loop(self):
        """Main monitoring loop with optimized parallel host checking."""
        while self.running.is_set():
            start_time = time.time()
            
            try:
                # Group hosts by their current status to prioritize down hosts
                up_hosts = []
                down_hosts = []
                
                for ip, status in self.hosts.items():
                    if status.is_up:
                        up_hosts.append((ip, status))
                    else:
                        down_hosts.append((ip, status))
                
                # Check down hosts first, then up hosts
                hosts_to_check = down_hosts + up_hosts
                
                if not hosts_to_check:
                    time.sleep(1)
                    continue
                
                # Calculate optimal number of workers based on host count
                max_workers = min(50, max(10, len(hosts_to_check) // 2))
                
                # Use ThreadPoolExecutor with optimized settings
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=max_workers,
                    thread_name_prefix='host_monitor_'
                ) as executor:
                    # Submit all hosts for monitoring
                    future_to_ip = {
                        executor.submit(self._monitor_host, ip, status): ip 
                        for ip, status in hosts_to_check
                    }
                    
                    # Process results with a more generous timeout
                    cycle_timeout = max(10, min(30, len(hosts_to_check) * 0.5))  # Dynamic timeout based on host count
                    
                    try:
                        for future in concurrent.futures.as_completed(
                            future_to_ip, 
                            timeout=cycle_timeout
                        ):
                            ip = future_to_ip[future]
                            try:
                                future.result(timeout=2.0)  # Increased per-host timeout
                            except concurrent.futures.TimeoutError:
                                logger.debug(f"Host {ip} check took too long, continuing")
                            except Exception as e:
                                logger.debug(f"Error processing {ip}: {e}")
                    except concurrent.futures.TimeoutError:
                        logger.debug(f"Monitoring cycle timed out after {cycle_timeout:.1f}s, continuing")
                
                # Calculate time taken and sleep if needed
                time_taken = time.time() - start_time
                sleep_time = max(0, UPDATE_INTERVAL - time_taken)
                
                # Only log if we're running behind schedule
                if time_taken > UPDATE_INTERVAL * 1.1:  # 10% over the update interval
                    logger.debug(f"Monitoring cycle took {time_taken:.1f}s (target: {UPDATE_INTERVAL}s)")
                
                if sleep_time > 0:
                    time.sleep(min(sleep_time, UPDATE_INTERVAL))
                    
            except Exception as e:
                logger.error(f"Unexpected error in monitor_loop: {e}")
                time.sleep(1)  # Prevent tight loop on errors
    
    def update_ui(self):
        """Update the console UI."""
        # Disable console output during updates to prevent flickering
        with Live(refresh_per_second=4, console=self.console, transient=True) as live:
            last_update = time.time()
            while self.running.is_set():
                current_time = time.time()
                # Only update the UI at most 4 times per second to reduce flicker
                if current_time - last_update >= 0.25:  # 4 FPS
                    last_update = current_time
                    # Create a grid for better layout
                    grid = Table.grid(expand=True)
                    grid.add_column()
                    
                    # Add title and status (minimal header)
                    grid.add_row(f"[dim]Monitoring {len(self.hosts)} hosts | Press Ctrl+C to exit[/]")
                    
                    # Create the main table
                    table = Table(show_header=True, header_style="bold magenta", expand=True)
                    table.add_column("IP", style="cyan", width=15)
                    table.add_column("Hostname", style="green", width=30)
                    table.add_column("Status", width=10)
                    table.add_column("Last Seen", width=20)
                    table.add_column("Avg. RTT (ms)", justify="right", width=15)
                    table.add_column("Packet Loss %", justify="right", width=15)
                    
                    # Sort hosts by IP address for consistent display
                    for ip, status in sorted(self.hosts.items()):
                        # Format status with color
                        status_text = "[green]UP[/]" if status.is_up else "[red]DOWN[/]"
                        
                        # Format last seen time
                        if status.last_seen:
                            last_seen = status.last_seen.strftime("%H:%M:%S")
                        else:
                            last_seen = "Never"
                        
                        # Add row to table
                        table.add_row(
                            ip,
                            status.hostname or "",
                            status_text,
                            last_seen,
                            f"{status.avg_response_time:.1f}" if status.response_times else "-",
                            f"{status.packet_loss_percent:.1f}%"
                        )
                    
                    # Add the table to the grid
                    grid.add_row(table)
                    grid.add_row("")
                    
                    # Add status bar
                    up_count = sum(1 for host in self.hosts.values() if host.is_up)
                    grid.add_row(f"[dim]Hosts: [green]{up_count} up[/], [red]{len(self.hosts) - up_count} down[/] | "
                                f"Last update: {datetime.now().strftime('%H:%M:%S')}[/]")
                    
                    # Update the live display
                    live.update(grid)
                
                # Small sleep to prevent CPU overuse
                time.sleep(0.05)
    
    def start(self):
        """Start the network monitor."""
        # Get local networks and discover hosts
        networks = self.get_local_networks()
        if not networks:
            self.console.print("[yellow]No local networks found. Please check your network connection.[/]")
            return

        # Discover hosts in each network
        host_count = 0
        for network in networks:
            for host in self.discover_hosts(network):
                if host not in self.hosts:
                    self.hosts[host] = HostStatus(ip=host)
                    host_count += 1

        if not self.hosts:
            self.console.print("[yellow]No hosts found in the network.[/]")
            return

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
            self.running.clear()

            if self.scan_thread:
                self.scan_thread.join(timeout=2)
            if self.ui_thread:
                self.ui_thread.join(timeout=1)

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

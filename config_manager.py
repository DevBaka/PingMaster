"""Configuration manager for the Network Monitor."""
import configparser
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

class ConfigManager:
    """Manages configuration loading and saving."""
    
    def __init__(self, config_file: str = 'config.ini'):
        """Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file.
        """
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        self.defaults = {
            'network': {
                'network': '192.168.1.0/24',
                'scan_interval': '300',
                'timeout': '2',
            },
            'logging': {
                'level': 'INFO',
                'file': 'network_monitor.log',
            },
            'alerts': {
                'email_alerts': 'false',
                'email_from': '',
                'email_to': '',
                'smtp_server': '',
                'smtp_port': '587',
                'smtp_username': '',
                'smtp_password': '',
                'alert_on_down': 'true',
                'alert_on_up': 'true',
            },
            'ports': {
                'common_ports': '21,22,23,25,53,80,110,143,443,445,465,587,993,995,1433,1521,3306,3389,5432,5900,8080,8443',
            }
        }
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or create default if not exists."""
        if not self.config_file.exists():
            self._create_default_config()
        
        self.config.read(self.config_file, encoding='utf-8')
        
        # Ensure all sections and options exist
        for section, options in self.defaults.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for option, value in options.items():
                if not self.config.has_option(section, option):
                    self.config.set(section, option, value)
        
        self._save_config()
    
    def _create_default_config(self):
        """Create a default configuration file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._save_config()
    
    def _save_config(self):
        """Save the current configuration to file."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get(self, section: str, option: str, fallback: Any = None) -> str:
        """Get a configuration value.
        
        Args:
            section: Configuration section.
            option: Configuration option.
            fallback: Fallback value if option is not found.
            
        Returns:
            The configuration value as a string.
        """
        try:
            return self.config.get(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def getint(self, section: str, option: str, fallback: int = None) -> int:
        """Get a configuration value as an integer.
        
        Args:
            section: Configuration section.
            option: Configuration option.
            fallback: Fallback value if option is not found or invalid.
            
        Returns:
            The configuration value as an integer.
        """
        try:
            return self.config.getint(section, option, fallback=fallback)
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def getfloat(self, section: str, option: str, fallback: float = None) -> float:
        """Get a configuration value as a float.
        
        Args:
            section: Configuration section.
            option: Configuration option.
            fallback: Fallback value if option is not found or invalid.
            
        Returns:
            The configuration value as a float.
        """
        try:
            return self.config.getfloat(section, option, fallback=fallback)
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def getboolean(self, section: str, option: str, fallback: bool = None) -> bool:
        """Get a configuration value as a boolean.
        
        Args:
            section: Configuration section.
            option: Configuration option.
            fallback: Fallback value if option is not found or invalid.
            
        Returns:
            The configuration value as a boolean.
        """
        try:
            return self.config.getboolean(section, option, fallback=fallback)
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def getlist(self, section: str, option: str, fallback: List[str] = None, 
                delimiter: str = ',', strip: bool = True) -> List[str]:
        """Get a configuration value as a list.
        
        Args:
            section: Configuration section.
            option: Configuration option.
            fallback: Fallback value if option is not found.
            delimiter: Delimiter to split the string.
            strip: Whether to strip whitespace from items.
            
        Returns:
            The configuration value as a list of strings.
        """
        value = self.get(section, option)
        if value is None:
            return fallback or []
        
        items = value.split(delimiter)
        if strip:
            items = [item.strip() for item in items]
        
        return items
    
    def set(self, section: str, option: str, value: Any):
        """Set a configuration value.
        
        Args:
            section: Configuration section.
            option: Configuration option.
            value: Value to set.
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        if isinstance(value, (list, tuple, set)):
            value = ','.join(str(item) for item in value)
        else:
            value = str(value)
        
        self.config.set(section, option, value)
        self._save_config()

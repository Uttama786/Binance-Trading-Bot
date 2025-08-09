"""
Configuration module for Binance Futures Trading Bot
Handles API credentials, settings, and environment configuration
"""

import os
import json
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class BotConfig:
    """Configuration class for the trading bot"""
    api_key: str
    api_secret: str
    use_testnet: bool = True
    base_url: str = "https://testnet.binancefuture.com"
    log_file: str = "bot.log"
    log_level: str = "INFO"
    default_leverage: int = 1
    max_position_size: float = 1000.0
    request_timeout: int = 30
    max_retries: int = 3


class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = None
    
    def load_config(self) -> BotConfig:
        """Load configuration from file or environment variables"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
        else:
            config_data = {}
        
        # Load from environment variables if not in file
        api_key = config_data.get('api_key') or os.getenv('BINANCE_API_KEY', '')
        api_secret = config_data.get('api_secret') or os.getenv('BINANCE_API_SECRET', '')
        
        if not api_key or not api_secret:
            raise ValueError("API credentials not found. Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables or create a config.json file.")
        
        self.config = BotConfig(
            api_key=api_key,
            api_secret=api_secret,
            use_testnet=config_data.get('use_testnet', True),
            base_url=config_data.get('base_url', "https://testnet.binancefuture.com"),
            log_file=config_data.get('log_file', 'bot.log'),
            log_level=config_data.get('log_level', 'INFO'),
            default_leverage=config_data.get('default_leverage', 1),
            max_position_size=config_data.get('max_position_size', 1000.0),
            request_timeout=config_data.get('request_timeout', 30),
            max_retries=config_data.get('max_retries', 3)
        )
        
        return self.config
    
    def save_config(self, config: BotConfig) -> None:
        """Save configuration to file"""
        config_data = {
            'api_key': config.api_key,
            'api_secret': config.api_secret,
            'use_testnet': config.use_testnet,
            'base_url': config.base_url,
            'log_file': config.log_file,
            'log_level': config.log_level,
            'default_leverage': config.default_leverage,
            'max_position_size': config.max_position_size,
            'request_timeout': config.request_timeout,
            'max_retries': config.max_retries
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def get_config(self) -> BotConfig:
        """Get current configuration"""
        if self.config is None:
            return self.load_config()
        return self.config

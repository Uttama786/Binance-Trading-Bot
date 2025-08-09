"""
Logging module for Binance Futures Trading Bot
Provides structured logging for API calls, orders, errors, and executions
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        
        return json.dumps(log_entry)


class BotLogger:
    """Main logging class for the trading bot"""
    
    def __init__(self, log_file: str = "bot.log", log_level: str = "INFO"):
        self.log_file = log_file
        self.log_level = getattr(logging, log_level.upper())
        
        # Create logs directory if it doesn't exist
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger('binance_bot')
        self.logger.setLevel(self.log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler with structured formatting
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(StructuredFormatter())
        
        # Console handler with simple formatting
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_api_call(self, endpoint: str, method: str, params: Dict[str, Any], 
                    status_code: int, response_time_ms: float, response: Optional[Dict] = None):
        """Log API call details"""
        extra_data = {
            "type": "API_CALL",
            "endpoint": endpoint,
            "method": method,
            "params": params,
            "status_code": status_code,
            "response_time_ms": response_time_ms
        }
        
        if response:
            extra_data["response"] = response
        
        record = self.logger.makeRecord(
            'binance_bot', logging.INFO, '', 0, '', (), None
        )
        record.extra_data = extra_data
        self.logger.handle(record)
    
    def log_order_placed(self, order_type: str, symbol: str, side: str, 
                        quantity: float, price: Optional[float] = None, 
                        order_id: Optional[str] = None, **kwargs):
        """Log order placement"""
        extra_data = {
            "type": "ORDER_PLACED",
            "order_type": order_type,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "order_id": order_id,
            **kwargs
        }
        
        record = self.logger.makeRecord(
            'binance_bot', logging.INFO, '', 0, '', (), None
        )
        record.extra_data = extra_data
        self.logger.handle(record)
    
    def log_order_executed(self, order_id: str, symbol: str, side: str,
                          quantity: float, price: float, commission: float):
        """Log order execution"""
        extra_data = {
            "type": "ORDER_EXECUTED",
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "commission": commission
        }
        
        record = self.logger.makeRecord(
            'binance_bot', logging.INFO, '', 0, '', (), None
        )
        record.extra_data = extra_data
        self.logger.handle(record)
    
    def log_error(self, error_type: str, message: str, **kwargs):
        """Log error details"""
        extra_data = {
            "type": "ERROR",
            "error_type": error_type,
            "message": message,
            **kwargs
        }
        
        record = self.logger.makeRecord(
            'binance_bot', logging.ERROR, '', 0, '', (), None
        )
        record.extra_data = extra_data
        self.logger.handle(record)
    
    def log_validation_error(self, field: str, value: Any, message: str):
        """Log validation errors"""
        self.log_error("VALIDATION_ERROR", message, field=field, value=value)
    
    def log_api_error(self, endpoint: str, status_code: int, error_message: str, error_code: Optional[str] = None):
        """Log API errors"""
        self.log_error("API_ERROR", error_message, endpoint=endpoint, status_code=status_code, error_code=error_code)
    
    def log_order_error(self, symbol: str, side: str, quantity: float, error_message: str, order_type: str, **kwargs):
        """Log order errors"""
        self.log_error("ORDER_ERROR", error_message, symbol=symbol, side=side, quantity=quantity, order_type=order_type, **kwargs)
    
    def log_bot_action(self, action: str, **kwargs):
        """Log general bot actions"""
        extra_data = {
            "type": "BOT_ACTION",
            "action": action,
            **kwargs
        }
        
        record = self.logger.makeRecord(
            'binance_bot', logging.INFO, '', 0, '', (), None
        )
        record.extra_data = extra_data
        self.logger.handle(record)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)

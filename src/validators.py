"""
Validation module for Binance Futures Trading Bot
Handles input validation for symbols, quantities, prices, and trading parameters
"""

import re
from typing import Dict, Any, List, Optional
from decimal import Decimal, InvalidOperation


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class TradingValidator:
    """Validates trading parameters and inputs"""
    
    def __init__(self, logger):
        self.logger = logger
        self.supported_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT',
            'SOLUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'MATICUSDT',
            'LINKUSDT', 'LTCUSDT', 'BCHUSDT', 'UNIUSDT', 'ATOMUSDT'
        ]
        
        # Common trading parameters
        self.min_quantity = 0.001
        self.max_quantity = 1000000
        self.min_price = 0.0001
        self.max_price = 1000000
        self.supported_sides = ['BUY', 'SELL']
        self.supported_order_types = ['MARKET', 'LIMIT', 'STOP_MARKET', 'STOP_LIMIT', 'TAKE_PROFIT_MARKET', 'TAKE_PROFIT_LIMIT']
    
    def validate_symbol(self, symbol: str) -> str:
        """Validate trading symbol"""
        if not symbol:
            self.logger.log_validation_error("symbol", symbol, "Symbol cannot be empty")
            raise ValidationError("Symbol cannot be empty")
        
        # Convert to uppercase and remove spaces
        symbol = symbol.upper().strip()
        
        # Check if symbol is in supported list
        if symbol not in self.supported_symbols:
            self.logger.log_validation_error("symbol", symbol, f"Symbol {symbol} is not supported")
            raise ValidationError(f"Symbol {symbol} is not supported. Supported symbols: {', '.join(self.supported_symbols)}")
        
        return symbol
    
    def validate_quantity(self, quantity: Any) -> float:
        """Validate order quantity"""
        try:
            quantity = float(quantity)
        except (ValueError, TypeError):
            self.logger.log_validation_error("quantity", quantity, "Quantity must be a valid number")
            raise ValidationError("Quantity must be a valid number")
        
        if quantity <= 0:
            self.logger.log_validation_error("quantity", quantity, "Quantity must be positive")
            raise ValidationError("Quantity must be positive")
        
        if quantity < self.min_quantity:
            self.logger.log_validation_error("quantity", quantity, f"Quantity must be at least {self.min_quantity}")
            raise ValidationError(f"Quantity must be at least {self.min_quantity}")
        
        if quantity > self.max_quantity:
            self.logger.log_validation_error("quantity", quantity, f"Quantity cannot exceed {self.max_quantity}")
            raise ValidationError(f"Quantity cannot exceed {self.max_quantity}")
        
        return quantity
    
    def validate_price(self, price: Any) -> float:
        """Validate order price"""
        try:
            price = float(price)
        except (ValueError, TypeError):
            self.logger.log_validation_error("price", price, "Price must be a valid number")
            raise ValidationError("Price must be a valid number")
        
        if price <= 0:
            self.logger.log_validation_error("price", price, "Price must be positive")
            raise ValidationError("Price must be positive")
        
        if price < self.min_price:
            self.logger.log_validation_error("price", price, f"Price must be at least {self.min_price}")
            raise ValidationError(f"Price must be at least {self.min_price}")
        
        if price > self.max_price:
            self.logger.log_validation_error("price", price, f"Price cannot exceed {self.max_price}")
            raise ValidationError(f"Price cannot exceed {self.max_price}")
        
        return price
    
    def validate_side(self, side: str) -> str:
        """Validate order side"""
        if not side:
            self.logger.log_validation_error("side", side, "Side cannot be empty")
            raise ValidationError("Side cannot be empty")
        
        side = side.upper().strip()
        
        if side not in self.supported_sides:
            self.logger.log_validation_error("side", side, f"Side {side} is not supported")
            raise ValidationError(f"Side {side} is not supported. Supported sides: {', '.join(self.supported_sides)}")
        
        return side
    
    def validate_order_type(self, order_type: str) -> str:
        """Validate order type"""
        if not order_type:
            self.logger.log_validation_error("order_type", order_type, "Order type cannot be empty")
            raise ValidationError("Order type cannot be empty")
        
        order_type = order_type.upper().strip()
        
        if order_type not in self.supported_order_types:
            self.logger.log_validation_error("order_type", order_type, f"Order type {order_type} is not supported")
            raise ValidationError(f"Order type {order_type} is not supported. Supported types: {', '.join(self.supported_order_types)}")
        
        return order_type
    
    def validate_leverage(self, leverage: Any) -> int:
        """Validate leverage setting"""
        try:
            leverage = int(leverage)
        except (ValueError, TypeError):
            self.logger.log_validation_error("leverage", leverage, "Leverage must be a valid integer")
            raise ValidationError("Leverage must be a valid integer")
        
        if leverage < 1 or leverage > 125:
            self.logger.log_validation_error("leverage", leverage, "Leverage must be between 1 and 125")
            raise ValidationError("Leverage must be between 1 and 125")
        
        return leverage
    
    def validate_time_in_force(self, time_in_force: str) -> str:
        """Validate time in force parameter"""
        valid_tif = ['GTC', 'IOC', 'FOK', 'GTX']
        
        if not time_in_force:
            return 'GTC'  # Default to Good Till Canceled
        
        time_in_force = time_in_force.upper().strip()
        
        if time_in_force not in valid_tif:
            self.logger.log_validation_error("time_in_force", time_in_force, f"Time in force {time_in_force} is not valid")
            raise ValidationError(f"Time in force {time_in_force} is not valid. Valid options: {', '.join(valid_tif)}")
        
        return time_in_force
    
    def validate_stop_price(self, stop_price: Any, side: str, current_price: float) -> float:
        """Validate stop price for stop orders"""
        stop_price = self.validate_price(stop_price)
        
        if side == 'BUY' and stop_price <= current_price:
            self.logger.log_validation_error("stop_price", stop_price, "Stop price for BUY orders must be above current price")
            raise ValidationError("Stop price for BUY orders must be above current price")
        
        if side == 'SELL' and stop_price >= current_price:
            self.logger.log_validation_error("stop_price", stop_price, "Stop price for SELL orders must be below current price")
            raise ValidationError("Stop price for SELL orders must be below current price")
        
        return stop_price
    
    def validate_take_profit_stop_loss(self, take_profit: float, stop_loss: float, side: str, entry_price: float):
        """Validate take profit and stop loss levels"""
        take_profit = self.validate_price(take_profit)
        stop_loss = self.validate_price(stop_loss)
        
        if side == 'BUY':
            if take_profit <= entry_price:
                self.logger.log_validation_error("take_profit", take_profit, "Take profit for BUY orders must be above entry price")
                raise ValidationError("Take profit for BUY orders must be above entry price")
            
            if stop_loss >= entry_price:
                self.logger.log_validation_error("stop_loss", stop_loss, "Stop loss for BUY orders must be below entry price")
                raise ValidationError("Stop loss for BUY orders must be below entry price")
        
        elif side == 'SELL':
            if take_profit >= entry_price:
                self.logger.log_validation_error("take_profit", take_profit, "Take profit for SELL orders must be below entry price")
                raise ValidationError("Take profit for SELL orders must be below entry price")
            
            if stop_loss <= entry_price:
                self.logger.log_validation_error("stop_loss", stop_loss, "Stop loss for SELL orders must be above entry price")
                raise ValidationError("Stop loss for SELL orders must be above entry price")
        
        return take_profit, stop_loss
    
    def validate_grid_parameters(self, upper_price: float, lower_price: float, grid_number: int, quantity: float):
        """Validate grid trading parameters"""
        upper_price = self.validate_price(upper_price)
        lower_price = self.validate_price(lower_price)
        
        if upper_price <= lower_price:
            self.logger.log_validation_error("upper_price", upper_price, "Upper price must be greater than lower price")
            raise ValidationError("Upper price must be greater than lower price")
        
        if grid_number < 2 or grid_number > 100:
            self.logger.log_validation_error("grid_number", grid_number, "Grid number must be between 2 and 100")
            raise ValidationError("Grid number must be between 2 and 100")
        
        quantity = self.validate_quantity(quantity)
        
        return upper_price, lower_price, grid_number, quantity
    
    def validate_twap_parameters(self, total_quantity: float, duration_minutes: int, chunks: int):
        """Validate TWAP parameters"""
        total_quantity = self.validate_quantity(total_quantity)
        
        if duration_minutes < 1 or duration_minutes > 1440:  # Max 24 hours
            self.logger.log_validation_error("duration_minutes", duration_minutes, "Duration must be between 1 and 1440 minutes")
            raise ValidationError("Duration must be between 1 and 1440 minutes")
        
        if chunks < 2 or chunks > 100:
            self.logger.log_validation_error("chunks", chunks, "Number of chunks must be between 2 and 100")
            raise ValidationError("Number of chunks must be between 2 and 100")
        
        return total_quantity, duration_minutes, chunks
    
    def validate_market_order_params(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Validate market order parameters"""
        return {
            'symbol': self.validate_symbol(symbol),
            'side': self.validate_side(side),
            'quantity': self.validate_quantity(quantity)
        }
    
    def validate_limit_order_params(self, symbol: str, side: str, quantity: float, price: float, 
                                  time_in_force: str = 'GTC') -> Dict[str, Any]:
        """Validate limit order parameters"""
        return {
            'symbol': self.validate_symbol(symbol),
            'side': self.validate_side(side),
            'quantity': self.validate_quantity(quantity),
            'price': self.validate_price(price),
            'time_in_force': self.validate_time_in_force(time_in_force)
        }

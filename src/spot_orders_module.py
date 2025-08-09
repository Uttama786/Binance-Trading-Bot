"""
Spot Orders Module for Binance Spot Trading
Handles spot order placement logic and validation
"""

from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_DOWN
from .spot_api_client import SpotAPIClient
from .validators import TradingValidator
from .logger import BotLogger


class SpotOrderManager:
    """Manages spot order placement and validation"""
    
    def __init__(self, api_client: SpotAPIClient, validator: TradingValidator, logger: BotLogger):
        self.api_client = api_client
        self.validator = validator
        self.logger = logger
        self.logger.info("SpotOrderManager initialized")
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Place a market order with quantity"""
        try:
            # Validate inputs
            if not self.validator.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
            
            if not self.validator.validate_side(side):
                raise ValueError(f"Invalid side: {side}")
            
            if not self.validator.validate_quantity(quantity):
                raise ValueError(f"Invalid quantity: {quantity}")
            
            # Get symbol info for precision
            symbol_info = self.api_client.get_symbol_info(symbol)
            lot_size_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
            
            if lot_size_filter:
                step_size = float(lot_size_filter['stepSize'])
                precision = len(str(step_size).split('.')[-1]) if '.' in str(step_size) else 0
                quantity = float(Decimal(str(quantity)).quantize(
                    Decimal(str(step_size)), rounding=ROUND_DOWN
                ))
            
            # Log order attempt
            self.logger.info(f"Placing spot market order: {symbol} {side} {quantity}")
            
            # Place order
            result = self.api_client.place_market_order(symbol, side, quantity)
            
            # Log success
            self.logger.info(f"Spot market order placed successfully - Order ID: {result.get('orderId')}")
            
            return result
            
        except Exception as e:
            self.logger.log_order_error(
                symbol=symbol,
                side=side,
                quantity=quantity,
                error_message=str(e),
                order_type="MARKET"
            )
            raise
    
    def place_market_order_usdt(self, symbol: str, side: str, usdt_amount: float) -> Dict[str, Any]:
        """Place a market order using USDT amount"""
        try:
            # Validate inputs
            if not self.validator.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
            
            if not self.validator.validate_side(side):
                raise ValueError(f"Invalid side: {side}")
            
            if usdt_amount <= 0:
                raise ValueError(f"Invalid USDT amount: {usdt_amount}")
            
            # Log order attempt
            self.logger.info(f"Placing spot market order: {symbol} {side} ${usdt_amount} USDT")
            
            # Place order
            result = self.api_client.place_market_order_usdt(symbol, side, usdt_amount)
            
            # Log success
            self.logger.info(f"Spot market order placed successfully - Order ID: {result.get('orderId')}, Executed: {result.get('executedQty')}")
            
            return result
            
        except Exception as e:
            self.logger.log_order_error(
                symbol=symbol,
                side=side,
                quantity=usdt_amount,
                error_message=str(e),
                order_type="MARKET"
            )
            raise
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        """Place a limit order"""
        try:
            # Validate inputs
            if not self.validator.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
            
            if not self.validator.validate_side(side):
                raise ValueError(f"Invalid side: {side}")
            
            if not self.validator.validate_quantity(quantity):
                raise ValueError(f"Invalid quantity: {quantity}")
            
            if not self.validator.validate_price(price):
                raise ValueError(f"Invalid price: {price}")
            
            # Get symbol info for precision
            symbol_info = self.api_client.get_symbol_info(symbol)
            
            # Apply lot size precision
            lot_size_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
            if lot_size_filter:
                step_size = float(lot_size_filter['stepSize'])
                quantity = float(Decimal(str(quantity)).quantize(
                    Decimal(str(step_size)), rounding=ROUND_DOWN
                ))
            
            # Apply price precision
            price_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)
            if price_filter:
                tick_size = float(price_filter['tickSize'])
                price = float(Decimal(str(price)).quantize(
                    Decimal(str(tick_size)), rounding=ROUND_DOWN
                ))
            
            # Log order attempt
            self.logger.info(f"Placing spot limit order: {symbol} {side} {quantity} @ ${price}")
            
            # Place order
            result = self.api_client.place_limit_order(symbol, side, quantity, price)
            
            # Log success
            self.logger.info(f"Spot limit order placed successfully - Order ID: {result.get('orderId')}")
            
            return result
            
        except Exception as e:
            self.logger.log_order_error(
                symbol=symbol,
                side=side,
                quantity=quantity,
                error_message=str(e),
                order_type="LIMIT",
                price=price
            )
            raise
    
    def get_account_balance(self, asset: str = None) -> Dict[str, Any]:
        """Get account balance information"""
        try:
            account_info = self.api_client.get_account_info()
            balances = account_info.get('balances', [])
            
            if asset:
                for balance in balances:
                    if balance['asset'] == asset.upper():
                        return balance
                return {'asset': asset.upper(), 'free': '0.00000000', 'locked': '0.00000000'}
            else:
                # Return all non-zero balances
                return [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
        
        except Exception as e:
            self.logger.error(f"Failed to get account balance: {str(e)}")
            raise

"""
Stop-Limit Orders module for Binance Futures Trading Bot
Handles stop-limit order placement and management
"""

from typing import Dict, Any, Optional
from ..api_client import BinanceAPIClient
from ..validators import TradingValidator, ValidationError
from ..logger import BotLogger


class StopLimitOrderManager:
    """Manages stop-limit order operations"""
    
    def __init__(self, api_client: BinanceAPIClient, validator: TradingValidator, logger: BotLogger):
        self.api_client = api_client
        self.validator = validator
        self.logger = logger
        self.logger.info("StopLimitOrderManager initialized")
    
    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, price: float, 
                              stop_price: float, time_in_force: str = 'GTC', reduce_only: bool = False) -> Dict[str, Any]:
        """
        Place a stop-limit order
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Limit price (execution price)
            stop_price: Stop price (trigger price)
            time_in_force: Time in force ('GTC', 'IOC', 'FOK', 'GTX')
            reduce_only: Whether this order should only reduce position
            
        Returns:
            Order response from Binance API
        """
        try:
            # Validate basic parameters
            validated_params = self.validator.validate_limit_order_params(symbol, side, quantity, price, time_in_force)
            
            # Get current market price for validation
            ticker = self.api_client.get_ticker_price(validated_params['symbol'])
            current_price = float(ticker['price'])
            
            # Validate stop price relative to current market price
            validated_stop_price = self.validator.validate_stop_price(stop_price, validated_params['side'], current_price)
            
            # Validate price relationship
            if validated_params['side'] == 'BUY':
                if validated_params['price'] < validated_stop_price:
                    self.logger.warning(f"Limit price ({validated_params['price']}) is below stop price ({validated_stop_price}) for BUY order")
            else:  # SELL
                if validated_params['price'] > validated_stop_price:
                    self.logger.warning(f"Limit price ({validated_params['price']}) is above stop price ({validated_stop_price}) for SELL order")
            
            # Place the order
            order_response = self.api_client.place_stop_limit_order(
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                price=validated_params['price'],
                stop_price=validated_stop_price,
                time_in_force=validated_params['time_in_force'],
                reduce_only=reduce_only
            )
            
            # Log order placement
            self.logger.log_order_placed(
                order_type="STOP_LIMIT",
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                price=validated_params['price'],
                order_id=order_response.get('orderId'),
                stop_price=validated_stop_price,
                time_in_force=validated_params['time_in_force'],
                reduce_only=reduce_only,
                current_market_price=current_price
            )
            
            self.logger.info(f"Stop-limit order placed successfully: {validated_params['side']} {validated_params['quantity']} {validated_params['symbol']} at {validated_params['price']} (stop: {validated_stop_price})")
            
            return order_response
            
        except ValidationError as e:
            self.logger.log_error("VALIDATION_ERROR", str(e), symbol=symbol, side=side, quantity=quantity, price=price, stop_price=stop_price)
            raise
        except Exception as e:
            self.logger.log_error("ORDER_ERROR", str(e), symbol=symbol, side=side, quantity=quantity, price=price, stop_price=stop_price)
            raise
    
    def place_stop_loss_limit(self, symbol: str, side: str, quantity: float, stop_price: float, 
                             limit_price: float, reduce_only: bool = True) -> Dict[str, Any]:
        """Place a stop-loss limit order"""
        return self.place_stop_limit_order(symbol, side, quantity, limit_price, stop_price, reduce_only=reduce_only)
    
    def place_take_profit_limit(self, symbol: str, side: str, quantity: float, stop_price: float,
                               limit_price: float, reduce_only: bool = True) -> Dict[str, Any]:
        """Place a take-profit limit order"""
        return self.place_stop_limit_order(symbol, side, quantity, limit_price, stop_price, reduce_only=reduce_only)
    
    def place_stop_market_order(self, symbol: str, side: str, quantity: float, 
                               stop_price: float, reduce_only: bool = False) -> Dict[str, Any]:
        """Place a stop market order"""
        try:
            # Validate basic parameters
            validated_params = self.validator.validate_market_order_params(symbol, side, quantity)
            
            # Get current market price for validation
            ticker = self.api_client.get_ticker_price(validated_params['symbol'])
            current_price = float(ticker['price'])
            
            # Validate stop price
            validated_stop_price = self.validator.validate_stop_price(stop_price, validated_params['side'], current_price)
            
            # Place the order
            order_response = self.api_client.place_stop_market_order(
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                stop_price=validated_stop_price,
                reduce_only=reduce_only
            )
            
            # Log order placement
            self.logger.log_order_placed(
                order_type="STOP_MARKET",
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                order_id=order_response.get('orderId'),
                stop_price=validated_stop_price,
                reduce_only=reduce_only,
                current_market_price=current_price
            )
            
            self.logger.info(f"Stop market order placed successfully: {validated_params['side']} {validated_params['quantity']} {validated_params['symbol']} (stop: {validated_stop_price})")
            
            return order_response
            
        except ValidationError as e:
            self.logger.log_error("VALIDATION_ERROR", str(e), symbol=symbol, side=side, quantity=quantity, stop_price=stop_price)
            raise
        except Exception as e:
            self.logger.log_error("ORDER_ERROR", str(e), symbol=symbol, side=side, quantity=quantity, stop_price=stop_price)
            raise
    
    def place_take_profit_market_order(self, symbol: str, side: str, quantity: float,
                                      stop_price: float, reduce_only: bool = True) -> Dict[str, Any]:
        """Place a take-profit market order"""
        try:
            # Validate basic parameters
            validated_params = self.validator.validate_market_order_params(symbol, side, quantity)
            
            # Get current market price for validation
            ticker = self.api_client.get_ticker_price(validated_params['symbol'])
            current_price = float(ticker['price'])
            
            # Validate stop price
            validated_stop_price = self.validator.validate_stop_price(stop_price, validated_params['side'], current_price)
            
            # Place the order
            order_response = self.api_client.place_take_profit_market_order(
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                stop_price=validated_stop_price,
                reduce_only=reduce_only
            )
            
            # Log order placement
            self.logger.log_order_placed(
                order_type="TAKE_PROFIT_MARKET",
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                order_id=order_response.get('orderId'),
                stop_price=validated_stop_price,
                reduce_only=reduce_only,
                current_market_price=current_price
            )
            
            self.logger.info(f"Take-profit market order placed successfully: {validated_params['side']} {validated_params['quantity']} {validated_params['symbol']} (stop: {validated_stop_price})")
            
            return order_response
            
        except ValidationError as e:
            self.logger.log_error("VALIDATION_ERROR", str(e), symbol=symbol, side=side, quantity=quantity, stop_price=stop_price)
            raise
        except Exception as e:
            self.logger.log_error("ORDER_ERROR", str(e), symbol=symbol, side=side, quantity=quantity, stop_price=stop_price)
            raise
    
    def place_take_profit_limit_order(self, symbol: str, side: str, quantity: float,
                                     price: float, stop_price: float, time_in_force: str = 'GTC',
                                     reduce_only: bool = True) -> Dict[str, Any]:
        """Place a take-profit limit order"""
        try:
            # Validate basic parameters
            validated_params = self.validator.validate_limit_order_params(symbol, side, quantity, price, time_in_force)
            
            # Get current market price for validation
            ticker = self.api_client.get_ticker_price(validated_params['symbol'])
            current_price = float(ticker['price'])
            
            # Validate stop price
            validated_stop_price = self.validator.validate_stop_price(stop_price, validated_params['side'], current_price)
            
            # Place the order
            order_response = self.api_client.place_take_profit_limit_order(
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                price=validated_params['price'],
                stop_price=validated_stop_price,
                time_in_force=validated_params['time_in_force'],
                reduce_only=reduce_only
            )
            
            # Log order placement
            self.logger.log_order_placed(
                order_type="TAKE_PROFIT_LIMIT",
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                price=validated_params['price'],
                order_id=order_response.get('orderId'),
                stop_price=validated_stop_price,
                time_in_force=validated_params['time_in_force'],
                reduce_only=reduce_only,
                current_market_price=current_price
            )
            
            self.logger.info(f"Take-profit limit order placed successfully: {validated_params['side']} {validated_params['quantity']} {validated_params['symbol']} at {validated_params['price']} (stop: {validated_stop_price})")
            
            return order_response
            
        except ValidationError as e:
            self.logger.log_error("VALIDATION_ERROR", str(e), symbol=symbol, side=side, quantity=quantity, price=price, stop_price=stop_price)
            raise
        except Exception as e:
            self.logger.log_error("ORDER_ERROR", str(e), symbol=symbol, side=side, quantity=quantity, price=price, stop_price=stop_price)
            raise
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get status of a stop-limit order"""
        try:
            order_status = self.api_client.get_order_status(symbol, order_id)
            
            # Log order status check
            self.logger.log_bot_action(
                "ORDER_STATUS_CHECK",
                symbol=symbol,
                order_id=order_id,
                status=order_status.get('status'),
                executed_qty=order_status.get('executedQty'),
                price=order_status.get('price'),
                stop_price=order_status.get('stopPrice'),
                order_type=order_status.get('type')
            )
            
            return order_status
            
        except Exception as e:
            self.logger.log_error("STATUS_CHECK_ERROR", str(e), symbol=symbol, order_id=order_id)
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel a stop-limit order"""
        try:
            cancel_response = self.api_client.cancel_order(symbol, order_id)
            
            # Log order cancellation
            self.logger.log_bot_action(
                "ORDER_CANCELLED",
                symbol=symbol,
                order_id=order_id,
                status=cancel_response.get('status')
            )
            
            self.logger.info(f"Stop-limit order {order_id} cancelled successfully for {symbol}")
            
            return cancel_response
            
        except Exception as e:
            self.logger.log_error("CANCEL_ERROR", str(e), symbol=symbol, order_id=order_id)
            raise

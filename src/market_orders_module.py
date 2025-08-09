"""
Market Orders module for Binance Futures Trading Bot
Handles market order placement and management
"""

from typing import Dict, Any, Optional
from .api_client import BinanceAPIClient
from .validators import TradingValidator, ValidationError
from .logger import BotLogger


class MarketOrderManager:
    """Manages market order operations"""
    
    def __init__(self, api_client: BinanceAPIClient, validator: TradingValidator, logger: BotLogger):
        self.api_client = api_client
        self.validator = validator
        self.logger = logger
        self.logger.info("MarketOrderManager initialized")
    
    def place_market_order(self, symbol: str, side: str, quantity: float, 
                          reduce_only: bool = False) -> Dict[str, Any]:
        """
        Place a market order
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            reduce_only: Whether this order should only reduce position
            
        Returns:
            Order response from Binance API
        """
        try:
            # Validate parameters
            validated_params = self.validator.validate_market_order_params(symbol, side, quantity)
            
            # Get current market price for logging
            ticker = self.api_client.get_ticker_price(validated_params['symbol'])
            current_price = float(ticker['price'])
            
            # Place the order
            order_response = self.api_client.place_market_order(
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                reduce_only=reduce_only
            )
            
            # Log order placement
            self.logger.log_order_placed(
                order_type="MARKET",
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                price=current_price,
                order_id=order_response.get('orderId'),
                reduce_only=reduce_only,
                estimated_price=current_price
            )
            
            self.logger.info(f"Market order placed successfully: {validated_params['side']} {validated_params['quantity']} {validated_params['symbol']} at ~{current_price}")
            
            return order_response
            
        except ValidationError as e:
            self.logger.log_error("VALIDATION_ERROR", str(e), symbol=symbol, side=side, quantity=quantity)
            raise
        except Exception as e:
            self.logger.log_error("ORDER_ERROR", str(e), symbol=symbol, side=side, quantity=quantity)
            raise
    
    def place_market_buy(self, symbol: str, quantity: float, reduce_only: bool = False) -> Dict[str, Any]:
        """Place a market buy order"""
        return self.place_market_order(symbol, 'BUY', quantity, reduce_only)
    
    def place_market_sell(self, symbol: str, quantity: float, reduce_only: bool = False) -> Dict[str, Any]:
        """Place a market sell order"""
        return self.place_market_order(symbol, 'SELL', quantity, reduce_only)
    
    def close_position_market(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Close a position using market order"""
        return self.place_market_order(symbol, side, quantity, reduce_only=True)
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get status of a market order"""
        try:
            order_status = self.api_client.get_order_status(symbol, order_id)
            
            # Log order status check
            self.logger.log_bot_action(
                "ORDER_STATUS_CHECK",
                symbol=symbol,
                order_id=order_id,
                status=order_status.get('status'),
                executed_qty=order_status.get('executedQty'),
                price=order_status.get('price')
            )
            
            return order_status
            
        except Exception as e:
            self.logger.log_error("STATUS_CHECK_ERROR", str(e), symbol=symbol, order_id=order_id)
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel a market order"""
        try:
            cancel_response = self.api_client.cancel_order(symbol, order_id)
            
            # Log order cancellation
            self.logger.log_bot_action(
                "ORDER_CANCELLED",
                symbol=symbol,
                order_id=order_id,
                status=cancel_response.get('status')
            )
            
            self.logger.info(f"Order {order_id} cancelled successfully for {symbol}")
            
            return cancel_response
            
        except Exception as e:
            self.logger.log_error("CANCEL_ERROR", str(e), symbol=symbol, order_id=order_id)
            raise
    
    def get_position_info(self, symbol: str) -> Dict[str, Any]:
        """Get current position information for a symbol"""
        try:
            positions = self.api_client.get_position_risk(symbol)
            
            if positions:
                position = positions[0]
                
                # Log position check
                self.logger.log_bot_action(
                    "POSITION_CHECK",
                    symbol=symbol,
                    position_amt=position.get('positionAmt'),
                    entry_price=position.get('entryPrice'),
                    mark_price=position.get('markPrice'),
                    unrealized_pnl=position.get('unRealizedProfit')
                )
                
                return position
            else:
                self.logger.warning(f"No position found for {symbol}")
                return {}
                
        except Exception as e:
            self.logger.log_error("POSITION_CHECK_ERROR", str(e), symbol=symbol)
            raise
    
    def calculate_quantity_from_usdt(self, symbol: str, usdt_amount: float) -> Dict[str, Any]:
        """Calculate quantity from USDT amount using current market price"""
        try:
            ticker = self.api_client.get_ticker_price(symbol)
            current_price = float(ticker['price'])
            
            quantity = usdt_amount / current_price
            
            # Validate the calculated quantity
            validated_quantity = self.validator.validate_quantity(quantity)
            
            self.logger.info(f"Calculated quantity: {usdt_amount} USDT = {validated_quantity} {symbol} at {current_price}")
            
            return {
                'quantity': validated_quantity,
                'price': current_price,
                'usdt_amount': usdt_amount
            }
            
        except Exception as e:
            self.logger.log_error("QUANTITY_CALCULATION_ERROR", str(e), symbol=symbol, usdt_amount=usdt_amount)
            raise
    
    def place_market_order_with_usdt(self, symbol: str, side: str, usdt_amount: float, 
                                    reduce_only: bool = False) -> Dict[str, Any]:
        """Place a market order using USDT amount instead of quantity"""
        try:
            quantity = self.calculate_quantity_from_usdt(symbol, usdt_amount)
            return self.place_market_order(symbol, side, quantity, reduce_only)
            
        except Exception as e:
            self.logger.log_error("USDT_ORDER_ERROR", str(e), symbol=symbol, side=side, usdt_amount=usdt_amount)
            raise

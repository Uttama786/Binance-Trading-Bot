"""
Limit Orders module for Binance Futures Trading Bot
Handles limit order placement and management
"""

from typing import Dict, Any, Optional
from .api_client import BinanceAPIClient
from .validators import TradingValidator, ValidationError
from .logger import BotLogger


class LimitOrderManager:
    """Manages limit order operations"""
    
    def __init__(self, api_client: BinanceAPIClient, validator: TradingValidator, logger: BotLogger):
        self.api_client = api_client
        self.validator = validator
        self.logger = logger
        self.logger.info("LimitOrderManager initialized")
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float,
                         time_in_force: str = 'GTC', reduce_only: bool = False) -> Dict[str, Any]:
        """
        Place a limit order
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Limit price
            time_in_force: Time in force ('GTC', 'IOC', 'FOK', 'GTX')
            reduce_only: Whether this order should only reduce position
            
        Returns:
            Order response from Binance API
        """
        try:
            # Validate parameters
            validated_params = self.validator.validate_limit_order_params(symbol, side, quantity, price, time_in_force)
            
            # Get current market price for comparison
            ticker = self.api_client.get_ticker_price(validated_params['symbol'])
            current_price = float(ticker['price'])
            
            # Validate price relative to current market price
            if validated_params['side'] == 'BUY' and validated_params['price'] >= current_price:
                self.logger.warning(f"Limit buy price ({validated_params['price']}) is above current market price ({current_price})")
            elif validated_params['side'] == 'SELL' and validated_params['price'] <= current_price:
                self.logger.warning(f"Limit sell price ({validated_params['price']}) is below current market price ({current_price})")
            
            # Place the order
            order_response = self.api_client.place_limit_order(
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                price=validated_params['price'],
                time_in_force=validated_params['time_in_force'],
                reduce_only=reduce_only
            )
            
            # Log order placement
            self.logger.log_order_placed(
                order_type="LIMIT",
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                price=validated_params['price'],
                order_id=order_response.get('orderId'),
                time_in_force=validated_params['time_in_force'],
                reduce_only=reduce_only,
                current_market_price=current_price
            )
            
            self.logger.info(f"Limit order placed successfully: {validated_params['side']} {validated_params['quantity']} {validated_params['symbol']} at {validated_params['price']}")
            
            return order_response
            
        except ValidationError as e:
            self.logger.log_error("VALIDATION_ERROR", str(e), symbol=symbol, side=side, quantity=quantity, price=price)
            raise
        except Exception as e:
            self.logger.log_error("ORDER_ERROR", str(e), symbol=symbol, side=side, quantity=quantity, price=price)
            raise
    
    def place_limit_buy(self, symbol: str, quantity: float, price: float,
                       time_in_force: str = 'GTC', reduce_only: bool = False) -> Dict[str, Any]:
        """Place a limit buy order"""
        return self.place_limit_order(symbol, 'BUY', quantity, price, time_in_force, reduce_only)
    
    def place_limit_sell(self, symbol: str, quantity: float, price: float,
                        time_in_force: str = 'GTC', reduce_only: bool = False) -> Dict[str, Any]:
        """Place a limit sell order"""
        return self.place_limit_order(symbol, 'SELL', quantity, price, time_in_force, reduce_only)
    
    def place_buy_below_market(self, symbol: str, quantity: float, price_offset_percent: float = 1.0) -> Dict[str, Any]:
        """Place a limit buy order below current market price"""
        try:
            ticker = self.api_client.get_ticker_price(symbol)
            current_price = float(ticker['price'])
            
            # Calculate buy price below market
            buy_price = current_price * (1 - price_offset_percent / 100)
            
            return self.place_limit_buy(symbol, quantity, buy_price)
            
        except Exception as e:
            self.logger.log_error("BUY_BELOW_MARKET_ERROR", str(e), symbol=symbol, quantity=quantity, offset=price_offset_percent)
            raise
    
    def place_sell_above_market(self, symbol: str, quantity: float, price_offset_percent: float = 1.0) -> Dict[str, Any]:
        """Place a limit sell order above current market price"""
        try:
            ticker = self.api_client.get_ticker_price(symbol)
            current_price = float(ticker['price'])
            
            # Calculate sell price above market
            sell_price = current_price * (1 + price_offset_percent / 100)
            
            return self.place_limit_sell(symbol, quantity, sell_price)
            
        except Exception as e:
            self.logger.log_error("SELL_ABOVE_MARKET_ERROR", str(e), symbol=symbol, quantity=quantity, offset=price_offset_percent)
            raise
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get status of a limit order"""
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
                order_type=order_status.get('type')
            )
            
            return order_status
            
        except Exception as e:
            self.logger.log_error("STATUS_CHECK_ERROR", str(e), symbol=symbol, order_id=order_id)
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel a limit order"""
        try:
            cancel_response = self.api_client.cancel_order(symbol, order_id)
            
            # Log order cancellation
            self.logger.log_bot_action(
                "ORDER_CANCELLED",
                symbol=symbol,
                order_id=order_id,
                status=cancel_response.get('status')
            )
            
            self.logger.info(f"Limit order {order_id} cancelled successfully for {symbol}")
            
            return cancel_response
            
        except Exception as e:
            self.logger.log_error("CANCEL_ERROR", str(e), symbol=symbol, order_id=order_id)
            raise
    
    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """Cancel all open orders for a symbol"""
        try:
            cancel_response = self.api_client.cancel_all_orders(symbol)
            
            # Log bulk cancellation
            self.logger.log_bot_action(
                "BULK_ORDER_CANCELLED",
                symbol=symbol,
                status=cancel_response.get('status')
            )
            
            self.logger.info(f"All open orders cancelled for {symbol}")
            
            return cancel_response
            
        except Exception as e:
            self.logger.log_error("BULK_CANCEL_ERROR", str(e), symbol=symbol)
            raise
    
    def get_open_orders(self, symbol: str = None) -> list:
        """Get all open orders"""
        try:
            open_orders = self.api_client.get_open_orders(symbol)
            
            # Log open orders check
            self.logger.log_bot_action(
                "OPEN_ORDERS_CHECK",
                symbol=symbol,
                count=len(open_orders)
            )
            
            return open_orders
            
        except Exception as e:
            self.logger.log_error("OPEN_ORDERS_ERROR", str(e), symbol=symbol)
            raise
    
    def modify_order(self, symbol: str, order_id: int, new_quantity: float = None, new_price: float = None) -> Dict[str, Any]:
        """Modify an existing limit order by canceling and replacing it"""
        try:
            # Get current order details
            current_order = self.api_client.get_order_status(symbol, order_id)
            
            if current_order['status'] != 'NEW':
                raise Exception(f"Cannot modify order {order_id} with status {current_order['status']}")
            
            # Cancel the current order
            self.cancel_order(symbol, order_id)
            
            # Place new order with modified parameters
            new_quantity = new_quantity or float(current_order['origQty'])
            new_price = new_price or float(current_order['price'])
            
            new_order = self.place_limit_order(
                symbol=symbol,
                side=current_order['side'],
                quantity=new_quantity,
                price=new_price,
                time_in_force=current_order['timeInForce'],
                reduce_only=current_order.get('reduceOnly', False)
            )
            
            # Log order modification
            self.logger.log_bot_action(
                "ORDER_MODIFIED",
                symbol=symbol,
                old_order_id=order_id,
                new_order_id=new_order.get('orderId'),
                old_quantity=current_order['origQty'],
                new_quantity=new_quantity,
                old_price=current_order['price'],
                new_price=new_price
            )
            
            self.logger.info(f"Order {order_id} modified successfully")
            
            return new_order
            
        except Exception as e:
            self.logger.log_error("MODIFY_ORDER_ERROR", str(e), symbol=symbol, order_id=order_id)
            raise
    
    def calculate_quantity_from_usdt(self, symbol: str, usdt_amount: float, price: float) -> Dict[str, Any]:
        """Calculate quantity from USDT amount and price"""
        try:
            quantity = usdt_amount / price
            
            # Validate the calculated quantity
            validated_quantity = self.validator.validate_quantity(quantity)
            
            self.logger.info(f"Calculated quantity: {usdt_amount} USDT = {validated_quantity} {symbol} at {price}")
            
            return {
                'quantity': validated_quantity,
                'price': price,
                'usdt_amount': usdt_amount
            }
            
        except Exception as e:
            self.logger.log_error("QUANTITY_CALCULATION_ERROR", str(e), symbol=symbol, usdt_amount=usdt_amount, price=price)
            raise
    
    def place_limit_order_with_usdt(self, symbol: str, side: str, usdt_amount: float, price: float,
                                   time_in_force: str = 'GTC', reduce_only: bool = False) -> Dict[str, Any]:
        """Place a limit order using USDT amount instead of quantity"""
        try:
            quantity = usdt_amount / price
            
            # Validate the calculated quantity
            validated_quantity = self.validator.validate_quantity(quantity)
            
            return self.place_limit_order(symbol, side, validated_quantity, price, time_in_force, reduce_only)
            
        except Exception as e:
            self.logger.log_error("USDT_LIMIT_ORDER_ERROR", str(e), symbol=symbol, side=side, usdt_amount=usdt_amount, price=price)
            raise

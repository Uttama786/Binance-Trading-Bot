"""
OCO (One-Cancels-the-Other) Orders module for Binance Futures Trading Bot
Handles OCO order placement and management
"""

from typing import Dict, Any, Optional
from ..api_client import BinanceAPIClient
from ..validators import TradingValidator, ValidationError
from ..logger import BotLogger


class OCOOrderManager:
    """Manages OCO (One-Cancels-the-Other) order operations"""
    
    def __init__(self, api_client: BinanceAPIClient, validator: TradingValidator, logger: BotLogger):
        self.api_client = api_client
        self.validator = validator
        self.logger = logger
        self.logger.info("OCOOrderManager initialized")
    
    def place_oco_order(self, symbol: str, side: str, quantity: float, price: float,
                       stop_price: float, stop_limit_price: float, 
                       stop_limit_time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        Place an OCO (One-Cancels-the-Other) order
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Take profit price
            stop_price: Stop loss price
            stop_limit_price: Stop limit price
            stop_limit_time_in_force: Time in force for stop limit order
            
        Returns:
            OCO order response from Binance API
        """
        try:
            # Validate basic parameters
            validated_params = self.validator.validate_limit_order_params(symbol, side, quantity, price)
            
            # Get current market price for validation
            ticker = self.api_client.get_ticker_price(validated_params['symbol'])
            current_price = float(ticker['price'])
            
            # Validate stop price and stop limit price
            validated_stop_price = self.validator.validate_price(stop_price)
            validated_stop_limit_price = self.validator.validate_price(stop_limit_price)
            
            # Validate time in force
            validated_time_in_force = self.validator.validate_time_in_force(stop_limit_time_in_force)
            
            # Validate price relationships based on side
            if validated_params['side'] == 'BUY':
                # For BUY orders: take profit should be above current price, stop loss below
                if validated_params['price'] <= current_price:
                    self.logger.warning(f"Take profit price ({validated_params['price']}) should be above current price ({current_price}) for BUY order")
                if validated_stop_price >= current_price:
                    self.logger.warning(f"Stop loss price ({validated_stop_price}) should be below current price ({current_price}) for BUY order")
                if validated_stop_limit_price >= validated_stop_price:
                    self.logger.warning(f"Stop limit price ({validated_stop_limit_price}) should be below stop price ({validated_stop_price}) for BUY order")
            else:  # SELL
                # For SELL orders: take profit should be below current price, stop loss above
                if validated_params['price'] >= current_price:
                    self.logger.warning(f"Take profit price ({validated_params['price']}) should be below current price ({current_price}) for SELL order")
                if validated_stop_price <= current_price:
                    self.logger.warning(f"Stop loss price ({validated_stop_price}) should be above current price ({current_price}) for SELL order")
                if validated_stop_limit_price <= validated_stop_price:
                    self.logger.warning(f"Stop limit price ({validated_stop_limit_price}) should be above stop price ({validated_stop_price}) for SELL order")
            
            # Place the OCO order
            order_response = self.api_client.place_oco_order(
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                price=validated_params['price'],
                stop_price=validated_stop_price,
                stop_limit_price=validated_stop_limit_price,
                stop_limit_time_in_force=validated_time_in_force
            )
            
            # Log order placement
            self.logger.log_order_placed(
                order_type="OCO",
                symbol=validated_params['symbol'],
                side=validated_params['side'],
                quantity=validated_params['quantity'],
                price=validated_params['price'],
                order_id=order_response.get('orderId'),
                stop_price=validated_stop_price,
                stop_limit_price=validated_stop_limit_price,
                stop_limit_time_in_force=validated_time_in_force,
                current_market_price=current_price
            )
            
            self.logger.info(f"OCO order placed successfully: {validated_params['side']} {validated_params['quantity']} {validated_params['symbol']} - TP: {validated_params['price']}, SL: {validated_stop_price}")
            
            return order_response
            
        except ValidationError as e:
            self.logger.log_error("VALIDATION_ERROR", str(e), symbol=symbol, side=side, quantity=quantity, 
                                price=price, stop_price=stop_price, stop_limit_price=stop_limit_price)
            raise
        except Exception as e:
            self.logger.log_error("ORDER_ERROR", str(e), symbol=symbol, side=side, quantity=quantity, 
                                price=price, stop_price=stop_price, stop_limit_price=stop_limit_price)
            raise
    
    def place_oco_buy(self, symbol: str, quantity: float, take_profit_price: float,
                     stop_loss_price: float, stop_limit_price: float, 
                     stop_limit_time_in_force: str = 'GTC') -> Dict[str, Any]:
        """Place an OCO buy order with take profit and stop loss"""
        return self.place_oco_order(symbol, 'BUY', quantity, take_profit_price, 
                                   stop_loss_price, stop_limit_price, stop_limit_time_in_force)
    
    def place_oco_sell(self, symbol: str, quantity: float, take_profit_price: float,
                      stop_loss_price: float, stop_limit_price: float, 
                      stop_limit_time_in_force: str = 'GTC') -> Dict[str, Any]:
        """Place an OCO sell order with take profit and stop loss"""
        return self.place_oco_order(symbol, 'SELL', quantity, take_profit_price, 
                                   stop_loss_price, stop_limit_price, stop_limit_time_in_force)
    
    def place_oco_with_percentages(self, symbol: str, side: str, quantity: float, 
                                  take_profit_percent: float, stop_loss_percent: float,
                                  stop_limit_offset_percent: float = 0.1) -> Dict[str, Any]:
        """
        Place an OCO order using percentage-based take profit and stop loss
        
        Args:
            symbol: Trading symbol
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            take_profit_percent: Take profit percentage from current price
            stop_loss_percent: Stop loss percentage from current price
            stop_limit_offset_percent: Offset for stop limit price from stop price
        """
        try:
            # Get current market price
            ticker = self.api_client.get_ticker_price(symbol)
            current_price = float(ticker['price'])
            
            # Calculate prices based on percentages
            if side == 'BUY':
                take_profit_price = current_price * (1 + take_profit_percent / 100)
                stop_loss_price = current_price * (1 - stop_loss_percent / 100)
                stop_limit_price = stop_loss_price * (1 - stop_limit_offset_percent / 100)
            else:  # SELL
                take_profit_price = current_price * (1 - take_profit_percent / 100)
                stop_loss_price = current_price * (1 + stop_loss_percent / 100)
                stop_limit_price = stop_loss_price * (1 + stop_limit_offset_percent / 100)
            
            # Validate calculated prices
            validated_take_profit = self.validator.validate_price(take_profit_price)
            validated_stop_loss = self.validator.validate_price(stop_loss_price)
            validated_stop_limit = self.validator.validate_price(stop_limit_price)
            
            # Place OCO order
            return self.place_oco_order(symbol, side, quantity, validated_take_profit, 
                                       validated_stop_loss, validated_stop_limit)
            
        except Exception as e:
            self.logger.log_error("PERCENTAGE_OCO_ERROR", str(e), symbol=symbol, side=side, 
                                quantity=quantity, tp_percent=take_profit_percent, sl_percent=stop_loss_percent)
            raise
    
    def place_oco_buy_with_percentages(self, symbol: str, quantity: float, 
                                      take_profit_percent: float, stop_loss_percent: float,
                                      stop_limit_offset_percent: float = 0.1) -> Dict[str, Any]:
        """Place an OCO buy order with percentage-based take profit and stop loss"""
        return self.place_oco_with_percentages(symbol, 'BUY', quantity, take_profit_percent, 
                                              stop_loss_percent, stop_limit_offset_percent)
    
    def place_oco_sell_with_percentages(self, symbol: str, quantity: float, 
                                       take_profit_percent: float, stop_loss_percent: float,
                                       stop_limit_offset_percent: float = 0.1) -> Dict[str, Any]:
        """Place an OCO sell order with percentage-based take profit and stop loss"""
        return self.place_oco_with_percentages(symbol, 'SELL', quantity, take_profit_percent, 
                                              stop_loss_percent, stop_limit_offset_percent)
    
    def get_oco_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get status of an OCO order"""
        try:
            # Note: Binance Futures doesn't have a direct OCO order status endpoint
            # We'll check the individual orders that make up the OCO
            open_orders = self.api_client.get_open_orders(symbol)
            
            oco_orders = [order for order in open_orders if order.get('orderId') == order_id]
            
            if oco_orders:
                order_status = oco_orders[0]
                
                # Log order status check
                self.logger.log_bot_action(
                    "OCO_ORDER_STATUS_CHECK",
                    symbol=symbol,
                    order_id=order_id,
                    status=order_status.get('status'),
                    executed_qty=order_status.get('executedQty'),
                    price=order_status.get('price'),
                    order_type=order_status.get('type')
                )
                
                return order_status
            else:
                self.logger.warning(f"OCO order {order_id} not found in open orders for {symbol}")
                return {}
                
        except Exception as e:
            self.logger.log_error("OCO_STATUS_CHECK_ERROR", str(e), symbol=symbol, order_id=order_id)
            raise
    
    def cancel_oco_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an OCO order"""
        try:
            cancel_response = self.api_client.cancel_order(symbol, order_id)
            
            # Log order cancellation
            self.logger.log_bot_action(
                "OCO_ORDER_CANCELLED",
                symbol=symbol,
                order_id=order_id,
                status=cancel_response.get('status')
            )
            
            self.logger.info(f"OCO order {order_id} cancelled successfully for {symbol}")
            
            return cancel_response
            
        except Exception as e:
            self.logger.log_error("OCO_CANCEL_ERROR", str(e), symbol=symbol, order_id=order_id)
            raise
    
    def get_open_oco_orders(self, symbol: str = None) -> list:
        """Get all open OCO orders"""
        try:
            open_orders = self.api_client.get_open_orders(symbol)
            
            # Filter for OCO-related orders (take profit and stop loss orders)
            oco_orders = []
            for order in open_orders:
                if order.get('type') in ['TAKE_PROFIT_LIMIT', 'STOP_LIMIT', 'TAKE_PROFIT_MARKET', 'STOP_MARKET']:
                    oco_orders.append(order)
            
            # Log OCO orders check
            self.logger.log_bot_action(
                "OPEN_OCO_ORDERS_CHECK",
                symbol=symbol,
                count=len(oco_orders)
            )
            
            return oco_orders
            
        except Exception as e:
            self.logger.log_error("OPEN_OCO_ORDERS_ERROR", str(e), symbol=symbol)
            raise

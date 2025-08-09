import time
import math
from typing import Dict, Any, Optional, List, Tuple
from ..api_client import BinanceAPIClient
from ..validators import TradingValidator, ValidationError
from ..logger import BotLogger


class GridOrderManager:
    """
    Grid Order Manager
    
    Implements automated buy-low/sell-high strategies within a specified price range.
    Places multiple limit orders at regular price intervals to capture price movements.
    """
    
    def __init__(self, api_client: BinanceAPIClient, validator: TradingValidator, logger: BotLogger):
        self.api_client = api_client
        self.validator = validator
        self.logger = logger
        self.logger.info("GridOrderManager initialized")
    
    def place_grid_order(self, symbol: str, side: str, total_quantity: float,
                         upper_price: float, lower_price: float, num_grids: int,
                         grid_type: str = 'ARITHMETIC', time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        Place a grid order with multiple limit orders at regular price intervals.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL' (or 'BOTH' for neutral grid)
            total_quantity: Total quantity to distribute across grids
            upper_price: Upper price limit for the grid
            lower_price: Lower price limit for the grid
            num_grids: Number of grid levels
            grid_type: 'ARITHMETIC' or 'GEOMETRIC'
            time_in_force: Time in force for limit orders
        
        Returns:
            Dict containing grid order details and placed orders
        """
        try:
            # Validate inputs
            symbol = self.validator.validate_symbol(symbol)
            side = self.validator.validate_side(side)
            total_quantity = self.validator.validate_quantity(total_quantity)
            upper_price = self.validator.validate_price(upper_price)
            lower_price = self.validator.validate_price(lower_price)
            
            if upper_price <= lower_price:
                raise ValidationError("Upper price must be greater than lower price")
            
            if num_grids < 2:
                raise ValidationError("Number of grids must be at least 2")
            
            if num_grids > 50:
                raise ValidationError("Number of grids cannot exceed 50")
            
            if grid_type not in ['ARITHMETIC', 'GEOMETRIC']:
                raise ValidationError(f"Invalid grid type: {grid_type}. Must be 'ARITHMETIC' or 'GEOMETRIC'")
            
            # Calculate grid prices and quantities
            grid_prices = self._calculate_grid_prices(lower_price, upper_price, num_grids, grid_type)
            grid_quantities = self._calculate_grid_quantities(total_quantity, num_grids, side)
            
            # Log grid order start
            self.logger.log_order_placed(
                order_type="GRID",
                symbol=symbol,
                side=side,
                quantity=total_quantity,
                price=None,
                extra_data={
                    "upper_price": upper_price,
                    "lower_price": lower_price,
                    "num_grids": num_grids,
                    "grid_type": grid_type,
                    "grid_prices": grid_prices,
                    "grid_quantities": grid_quantities
                }
            )
            
            # Place grid orders
            placed_orders = []
            failed_orders = []
            
            for i, (price, quantity) in enumerate(zip(grid_prices, grid_quantities)):
                try:
                    # Determine order side for each grid level
                    if side == 'BOTH':
                        # For neutral grid, alternate buy/sell orders
                        grid_side = 'BUY' if i % 2 == 0 else 'SELL'
                    else:
                        grid_side = side
                    
                    # Place limit order
                    order_result = self.api_client.place_limit_order(
                        symbol=symbol,
                        side=grid_side,
                        quantity=quantity,
                        price=price,
                        time_in_force=time_in_force
                    )
                    
                    placed_orders.append({
                        "grid_index": i + 1,
                        "price": price,
                        "quantity": quantity,
                        "side": grid_side,
                        "order_id": order_result.get('orderId'),
                        "status": order_result.get('status')
                    })
                    
                    self.logger.info(f"Grid order {i+1}/{num_grids} placed successfully", extra_data={
                        "grid_index": i + 1,
                        "price": price,
                        "quantity": quantity,
                        "side": grid_side,
                        "order_id": order_result.get('orderId')
                    })
                    
                except Exception as e:
                    failed_orders.append({
                        "grid_index": i + 1,
                        "price": price,
                        "quantity": quantity,
                        "error": str(e)
                    })
                    
                    self.logger.log_error(
                        error_type="GRID_ORDER_FAILED",
                        message=f"Failed to place grid order {i+1}",
                        extra_data={
                            "grid_index": i + 1,
                            "price": price,
                            "quantity": quantity,
                            "error": str(e)
                        }
                    )
                
                # Small delay between orders to avoid rate limiting
                time.sleep(0.1)
            
            result = {
                "symbol": symbol,
                "side": side,
                "total_quantity": total_quantity,
                "upper_price": upper_price,
                "lower_price": lower_price,
                "num_grids": num_grids,
                "grid_type": grid_type,
                "placed_orders": placed_orders,
                "failed_orders": failed_orders,
                "success_rate": len(placed_orders) / num_grids * 100,
                "grid_prices": grid_prices,
                "grid_quantities": grid_quantities
            }
            
            self.logger.info("Grid order completed", extra_data=result)
            return result
            
        except Exception as e:
            self.logger.log_error(
                error_type="GRID_ORDER_FAILED",
                message=f"Failed to place grid order: {str(e)}",
                extra_data={
                    "symbol": symbol,
                    "side": side,
                    "total_quantity": total_quantity,
                    "upper_price": upper_price,
                    "lower_price": lower_price,
                    "num_grids": num_grids
                }
            )
            raise
    
    def place_martingale_grid(self, symbol: str, side: str, base_quantity: float,
                              upper_price: float, lower_price: float, num_grids: int,
                              multiplier: float = 2.0, grid_type: str = 'ARITHMETIC') -> Dict[str, Any]:
        """
        Place a Martingale grid order with exponentially increasing quantities.
        
        Args:
            symbol: Trading symbol
            side: 'BUY' or 'SELL'
            base_quantity: Base quantity for the first grid
            upper_price: Upper price limit
            lower_price: Lower price limit
            num_grids: Number of grid levels
            multiplier: Quantity multiplier for each grid level
            grid_type: 'ARITHMETIC' or 'GEOMETRIC'
        
        Returns:
            Dict containing Martingale grid order details
        """
        try:
            # Validate inputs
            symbol = self.validator.validate_symbol(symbol)
            side = self.validator.validate_side(side)
            base_quantity = self.validator.validate_quantity(base_quantity)
            upper_price = self.validator.validate_price(upper_price)
            lower_price = self.validator.validate_price(lower_price)
            
            if upper_price <= lower_price:
                raise ValidationError("Upper price must be greater than lower price")
            
            if multiplier <= 1.0:
                raise ValidationError("Multiplier must be greater than 1.0")
            
            if num_grids < 2:
                raise ValidationError("Number of grids must be at least 2")
            
            # Calculate grid prices
            grid_prices = self._calculate_grid_prices(lower_price, upper_price, num_grids, grid_type)
            
            # Calculate Martingale quantities
            grid_quantities = []
            current_quantity = base_quantity
            for i in range(num_grids):
                grid_quantities.append(current_quantity)
                current_quantity *= multiplier
            
            # Log Martingale grid order start
            self.logger.log_order_placed(
                order_type="MARTINGALE_GRID",
                symbol=symbol,
                side=side,
                quantity=sum(grid_quantities),
                price=None,
                extra_data={
                    "upper_price": upper_price,
                    "lower_price": lower_price,
                    "num_grids": num_grids,
                    "grid_type": grid_type,
                    "base_quantity": base_quantity,
                    "multiplier": multiplier,
                    "grid_prices": grid_prices,
                    "grid_quantities": grid_quantities
                }
            )
            
            # Place grid orders
            placed_orders = []
            failed_orders = []
            
            for i, (price, quantity) in enumerate(zip(grid_prices, grid_quantities)):
                try:
                    # Place limit order
                    order_result = self.api_client.place_limit_order(
                        symbol=symbol,
                        side=side,
                        quantity=quantity,
                        price=price,
                        time_in_force='GTC'
                    )
                    
                    placed_orders.append({
                        "grid_index": i + 1,
                        "price": price,
                        "quantity": quantity,
                        "side": side,
                        "order_id": order_result.get('orderId'),
                        "status": order_result.get('status')
                    })
                    
                    self.logger.info(f"Martingale grid order {i+1}/{num_grids} placed successfully", extra_data={
                        "grid_index": i + 1,
                        "price": price,
                        "quantity": quantity,
                        "multiplier": multiplier ** i
                    })
                    
                except Exception as e:
                    failed_orders.append({
                        "grid_index": i + 1,
                        "price": price,
                        "quantity": quantity,
                        "error": str(e)
                    })
                    
                    self.logger.log_error(
                        error_type="MARTINGALE_GRID_FAILED",
                        message=f"Failed to place Martingale grid order {i+1}",
                        extra_data={
                            "grid_index": i + 1,
                            "price": price,
                            "quantity": quantity,
                            "error": str(e)
                        }
                    )
                
                time.sleep(0.1)
            
            result = {
                "symbol": symbol,
                "side": side,
                "base_quantity": base_quantity,
                "total_quantity": sum(grid_quantities),
                "upper_price": upper_price,
                "lower_price": lower_price,
                "num_grids": num_grids,
                "grid_type": grid_type,
                "multiplier": multiplier,
                "placed_orders": placed_orders,
                "failed_orders": failed_orders,
                "success_rate": len(placed_orders) / num_grids * 100,
                "grid_prices": grid_prices,
                "grid_quantities": grid_quantities
            }
            
            self.logger.info("Martingale grid order completed", extra_data=result)
            return result
            
        except Exception as e:
            self.logger.log_error(
                error_type="MARTINGALE_GRID_FAILED",
                message=f"Failed to place Martingale grid order: {str(e)}",
                extra_data={
                    "symbol": symbol,
                    "side": side,
                    "base_quantity": base_quantity,
                    "multiplier": multiplier
                }
            )
            raise
    
    def place_dca_grid(self, symbol: str, side: str, total_usdt: float,
                       upper_price: float, lower_price: float, num_grids: int,
                       grid_type: str = 'ARITHMETIC') -> Dict[str, Any]:
        """
        Place a Dollar-Cost Averaging (DCA) grid order.
        
        Args:
            symbol: Trading symbol
            side: 'BUY' or 'SELL'
            total_usdt: Total USDT amount to invest
            upper_price: Upper price limit
            lower_price: Lower price limit
            num_grids: Number of grid levels
            grid_type: 'ARITHMETIC' or 'GEOMETRIC'
        
        Returns:
            Dict containing DCA grid order details
        """
        try:
            # Validate inputs
            symbol = self.validator.validate_symbol(symbol)
            side = self.validator.validate_side(side)
            
            if total_usdt <= 0:
                raise ValidationError("Total USDT amount must be positive")
            
            upper_price = self.validator.validate_price(upper_price)
            lower_price = self.validator.validate_price(lower_price)
            
            if upper_price <= lower_price:
                raise ValidationError("Upper price must be greater than lower price")
            
            # Calculate grid prices
            grid_prices = self._calculate_grid_prices(lower_price, upper_price, num_grids, grid_type)
            
            # Calculate USDT per grid
            usdt_per_grid = total_usdt / num_grids
            
            # Calculate quantities based on USDT amount
            grid_quantities = []
            for price in grid_prices:
                quantity = usdt_per_grid / price
                grid_quantities.append(quantity)
            
            # Log DCA grid order start
            self.logger.log_order_placed(
                order_type="DCA_GRID",
                symbol=symbol,
                side=side,
                quantity=sum(grid_quantities),
                price=None,
                extra_data={
                    "total_usdt": total_usdt,
                    "upper_price": upper_price,
                    "lower_price": lower_price,
                    "num_grids": num_grids,
                    "grid_type": grid_type,
                    "usdt_per_grid": usdt_per_grid,
                    "grid_prices": grid_prices,
                    "grid_quantities": grid_quantities
                }
            )
            
            # Place grid orders
            placed_orders = []
            failed_orders = []
            
            for i, (price, quantity) in enumerate(zip(grid_prices, grid_quantities)):
                try:
                    # Place limit order
                    order_result = self.api_client.place_limit_order(
                        symbol=symbol,
                        side=side,
                        quantity=quantity,
                        price=price,
                        time_in_force='GTC'
                    )
                    
                    placed_orders.append({
                        "grid_index": i + 1,
                        "price": price,
                        "quantity": quantity,
                        "usdt_amount": usdt_per_grid,
                        "side": side,
                        "order_id": order_result.get('orderId'),
                        "status": order_result.get('status')
                    })
                    
                    self.logger.info(f"DCA grid order {i+1}/{num_grids} placed successfully", extra_data={
                        "grid_index": i + 1,
                        "price": price,
                        "quantity": quantity,
                        "usdt_amount": usdt_per_grid
                    })
                    
                except Exception as e:
                    failed_orders.append({
                        "grid_index": i + 1,
                        "price": price,
                        "quantity": quantity,
                        "error": str(e)
                    })
                    
                    self.logger.log_error(
                        error_type="DCA_GRID_FAILED",
                        message=f"Failed to place DCA grid order {i+1}",
                        extra_data={
                            "grid_index": i + 1,
                            "price": price,
                            "quantity": quantity,
                            "error": str(e)
                        }
                    )
                
                time.sleep(0.1)
            
            result = {
                "symbol": symbol,
                "side": side,
                "total_usdt": total_usdt,
                "total_quantity": sum(grid_quantities),
                "upper_price": upper_price,
                "lower_price": lower_price,
                "num_grids": num_grids,
                "grid_type": grid_type,
                "usdt_per_grid": usdt_per_grid,
                "placed_orders": placed_orders,
                "failed_orders": failed_orders,
                "success_rate": len(placed_orders) / num_grids * 100,
                "grid_prices": grid_prices,
                "grid_quantities": grid_quantities
            }
            
            self.logger.info("DCA grid order completed", extra_data=result)
            return result
            
        except Exception as e:
            self.logger.log_error(
                error_type="DCA_GRID_FAILED",
                message=f"Failed to place DCA grid order: {str(e)}",
                extra_data={
                    "symbol": symbol,
                    "side": side,
                    "total_usdt": total_usdt
                }
            )
            raise
    
    def _calculate_grid_prices(self, lower_price: float, upper_price: float, 
                              num_grids: int, grid_type: str) -> List[float]:
        """
        Calculate grid prices based on grid type.
        
        Args:
            lower_price: Lower price limit
            upper_price: Upper price limit
            num_grids: Number of grid levels
            grid_type: 'ARITHMETIC' or 'GEOMETRIC'
        
        Returns:
            List of grid prices
        """
        if grid_type == 'ARITHMETIC':
            # Equal price intervals
            price_step = (upper_price - lower_price) / (num_grids - 1)
            return [lower_price + i * price_step for i in range(num_grids)]
        
        elif grid_type == 'GEOMETRIC':
            # Equal percentage intervals
            ratio = (upper_price / lower_price) ** (1 / (num_grids - 1))
            return [lower_price * (ratio ** i) for i in range(num_grids)]
        
        else:
            return [lower_price + i * (upper_price - lower_price) / (num_grids - 1) for i in range(num_grids)]
    
    def _calculate_grid_quantities(self, total_quantity: float, num_grids: int, side: str) -> List[float]:
        """
        Calculate quantities for each grid level.
        
        Args:
            total_quantity: Total quantity to distribute
            num_grids: Number of grid levels
            side: Order side
        
        Returns:
            List of grid quantities
        """
        if side == 'BOTH':
            # For neutral grid, distribute quantity evenly
            return [total_quantity / num_grids] * num_grids
        else:
            # For single-side grid, distribute quantity evenly
            return [total_quantity / num_grids] * num_grids
    
    def get_grid_status(self, symbol: str) -> Dict[str, Any]:
        """
        Get status of all grid orders for a symbol.
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Dict containing grid order status
        """
        try:
            # Get all open orders for the symbol
            open_orders = self.api_client.get_open_orders(symbol=symbol)
            
            # Filter grid orders (this is a simplified approach)
            grid_orders = []
            for order in open_orders:
                if order.get('type') == 'LIMIT':
                    grid_orders.append(order)
            
            result = {
                "symbol": symbol,
                "total_grid_orders": len(grid_orders),
                "grid_orders": grid_orders
            }
            
            self.logger.info(f"Retrieved grid status for {symbol}", extra_data=result)
            return result
            
        except Exception as e:
            self.logger.log_error(
                error_type="GRID_STATUS_FAILED",
                message=f"Failed to get grid status: {str(e)}",
                extra_data={"symbol": symbol}
            )
            raise
    
    def cancel_grid_orders(self, symbol: str) -> Dict[str, Any]:
        """
        Cancel all grid orders for a symbol.
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Dict containing cancellation results
        """
        try:
            # Cancel all open orders for the symbol
            result = self.api_client.cancel_all_open_orders(symbol=symbol)
            
            self.logger.info(f"Cancelled all grid orders for {symbol}", extra_data=result)
            return result
            
        except Exception as e:
            self.logger.log_error(
                error_type="GRID_CANCEL_FAILED",
                message=f"Failed to cancel grid orders: {str(e)}",
                extra_data={"symbol": symbol}
            )
            raise

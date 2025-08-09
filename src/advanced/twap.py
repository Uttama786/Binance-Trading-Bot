import time
import math
from typing import Dict, Any, Optional, List
from ..api_client import BinanceAPIClient
from ..validators import TradingValidator, ValidationError
from ..logger import BotLogger


class TWAPOrderManager:
    """
    Time-Weighted Average Price (TWAP) Order Manager
    
    Splits large orders into smaller chunks executed over a specified time period
    to minimize market impact and achieve better average prices.
    """
    
    def __init__(self, api_client: BinanceAPIClient, validator: TradingValidator, logger: BotLogger):
        self.api_client = api_client
        self.validator = validator
        self.logger = logger
        self.logger.info("TWAPOrderManager initialized")
    
    def place_twap_order(self, symbol: str, side: str, total_quantity: float,
                         duration_minutes: int, num_chunks: int = 10,
                         order_type: str = 'MARKET', price: Optional[float] = None,
                         time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        Place a TWAP order that splits the total quantity into chunks over time.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            total_quantity: Total quantity to trade
            duration_minutes: Total duration in minutes
            num_chunks: Number of chunks to split the order into
            order_type: 'MARKET' or 'LIMIT'
            price: Limit price (required for LIMIT orders)
            time_in_force: Time in force for limit orders ('GTC', 'IOC', 'FOK')
        
        Returns:
            Dict containing TWAP order details and chunk information
        """
        try:
            # Validate inputs
            symbol = self.validator.validate_symbol(symbol)
            side = self.validator.validate_side(side)
            total_quantity = self.validator.validate_quantity(total_quantity)
            
            if order_type not in ['MARKET', 'LIMIT']:
                raise ValidationError(f"Invalid order type: {order_type}. Must be 'MARKET' or 'LIMIT'")
            
            if order_type == 'LIMIT' and price is None:
                raise ValidationError("Price is required for LIMIT orders")
            
            if order_type == 'LIMIT':
                price = self.validator.validate_price(price)
            
            if duration_minutes < 1:
                raise ValidationError("Duration must be at least 1 minute")
            
            if num_chunks < 2:
                raise ValidationError("Number of chunks must be at least 2")
            
            if num_chunks > 100:
                raise ValidationError("Number of chunks cannot exceed 100")
            
            # Calculate chunk size and interval
            chunk_quantity = total_quantity / num_chunks
            interval_seconds = (duration_minutes * 60) / (num_chunks - 1)
            
            # Validate chunk quantity
            chunk_quantity = self.validator.validate_quantity(chunk_quantity)
            
            # Log TWAP order start
            self.logger.log_order_placed(
                order_type="TWAP",
                symbol=symbol,
                side=side,
                quantity=total_quantity,
                price=price,
                extra_data={
                    "duration_minutes": duration_minutes,
                    "num_chunks": num_chunks,
                    "chunk_quantity": chunk_quantity,
                    "interval_seconds": interval_seconds,
                    "twap_order_type": order_type
                }
            )
            
            # Execute chunks
            executed_chunks = []
            failed_chunks = []
            total_executed = 0.0
            total_cost = 0.0
            
            for i in range(num_chunks):
                try:
                    # Place individual chunk order
                    if order_type == 'MARKET':
                        chunk_result = self.api_client.place_market_order(
                            symbol=symbol,
                            side=side,
                            quantity=chunk_quantity
                        )
                    else:  # LIMIT
                        chunk_result = self.api_client.place_limit_order(
                            symbol=symbol,
                            side=side,
                            quantity=chunk_quantity,
                            price=price,
                            time_in_force=time_in_force
                        )
                    
                    executed_chunks.append({
                        "chunk_index": i + 1,
                        "quantity": chunk_quantity,
                        "order_id": chunk_result.get('orderId'),
                        "status": chunk_result.get('status'),
                        "executed_qty": float(chunk_result.get('executedQty', 0)),
                        "cummulative_quote_qty": float(chunk_result.get('cummulativeQuoteQty', 0))
                    })
                    
                    total_executed += float(chunk_result.get('executedQty', 0))
                    total_cost += float(chunk_result.get('cummulativeQuoteQty', 0))
                    
                    self.logger.info(f"TWAP chunk {i+1}/{num_chunks} executed successfully", extra_data={
                        "chunk_index": i + 1,
                        "order_id": chunk_result.get('orderId'),
                        "executed_qty": chunk_result.get('executedQty'),
                        "status": chunk_result.get('status')
                    })
                    
                except Exception as e:
                    failed_chunks.append({
                        "chunk_index": i + 1,
                        "quantity": chunk_quantity,
                        "error": str(e)
                    })
                    
                    self.logger.log_error(
                        error_type="TWAP_CHUNK_FAILED",
                        message=f"Failed to execute TWAP chunk {i+1}",
                        extra_data={
                            "chunk_index": i + 1,
                            "quantity": chunk_quantity,
                            "error": str(e)
                        }
                    )
                
                # Wait for next chunk (except for the last chunk)
                if i < num_chunks - 1:
                    time.sleep(interval_seconds)
            
            # Calculate average price
            avg_price = total_cost / total_executed if total_executed > 0 else 0
            
            result = {
                "symbol": symbol,
                "side": side,
                "total_quantity": total_quantity,
                "duration_minutes": duration_minutes,
                "num_chunks": num_chunks,
                "order_type": order_type,
                "price": price,
                "total_executed": total_executed,
                "total_cost": total_cost,
                "average_price": avg_price,
                "executed_chunks": executed_chunks,
                "failed_chunks": failed_chunks,
                "success_rate": len(executed_chunks) / num_chunks * 100
            }
            
            self.logger.info("TWAP order completed", extra_data=result)
            return result
            
        except Exception as e:
            self.logger.log_error(
                error_type="TWAP_ORDER_FAILED",
                message=f"Failed to place TWAP order: {str(e)}",
                extra_data={
                    "symbol": symbol,
                    "side": side,
                    "total_quantity": total_quantity,
                    "duration_minutes": duration_minutes,
                    "num_chunks": num_chunks
                }
            )
            raise
    
    def place_twap_with_volume_profile(self, symbol: str, side: str, total_quantity: float,
                                       duration_minutes: int, volume_profile: str = 'UNIFORM',
                                       order_type: str = 'MARKET', price: Optional[float] = None) -> Dict[str, Any]:
        """
        Place a TWAP order with different volume profiles.
        
        Args:
            symbol: Trading symbol
            side: 'BUY' or 'SELL'
            total_quantity: Total quantity to trade
            duration_minutes: Total duration in minutes
            volume_profile: 'UNIFORM', 'FRONT_LOADED', 'BACK_LOADED', 'MIDDLE_LOADED'
            order_type: 'MARKET' or 'LIMIT'
            price: Limit price (for LIMIT orders)
        
        Returns:
            Dict containing TWAP order details
        """
        try:
            # Validate inputs
            symbol = self.validator.validate_symbol(symbol)
            side = self.validator.validate_side(side)
            total_quantity = self.validator.validate_quantity(total_quantity)
            
            if volume_profile not in ['UNIFORM', 'FRONT_LOADED', 'BACK_LOADED', 'MIDDLE_LOADED']:
                raise ValidationError(f"Invalid volume profile: {volume_profile}")
            
            # Calculate chunk quantities based on volume profile
            num_chunks = 10
            chunk_quantities = self._calculate_volume_profile(total_quantity, num_chunks, volume_profile)
            
            # Calculate intervals
            interval_seconds = (duration_minutes * 60) / (num_chunks - 1)
            
            # Log TWAP order start with volume profile
            self.logger.log_order_placed(
                order_type="TWAP_VOLUME_PROFILE",
                symbol=symbol,
                side=side,
                quantity=total_quantity,
                price=price,
                extra_data={
                    "duration_minutes": duration_minutes,
                    "num_chunks": num_chunks,
                    "volume_profile": volume_profile,
                    "chunk_quantities": chunk_quantities,
                    "interval_seconds": interval_seconds
                }
            )
            
            # Execute chunks with varying quantities
            executed_chunks = []
            failed_chunks = []
            total_executed = 0.0
            total_cost = 0.0
            
            for i, chunk_qty in enumerate(chunk_quantities):
                try:
                    # Validate chunk quantity
                    chunk_qty = self.validator.validate_quantity(chunk_qty)
                    
                    # Place individual chunk order
                    if order_type == 'MARKET':
                        chunk_result = self.api_client.place_market_order(
                            symbol=symbol,
                            side=side,
                            quantity=chunk_qty
                        )
                    else:  # LIMIT
                        chunk_result = self.api_client.place_limit_order(
                            symbol=symbol,
                            side=side,
                            quantity=chunk_qty,
                            price=price,
                            time_in_force='GTC'
                        )
                    
                    executed_chunks.append({
                        "chunk_index": i + 1,
                        "quantity": chunk_qty,
                        "order_id": chunk_result.get('orderId'),
                        "status": chunk_result.get('status'),
                        "executed_qty": float(chunk_result.get('executedQty', 0)),
                        "cummulative_quote_qty": float(chunk_result.get('cummulativeQuoteQty', 0))
                    })
                    
                    total_executed += float(chunk_result.get('executedQty', 0))
                    total_cost += float(chunk_result.get('cummulativeQuoteQty', 0))
                    
                except Exception as e:
                    failed_chunks.append({
                        "chunk_index": i + 1,
                        "quantity": chunk_qty,
                        "error": str(e)
                    })
                    
                    self.logger.log_error(
                        error_type="TWAP_CHUNK_FAILED",
                        message=f"Failed to execute TWAP chunk {i+1}",
                        extra_data={
                            "chunk_index": i + 1,
                            "quantity": chunk_qty,
                            "error": str(e)
                        }
                    )
                
                # Wait for next chunk (except for the last chunk)
                if i < num_chunks - 1:
                    time.sleep(interval_seconds)
            
            # Calculate average price
            avg_price = total_cost / total_executed if total_executed > 0 else 0
            
            result = {
                "symbol": symbol,
                "side": side,
                "total_quantity": total_quantity,
                "duration_minutes": duration_minutes,
                "num_chunks": num_chunks,
                "volume_profile": volume_profile,
                "order_type": order_type,
                "price": price,
                "total_executed": total_executed,
                "total_cost": total_cost,
                "average_price": avg_price,
                "executed_chunks": executed_chunks,
                "failed_chunks": failed_chunks,
                "success_rate": len(executed_chunks) / num_chunks * 100
            }
            
            self.logger.info("TWAP order with volume profile completed", extra_data=result)
            return result
            
        except Exception as e:
            self.logger.log_error(
                error_type="TWAP_VOLUME_PROFILE_FAILED",
                message=f"Failed to place TWAP order with volume profile: {str(e)}",
                extra_data={
                    "symbol": symbol,
                    "side": side,
                    "total_quantity": total_quantity,
                    "volume_profile": volume_profile
                }
            )
            raise
    
    def _calculate_volume_profile(self, total_quantity: float, num_chunks: int, profile: str) -> List[float]:
        """
        Calculate chunk quantities based on volume profile.
        
        Args:
            total_quantity: Total quantity to distribute
            num_chunks: Number of chunks
            profile: Volume profile type
        
        Returns:
            List of chunk quantities
        """
        if profile == 'UNIFORM':
            return [total_quantity / num_chunks] * num_chunks
        
        elif profile == 'FRONT_LOADED':
            # More volume at the beginning
            weights = [1.5 - 0.5 * i / (num_chunks - 1) for i in range(num_chunks)]
            total_weight = sum(weights)
            return [total_quantity * w / total_weight for w in weights]
        
        elif profile == 'BACK_LOADED':
            # More volume at the end
            weights = [0.5 + 0.5 * i / (num_chunks - 1) for i in range(num_chunks)]
            total_weight = sum(weights)
            return [total_quantity * w / total_weight for w in weights]
        
        elif profile == 'MIDDLE_LOADED':
            # More volume in the middle
            weights = []
            for i in range(num_chunks):
                mid_point = (num_chunks - 1) / 2
                distance = abs(i - mid_point)
                weight = 1.5 - distance / mid_point
                weights.append(max(0.5, weight))
            total_weight = sum(weights)
            return [total_quantity * w / total_weight for w in weights]
        
        else:
            return [total_quantity / num_chunks] * num_chunks

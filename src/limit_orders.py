#!/usr/bin/env python3
"""
Limit Orders CLI Entry Point

Usage:
    python src/limit_orders.py <symbol> <side> <quantity> <price>
    python src/limit_orders.py BTCUSDT BUY 0.01 50000
    python src/limit_orders.py ETHUSDT SELL 0.1 3000
"""

import sys
import argparse
from .config import ConfigManager
from .logger import BotLogger
from .validators import TradingValidator
from .api_client import BinanceAPIClient
from .limit_orders_module import LimitOrderManager


def main():
    parser = argparse.ArgumentParser(description='Binance Futures Limit Order Bot')
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('price', type=float, help='Limit price')
    parser.add_argument('--time-in-force', default='GTC', choices=['GTC', 'IOC', 'FOK'], help='Time in force')
    parser.add_argument('--reduce-only', action='store_true', help='Reduce only order')
    parser.add_argument('--usdt', type=float, help='USDT amount instead of quantity')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Initialize components
        logger = BotLogger(config.log_file, config.log_level)
        validator = TradingValidator(logger)
        api_client = BinanceAPIClient(config.api_key, config.api_secret, config.base_url, logger)
        limit_manager = LimitOrderManager(api_client, validator, logger)
        
        # Place order
        if args.usdt:
            result = limit_manager.calculate_quantity_from_usdt(args.symbol, args.usdt, args.price)
            quantity = result['quantity']
            print(f"Calculated quantity: {quantity} for {args.usdt} USDT at {args.price}")
        else:
            quantity = args.quantity
        
        result = limit_manager.place_limit_order(
            symbol=args.symbol,
            side=args.side,
            quantity=quantity,
            price=args.price,
            time_in_force=args.time_in_force,
            reduce_only=args.reduce_only
        )
        
        print(f"✅ Limit order placed successfully!")
        print(f"Order ID: {result.get('orderId')}")
        print(f"Status: {result.get('status')}")
        print(f"Price: {result.get('price')}")
        print(f"Quantity: {result.get('origQty')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

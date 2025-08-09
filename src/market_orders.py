#!/usr/bin/env python3
"""
Market Orders CLI Entry Point

Usage:
    python src/market_orders.py <symbol> <side> <quantity>
    python src/market_orders.py BTCUSDT BUY 0.01
    python src/market_orders.py ETHUSDT SELL 0.1
"""

import sys
import argparse
from .config import ConfigManager
from .logger import BotLogger
from .validators import TradingValidator
from .api_client import BinanceAPIClient
from .market_orders_module import MarketOrderManager


def main():
    parser = argparse.ArgumentParser(description='Binance Futures Market Order Bot')
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('--usdt', type=float, help='USDT amount instead of quantity')
    parser.add_argument('--reduce-only', action='store_true', help='Reduce only order')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Initialize components
        logger = BotLogger(config.log_file, config.log_level)
        validator = TradingValidator(logger)
        api_client = BinanceAPIClient(config.api_key, config.api_secret, config.base_url, logger)
        market_manager = MarketOrderManager(api_client, validator, logger)
        
        # Place order
        if args.usdt:
            result = market_manager.calculate_quantity_from_usdt(args.symbol, args.usdt)
            quantity = result['quantity']
            print(f"Calculated quantity: {quantity} for {args.usdt} USDT")
        else:
            quantity = args.quantity
        
        result = market_manager.place_market_order(
            symbol=args.symbol,
            side=args.side,
            quantity=quantity,
            reduce_only=args.reduce_only
        )
        
        print(f"✅ Market order placed successfully!")
        print(f"Order ID: {result.get('orderId')}")
        print(f"Status: {result.get('status')}")
        print(f"Executed Qty: {result.get('executedQty')}")
        print(f"Price: {result.get('avgPrice')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

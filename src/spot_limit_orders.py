#!/usr/bin/env python3
"""
Spot Limit Orders CLI Entry Point

Usage:
    python -m src.spot_limit_orders <symbol> <side> <quantity> <price>
    python -m src.spot_limit_orders BTCUSDT BUY 0.001 50000
    python -m src.spot_limit_orders ETHUSDT SELL 0.01 3000
"""

import sys
import argparse
from .config import ConfigManager
from .logger import BotLogger
from .validators import TradingValidator
from .spot_api_client import SpotAPIClient
from .spot_orders_module import SpotOrderManager


def main():
    parser = argparse.ArgumentParser(description='Binance Spot Limit Order Bot')
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('price', type=float, help='Limit price')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Initialize components
        logger = BotLogger(config.log_file, config.log_level)
        validator = TradingValidator(logger)
        api_client = SpotAPIClient(config.api_key, config.api_secret, config.base_url, logger)
        spot_manager = SpotOrderManager(api_client, validator, logger)
        
        # Place limit order
        result = spot_manager.place_limit_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity,
            price=args.price
        )
        
        print(f"✅ Spot limit order placed successfully!")
        print(f"Order ID: {result.get('orderId')}")
        print(f"Status: {result.get('status')}")
        print(f"Symbol: {result.get('symbol')}")
        print(f"Side: {result.get('side')}")
        print(f"Quantity: {result.get('origQty')}")
        print(f"Price: {result.get('price')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

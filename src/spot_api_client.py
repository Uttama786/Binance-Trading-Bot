"""
Spot API Client module for Binance Spot Trading
Handles all API interactions with Binance Spot (testnet)
"""

import time
import hmac
import hashlib
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
from .logger import BotLogger


class SpotAPIClient:
    """API client for Binance Spot trading"""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://testnet.binance.vision", logger: BotLogger = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.logger = logger or BotLogger()
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for authenticated requests"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                     signed: bool = False) -> Dict[str, Any]:
        """Make HTTP request to Binance Spot API with logging and error handling"""
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        # Add timestamp for signed requests
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, data=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_time = (time.time() - start_time) * 1000
            
            # Log the API call
            self.logger.log_api_call(
                endpoint=endpoint,
                method=method.upper(),
                params={k: v for k, v in params.items() if k != 'signature'},
                status_code=response.status_code,
                response_time_ms=response_time
            )
            
            # Handle response
            if response.status_code == 200:
                return response.json()
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    error_data = {'msg': response.text}
                
                error_msg = error_data.get('msg', 'Unknown error')
                error_code = error_data.get('code', None)
                
                self.logger.log_api_error(
                    endpoint=endpoint,
                    status_code=response.status_code,
                    error_message=error_msg,
                    error_code=error_code
                )
                
                raise Exception(f"API Error {response.status_code}: {error_msg}")
                
        except requests.exceptions.RequestException as e:
            self.logger.log_api_error(
                endpoint=endpoint,
                status_code=0,
                error_message=f"Network error: {str(e)}",
                error_code=None
            )
            raise Exception(f"Network error: {str(e)}")
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        return self._make_request('GET', '/api/v3/account', signed=True)
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information"""
        response = self._make_request('GET', '/api/v3/exchangeInfo')
        symbols = response.get('symbols', [])
        for sym in symbols:
            if sym['symbol'] == symbol:
                return sym
        raise Exception(f"Symbol {symbol} not found")
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        params = {'symbol': symbol}
        response = self._make_request('GET', '/api/v3/ticker/price', params)
        return float(response['price'])
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Place a market order"""
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': 'MARKET',
            'quantity': quantity
        }
        return self._make_request('POST', '/api/v3/order', params, signed=True)
    
    def place_market_order_usdt(self, symbol: str, side: str, usdt_amount: float) -> Dict[str, Any]:
        """Place a market order using USDT amount (quoteOrderQty)"""
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': 'MARKET',
            'quoteOrderQty': usdt_amount
        }
        return self._make_request('POST', '/api/v3/order', params, signed=True)
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        """Place a limit order"""
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': 'LIMIT',
            'timeInForce': 'GTC',
            'quantity': quantity,
            'price': price
        }
        return self._make_request('POST', '/api/v3/order', params, signed=True)
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order status"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._make_request('GET', '/api/v3/order', params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an order"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._make_request('DELETE', '/api/v3/order', params, signed=True)

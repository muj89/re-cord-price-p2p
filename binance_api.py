import requests
import logging
import time

logger = logging.getLogger(__name__)

def fetch_binance_p2p_data():
    """
    Fetches USDT to SDG exchange rate data from Binance P2P API.
    Returns filtered data for both BUY and SELL offers.
    
    Returns:
        tuple: (buy_data, sell_data) - filtered data for both BUY and SELL transactions
    """
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Buy data (users selling USDT)
    buy_payload = {
        "page": 1,
        "rows": 20,
        "payTypes": [],
        "asset": "USDT",
        "tradeType": "BUY",
        "fiat": "SDG",
        "publisherType": None
    }
    
    # Sell data (users buying USDT)
    sell_payload = {
        "page": 1,
        "rows": 20,
        "payTypes": [],
        "asset": "USDT",
        "tradeType": "SELL",
        "fiat": "SDG",
        "publisherType": None
    }
    
    buy_data = []
    sell_data = []
    
    try:
        # Fetch BUY data
        buy_response = requests.post(url, headers=headers, json=buy_payload)
        if buy_response.status_code == 200:
            buy_result = buy_response.json()
            if 'data' in buy_result and buy_result['data']:
                raw_buy_data = buy_result['data']
                
                # Extract and filter relevant fields
                for item in raw_buy_data:
                    advertiser = item.get('advertiser', {})
                    is_merchant = advertiser.get('userType') == 'merchant'
                    available_qty = float(item.get('dynamicMaxSingleTransAmount', "0"))
                    
                    # Filter for merchants or offers with quantity > 1000
                    if is_merchant or available_qty > 1000:
                        buy_data.append({
                            'price': item.get('price', '0'),
                            'min_amount': item.get('minSingleTransAmount', '0'),
                            'max_amount': item.get('dynamicMaxSingleTransAmount', '0'),
                            'available_qty': available_qty,
                            'payment_methods': [method.get('identifier') for method in item.get('adv', {}).get('tradeMethods', [])],
                            'is_merchant': is_merchant,
                            'completed_rate': advertiser.get('monthFinishRate', '0%'),
                            'advertiser_name': advertiser.get('nickName', 'Unknown')
                        })
        
        # Add delay to avoid rate limiting
        time.sleep(1)
        
        # Fetch SELL data
        sell_response = requests.post(url, headers=headers, json=sell_payload)
        if sell_response.status_code == 200:
            sell_result = sell_response.json()
            if 'data' in sell_result and sell_result['data']:
                raw_sell_data = sell_result['data']
                
                # Extract and filter relevant fields
                for item in raw_sell_data:
                    advertiser = item.get('advertiser', {})
                    is_merchant = advertiser.get('userType') == 'merchant'
                    available_qty = float(item.get('dynamicMaxSingleTransAmount', "0"))
                    
                    # Filter for merchants or offers with quantity > 1000
                    if is_merchant or available_qty > 1000:
                        sell_data.append({
                            'price': item.get('price', '0'),
                            'min_amount': item.get('minSingleTransAmount', '0'),
                            'max_amount': item.get('dynamicMaxSingleTransAmount', '0'),
                            'available_qty': available_qty,
                            'payment_methods': [method.get('identifier') for method in item.get('adv', {}).get('tradeMethods', [])],
                            'is_merchant': is_merchant,
                            'completed_rate': advertiser.get('monthFinishRate', '0%'),
                            'advertiser_name': advertiser.get('nickName', 'Unknown')
                        })
        
        logger.info(f"Successfully fetched Binance P2P data. BUY offers: {len(buy_data)}, SELL offers: {len(sell_data)}")
        return buy_data, sell_data
    
    except Exception as e:
        logger.error(f"Error fetching Binance P2P data: {str(e)}")
        return [], []

import os
import pandas as pd
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DATA_DIR = "data"

def save_to_excel(buy_data, sell_data, filename):
    """
    Save the fetched data to an Excel file.
    
    Args:
        buy_data: List of buy offers
        sell_data: List of sell offers
        filename: Path to save the Excel file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create DataFrames
        buy_df = pd.DataFrame(buy_data)
        sell_df = pd.DataFrame(sell_data)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create Excel writer
        with pd.ExcelWriter(filename) as writer:
            # Write metadata sheet
            pd.DataFrame([
                {"Key": "Generated At", "Value": timestamp},
                {"Key": "BUY Offers Count", "Value": len(buy_data)},
                {"Key": "SELL Offers Count", "Value": len(sell_data)}
            ]).to_excel(writer, sheet_name='Metadata', index=False)
            
            # Write data sheets
            if not buy_df.empty:
                buy_df.to_excel(writer, sheet_name='BUY Offers', index=False)
            
            if not sell_df.empty:
                sell_df.to_excel(writer, sheet_name='SELL Offers', index=False)
            
            # Calculate averages
            if not buy_df.empty:
                buy_avg = buy_df['price'].astype(float).mean()
            else:
                buy_avg = 0
                
            if not sell_df.empty:
                sell_avg = sell_df['price'].astype(float).mean()
            else:
                sell_avg = 0
            
            # Create summary sheet
            summary_data = {
                'Metric': ['Average BUY Price', 'Average SELL Price', 'Spread'],
                'Value': [buy_avg, sell_avg, sell_avg - buy_avg]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        logger.info(f"Successfully saved data to Excel file: {filename}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving to Excel: {str(e)}")
        return False

def get_latest_data():
    """
    Get the latest data from the JSON cache.
    
    Returns:
        dict: The latest data or None if not available
    """
    latest_file = f"{DATA_DIR}/latest_data.json"
    try:
        if os.path.exists(latest_file):
            with open(latest_file, "r") as f:
                data = json.load(f)
                return data
        return None
    except Exception as e:
        logger.error(f"Error reading latest data: {str(e)}")
        return None

def get_historical_data():
    """
    Get the historical data from the JSON cache.
    
    Returns:
        list: The historical data or None if not available
    """
    historical_file = f"{DATA_DIR}/historical_data.json"
    try:
        if os.path.exists(historical_file):
            with open(historical_file, "r") as f:
                data = json.load(f)
                return data
        return None
    except Exception as e:
        logger.error(f"Error reading historical data: {str(e)}")
        return None

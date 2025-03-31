import os
import logging
from flask import Flask, render_template, jsonify, request, send_file
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import json
import pandas as pd
from binance_api import fetch_binance_p2p_data
from data_manager import save_to_excel, get_historical_data, get_latest_data

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Initialize data storage
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Initialize scheduler
scheduler = BackgroundScheduler()

def update_exchange_rate_data():
    """Fetch the latest data from Binance P2P and save it"""
    try:
        logger.info(f"Updating exchange rate data at {datetime.datetime.now()}")
        buy_data, sell_data = fetch_binance_p2p_data()
        
        # Check if we have valid data
        if buy_data and sell_data:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # Save to Excel
            excel_filename = f"{DATA_DIR}/binance_p2p_usdt_sdg_{timestamp}.xlsx"
            save_to_excel(buy_data, sell_data, excel_filename)
            
            # Save to JSON for quick access
            latest_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "buy_data": buy_data,
                "sell_data": sell_data
            }
            
            with open(f"{DATA_DIR}/latest_data.json", "w") as f:
                json.dump(latest_data, f)
                
            # Update historical data
            update_historical_data(buy_data, sell_data)
                
            logger.info(f"Data updated successfully and saved to {excel_filename}")
            return True
        else:
            logger.error("Failed to fetch valid data from Binance")
            return False
    except Exception as e:
        logger.error(f"Error updating exchange rate data: {str(e)}")
        return False

def update_historical_data(buy_data, sell_data):
    """Update the historical data JSON file with new data points"""
    try:
        historical_file = f"{DATA_DIR}/historical_data.json"
        
        # Calculate average prices
        buy_prices = [float(offer['price']) for offer in buy_data]
        sell_prices = [float(offer['price']) for offer in sell_data]
        
        buy_avg = sum(buy_prices) / len(buy_prices) if buy_prices else 0
        sell_avg = sum(sell_prices) / len(sell_prices) if sell_prices else 0
        
        # Create new data point
        new_data_point = {
            "timestamp": datetime.datetime.now().isoformat(),
            "buy_avg": buy_avg,
            "sell_avg": sell_avg
        }
        
        # Load existing historical data or create new
        if os.path.exists(historical_file):
            with open(historical_file, "r") as f:
                historical_data = json.load(f)
        else:
            historical_data = []
        
        # Add new data point and save
        historical_data.append(new_data_point)
        
        # Keep only last 100 data points to avoid file growing too large
        if len(historical_data) > 100:
            historical_data = historical_data[-100:]
            
        with open(historical_file, "w") as f:
            json.dump(historical_data, f)
            
        logger.info("Historical data updated successfully")
    except Exception as e:
        logger.error(f"Error updating historical data: {str(e)}")

# Schedule data updates every hour
scheduler.add_job(update_exchange_rate_data, 'interval', hours=1)
scheduler.start()

# Run an initial update
update_exchange_rate_data()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/latest-data')
def api_latest_data():
    """API endpoint to get the latest data"""
    data = get_latest_data()
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": "No data available"}), 404

@app.route('/api/historical-data')
def api_historical_data():
    """API endpoint to get historical data"""
    data = get_historical_data()
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": "No historical data available"}), 404

@app.route('/api/update-now', methods=['POST'])
def api_update_now():
    """API endpoint to manually trigger a data update"""
    success = update_exchange_rate_data()
    if success:
        return jsonify({"message": "Data updated successfully"})
    else:
        return jsonify({"error": "Failed to update data"}), 500

@app.route('/api/download-latest')
def download_latest():
    """Download the latest Excel file"""
    try:
        # Find the most recent Excel file
        excel_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.xlsx')]
        if not excel_files:
            return jsonify({"error": "No Excel files available"}), 404
        
        latest_file = max(excel_files, key=lambda x: os.path.getmtime(os.path.join(DATA_DIR, x)))
        return send_file(os.path.join(DATA_DIR, latest_file), as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading Excel file: {str(e)}")
        return jsonify({"error": "Failed to download Excel file"}), 500

@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    """Ensure the scheduler is shut down when the app context ends"""
    if scheduler.running:
        scheduler.shutdown()

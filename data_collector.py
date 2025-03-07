import requests
import pandas as pd
import yfinance as yf
import json
import numpy as np
from datetime import datetime, timedelta
import os
import time
import math
import ssl
import random
import traceback
from tqdm import tqdm

# Configure SSL context and disable warnings
ssl._create_default_https_context = ssl._create_unverified_context
import warnings

warnings.filterwarnings('ignore')


def get_all_indian_stocks():
    """Get complete list of stocks from both NSE and BSE"""
    all_symbols = []

    try:
        # NSE stocks
        print("Fetching NSE stocks...")
        nse_main_url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        nse_df = pd.read_csv(nse_main_url)
        nse_symbols = [f"{symbol.strip()}.NS" for symbol in nse_df['SYMBOL'].tolist()]
        all_symbols.extend(nse_symbols)
        print(f"Found {len(nse_symbols)} NSE stocks")

        # Save NSE symbols separately for reference
        with open('data/nse_symbols.json', 'w') as f:
            json.dump(nse_symbols, f, indent=2)
    except Exception as e:
        print(f"Error fetching NSE main list: {e}")
        traceback.print_exc()

    try:
        # BSE stocks
        print("Fetching BSE stocks...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        # Use a more reliable BSE API endpoint
        bse_url = "https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Scripcode=&industry=&segment=Equity&status=Active"

        # Make the request with a timeout
        response = requests.get(bse_url, headers=headers, timeout=30)

        if response.status_code == 200:
            # Debug the response content
            content_start = response.content[:100].decode('utf-8', errors='ignore')
            print(f"BSE API response starts with: {content_start}...")

            # Try to parse JSON with error handling
            try:
                bse_data = response.json()
                if 'Table' in bse_data and isinstance(bse_data['Table'], list):
                    bse_symbols = [f"{item.get('SCRIP_CD')}.BO" for item in bse_data['Table'] if 'SCRIP_CD' in item]
                    all_symbols.extend(bse_symbols)
                    print(f"Found {len(bse_symbols)} BSE stocks")

                    # Save BSE symbols separately for reference
                    with open('data/bse_symbols.json', 'w') as f:
                        json.dump(bse_symbols, f, indent=2)
                else:
                    print(
                        f"Invalid BSE data format. Keys: {bse_data.keys() if isinstance(bse_data, dict) else 'Not a dict'}")
            except json.JSONDecodeError as je:
                print(f"Error decoding BSE JSON: {je}")
                # Try to extract script codes using a fallback method
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # Look for any JSON-like content in the HTML
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if 'SCRIP_CD' in script.text:
                            print("Found script tags with SCRIP_CD, trying to extract...")
                            # Further processing would be needed here
                except:
                    print("Beautiful Soup parsing failed or not available")
        else:
            print(f"Failed to fetch BSE stocks, status code: {response.status_code}")
            print(f"Response content: {response.content[:200]}")

        # If BSE failed, try an alternative method
        if not any(s.endswith('.BO') for s in all_symbols):
            print("Attempting alternative BSE data source...")
            try:
                # Alternative: Use a list of common BSE scrip codes
                # This is a fallback and will only include major stocks
                common_bse_codes = [
                    "500325", "500570", "500180", "532540", "532174", "500247",
                    "500696", "500875", "500112", "532978", "532454", "500820"
                ]
                bse_symbols = [f"{code}.BO" for code in common_bse_codes]
                all_symbols.extend(bse_symbols)
                print(f"Using {len(bse_symbols)} common BSE stocks as fallback")
            except Exception as alt_e:
                print(f"Alternative BSE method failed: {alt_e}")

    except Exception as e:
        print(f"Error fetching BSE stocks: {e}")
        traceback.print_exc()

    if not all_symbols:
        print("All methods failed, using hardcoded list of major Indian stocks")
        major_stocks = [
            "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "KOTAKBANK.NS",
            "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "ASIANPAINT.NS",
            "HCLTECH.NS", "AXISBANK.NS", "LT.NS", "MARUTI.NS", "TITAN.NS", "BAJAJFINSV.NS",
            "SUNPHARMA.NS", "WIPRO.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS", "TECHM.NS", "DIVISLAB.NS",
        ]
        all_symbols = major_stocks

    # Ensure uniqueness and clean any invalid symbols
    unique_symbols = []
    for symbol in all_symbols:
        if symbol and isinstance(symbol, str) and (symbol.endswith('.NS') or symbol.endswith('.BO')):
            # Trim whitespace and ensure valid format
            cleaned_symbol = symbol.strip()
            if cleaned_symbol not in unique_symbols:
                unique_symbols.append(cleaned_symbol)

    print(f"Total unique stock symbols: {len(unique_symbols)}")
    return unique_symbols


def get_market_cap_data():
    """Try to get market cap data to prioritize stocks"""
    try:
        print("Fetching market cap data...")
        nse_main_url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        df = pd.read_csv(nse_main_url)

        # Create a dictionary with symbol and market cap
        market_cap_dict = {}

        # Check what columns are available
        print(f"Available columns: {df.columns.tolist()}")

        for _, row in df.iterrows():
            symbol = f"{row['SYMBOL'].strip()}.NS"

            # If market cap column exists
            if 'MARKET_CAP' in df.columns:
                market_cap = row.get('MARKET_CAP', 0)
            elif 'MKTCAP' in df.columns:
                market_cap = row.get('MKTCAP', 0)
            else:
                # Try to estimate from other columns if available
                issued_shares_col = next((col for col in df.columns if 'SHARES' in col.upper()), None)
                close_col = next((col for col in df.columns if 'CLOSE' in col.upper()), None)

                if issued_shares_col and close_col:
                    market_cap = row.get(close_col, 0) * row.get(issued_shares_col, 0)
                else:
                    market_cap = 0

            market_cap_dict[symbol] = market_cap

        return market_cap_dict
    except Exception as e:
        print(f"Error fetching market cap data: {e}")
        traceback.print_exc()
        return {}


def prioritize_stocks(all_symbols, market_cap_data, args):
    """Prioritize which stocks to process first based on market cap"""
    if args.symbols:
        requested_symbols = args.symbols.split(',')
        return [s for s in requested_symbols if s in all_symbols]

    # Process in market cap order if data is available
    if market_cap_data and not args.random:
        # Sort by market cap (highest first)
        prioritized = sorted(
            [(s, market_cap_data.get(s, 0)) for s in all_symbols],
            key=lambda x: x[1],
            reverse=True
        )
        return [s[0] for s in prioritized]

    # If no market cap data or random order requested, shuffle symbols
    if args.random:
        random.shuffle(all_symbols)

    return all_symbols


def fetch_historical_price_data(symbol, period="6mo"):
    """Get historical price data for calculating technical indicators"""
    try:
        stock = yf.Ticker(symbol)
        # Note: Using '6mo' instead of '6m' to match yfinance's expected format
        history = stock.history(period=period)

        if history is None or history.empty:
            return None

        # Fix any missing columns
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col not in history.columns:
                history[col] = 0

        # Convert to numeric and handle any potential string values
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            history[col] = pd.to_numeric(history[col], errors='coerce')

        # Replace NaN values with previous values or 0
        history = history.fillna(method='ffill').fillna(0)

        return history
    except Exception as e:
        print(f"Error fetching historical price data for {symbol}: {e}")
        return None


def calculate_basic_technical_indicators(df):
    """Calculate only the most essential technical indicators to save time"""
    if df is None or df.empty or len(df) < 20:  # Reduced minimum requirement to 20 days
        return None

    try:
        # Use only closing prices
        close_prices = df['Close'].values

        # Basic indicators
        result = {
            'price_history_available': True,
            'historical_prices': close_prices[-50:].tolist() if len(close_prices) >= 50 else close_prices.tolist()
        }

        # 50-day and 200-day moving averages
        if len(close_prices) >= 50:
            result['ma_50'] = float(np.mean(close_prices[-50:]))

        if len(close_prices) >= 200:
            result['ma_200'] = float(np.mean(close_prices[-200:]))

        # Simple RSI calculation
        try:
            # Calculate price changes
            deltas = np.diff(close_prices)

            # Only calculate if we have enough data
            if len(deltas) >= 14:
                # Get last 14 periods
                recent_deltas = deltas[-14:]

                # Separate gains and losses
                gains = np.where(recent_deltas > 0, recent_deltas, 0)
                losses = np.where(recent_deltas < 0, -recent_deltas, 0)

                # Calculate averages
                avg_gain = np.mean(gains)
                avg_loss = np.mean(losses)

                # Calculate RSI
                if avg_loss == 0:
                    rsi = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))

                result['rsi'] = float(rsi)
        except Exception as e:
            print(f"Error calculating RSI: {e}")

        return result
    except Exception as e:
        print(f"Error calculating technical indicators: {e}")
        return {
            'price_history_available': False,
            'error': str(e)
        }


def process_single_stock(symbol):
    """Process a single stock with all required data"""
    try:
        print(f"Processing {symbol}")

        # Get basic data
        stock = yf.Ticker(symbol)
        info = {}

        try:
            info = stock.info
        except Exception as e:
            print(f"Error fetching info for {symbol}: {e}")
            return {
                'name': symbol,
                'symbol': symbol,
                'error': f"Failed to fetch basic info: {str(e)}",
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M")
            }, False

        if not info or len(info) < 5:
            return {
                'name': symbol,
                'symbol': symbol,
                'error': "Insufficient data from Yahoo Finance",
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M")
            }, False

        # Get financial statements
        try:
            balance_sheet = stock.balance_sheet
        except Exception as e:
            print(f"Warning: Failed to fetch balance sheet for {symbol}: {e}")
            balance_sheet = pd.DataFrame()

        try:
            income_stmt = stock.income_stmt
        except Exception as e:
            print(f"Warning: Failed to fetch income statement for {symbol}: {e}")
            income_stmt = pd.DataFrame()

        try:
            cash_flow = stock.cashflow
        except Exception as e:
            print(f"Warning: Failed to fetch cash flow statement for {symbol}: {e}")
            cash_flow = pd.DataFrame()

        # Calculate fundamental metrics
        try:
            if 'returnOnEquity' in info:
                roe = info['returnOnEquity'] * 100
            else:
                if not income_stmt.empty and not balance_sheet.empty:
                    net_income = None
                    for field in ['Net Income', 'Net Income From Continuing Operation Net Minority Interest',
                                  'Net Income Common Stockholders']:
                        if field in income_stmt.index:
                            net_income = income_stmt.loc[field].iloc[0]
                            break

                    total_equity = None
                    for field in ['Stockholders Equity', 'Total Equity Gross Minority Interest', 'Common Stock Equity']:
                        if field in balance_sheet.index:
                            total_equity = balance_sheet.loc[field].iloc[0]
                            break

                    roe = (
                                      net_income / total_equity) * 100 if net_income and total_equity and total_equity > 0 else None
                else:
                    roe = None
        except Exception:
            roe = None

        try:
            if 'debtToEquity' in info:
                debt_to_equity = info['debtToEquity'] / 100
            else:
                if not balance_sheet.empty:
                    total_debt = None
                    if 'Total Debt' in balance_sheet.index:
                        total_debt = balance_sheet.loc['Total Debt'].iloc[0]
                    else:
                        long_term_debt = balance_sheet.loc['Long Term Debt'].iloc[
                            0] if 'Long Term Debt' in balance_sheet.index else 0
                        short_term_debt = balance_sheet.loc['Current Debt'].iloc[
                            0] if 'Current Debt' in balance_sheet.index else 0
                        total_debt = long_term_debt + short_term_debt

                    total_equity = None
                    for field in ['Stockholders Equity', 'Total Equity Gross Minority Interest', 'Common Stock Equity']:
                        if field in balance_sheet.index:
                            total_equity = balance_sheet.loc[field].iloc[0]
                            break

                    debt_to_equity = total_debt / total_equity if total_debt is not None and total_equity is not None and total_equity > 0 else None
                else:
                    debt_to_equity = None
        except Exception:
            debt_to_equity = None

        # Try to calculate FCF
        try:
            if not cash_flow.empty:
                operating_cf = None
                for field in ['Operating Cash Flow', 'CashFlowFromOperations', 'CashFromOperations']:
                    if field in cash_flow.index:
                        operating_cf = cash_flow.loc[field].iloc[0]
                        break

                capital_expenditure = None
                for field in ['Capital Expenditure', 'CapitalExpenditures', 'Capex']:
                    if field in cash_flow.index:
                        capital_expenditure = cash_flow.loc[field].iloc[0]
                        break

                fcf = operating_cf - abs(
                    capital_expenditure) if operating_cf is not None and capital_expenditure is not None else None
            else:
                fcf = None
        except Exception:
            fcf = None

        # Get current price and market cap
        current_price = info.get('currentPrice', info.get('previousClose', info.get('regularMarketPrice')))
        market_cap = info.get('marketCap', 0)

        # Create basic data structure
        stock_data = {
            'name': info.get('longName', info.get('shortName', symbol)),
            'symbol': symbol,
            'sector': info.get('sector', info.get('industry', 'Unknown')),
            'current_price': current_price,
            'market_cap': market_cap,
            'pe_ratio': info.get('trailingPE', info.get('forwardPE')),
            'roe': roe,
            'debt_to_equity': debt_to_equity,
            'fcf': fcf,
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        # Add important ratios if available
        if 'bookValue' in info:
            stock_data['bookValue'] = info['bookValue']

            if current_price:
                stock_data['pb_ratio'] = current_price / info['bookValue']

        if 'trailingEPS' in info:
            stock_data['eps'] = info['trailingEPS']
        elif 'forwardEPS' in info:
            stock_data['eps'] = info['forwardEPS']

        if 'dividendYield' in info and info['dividendYield'] is not None:
            stock_data['dividendYield'] = info['dividendYield'] * 100

        if 'payoutRatio' in info and info['payoutRatio'] is not None:
            stock_data['payoutRatio'] = info['payoutRatio'] * 100

        # Always try to get technical data for all stocks
        try:
            # Use period="6mo" to match yfinance's expected format
            hist_data = fetch_historical_price_data(symbol, period="6mo")
            if hist_data is not None and not hist_data.empty:
                technical_data = calculate_basic_technical_indicators(hist_data)
                if technical_data:
                    stock_data.update(technical_data)
        except Exception as e:
            print(f"Error getting technical data for {symbol}: {e}")

        return stock_data, True
    except Exception as e:
        print(f"Error processing {symbol}: {e}")
        traceback.print_exc()
        return {
            'name': symbol.replace('.NS', '').replace('.BO', ''),
            'symbol': symbol,
            'error': str(e),
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M")
        }, False


def process_stocks(symbols_to_process, batch_size=20, max_runtime=None):
    """Process a list of stocks in batches with runtime checks"""
    print(f"Starting to process {len(symbols_to_process)} stocks...")

    all_data = {}
    start_time = time.time()

    # Create a counter for successful and failed stocks
    success_count = 0
    fail_count = 0

    # Convert batch size to proper number
    batch_size = min(batch_size, len(symbols_to_process))

    # Process in batches
    for i in range(0, len(symbols_to_process), batch_size):
        # Check runtime limit if specified
        if max_runtime and time.time() - start_time > max_runtime:
            print(f"Reached maximum runtime of {max_runtime / 3600:.2f} hours. Stopping processing.")
            break

        # Get current batch
        end_idx = min(i + batch_size, len(symbols_to_process))
        current_batch = symbols_to_process[i:end_idx]

        print(
            f"\nProcessing batch {i // batch_size + 1}/{math.ceil(len(symbols_to_process) / batch_size)} ({len(current_batch)} stocks)")

        # Process each stock in the batch
        for symbol in current_batch:
            stock_data, success = process_single_stock(symbol)
            all_data[symbol] = stock_data

            # Update counters
            if success and 'error' not in stock_data:
                success_count += 1
            else:
                fail_count += 1

        # Save after each batch
        save_data(all_data)

        # Print progress stats
        completion_percentage = ((i + len(current_batch)) / len(symbols_to_process)) * 100
        print(f"Progress: {success_count} successful, {fail_count} failed, {completion_percentage:.2f}% completed")

        # Pause between batches to avoid rate limits (except for last batch)
        if end_idx < len(symbols_to_process):
            sleep_time = 15  # Reduced sleep time to process more stocks
            print(f"Pausing for {sleep_time} seconds to respect API limits...")
            time.sleep(sleep_time)

    return all_data


def save_data(data):
    """Save the collected data"""
    try:
        output_dir = 'data'
        os.makedirs(output_dir, exist_ok=True)

        # Save daily snapshot
        daily_file = f"{output_dir}/stock_data_{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(daily_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Update latest data
        with open(f"{output_dir}/latest.json", 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Data saved to {daily_file} and latest.json")

        # Also save a summary file with key metrics
        summary_data = {}
        for symbol, stock_data in data.items():
            if 'error' not in stock_data:
                summary_data[symbol] = {
                    'name': stock_data.get('name', ''),
                    'price': stock_data.get('current_price', 0),
                    'sector': stock_data.get('sector', 'Unknown'),
                    'market_cap': stock_data.get('market_cap', 0),
                    'pe_ratio': stock_data.get('pe_ratio', 0),
                    'roe': stock_data.get('roe', 0),
                    'debt_to_equity': stock_data.get('debt_to_equity', 0),
                    'last_updated': stock_data.get('last_updated', '')
                }

        with open(f"{output_dir}/summary_{datetime.now().strftime('%Y-%m-%d')}.json", 'w') as f:
            json.dump(summary_data, f, indent=2)

    except Exception as e:
        print(f"Error saving data: {e}")
        traceback.print_exc()


def parse_arguments():
    """Parse command-line arguments"""
    import argparse
    parser = argparse.ArgumentParser(description='Collect stock data for analysis')
    parser.add_argument('--batch-size', type=int, default=20, help='Batch size for processing')
    parser.add_argument('--max-runtime', type=float, default=None, help='Maximum runtime in hours')
    parser.add_argument('--symbols', type=str, default=None, help='Specific symbols to process, comma separated')
    parser.add_argument('--random', action='store_true', help='Process stocks in random order')
    parser.add_argument('--test', action='store_true', help='Run in test mode with small number of stocks')
    return parser.parse_args()


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()

    print("Starting daily stock data collection...")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if current time is after 4 PM (for market close)
    current_hour = datetime.now().hour
    print(f"Current hour: {current_hour}")

    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)

    # Get all Indian stocks
    if args.test:
        # Use a small subset for testing
        all_symbols = [
            "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
            "KOTAKBANK.NS", "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BAJFINANCE.NS"
        ]
        print(f"TEST MODE: Using {len(all_symbols)} major stocks for testing")
    else:
        all_symbols = get_all_indian_stocks()

    # Get market cap data for prioritization
    market_cap_data = get_market_cap_data()

    # Prioritize stocks to process
    symbols_to_process = prioritize_stocks(all_symbols, market_cap_data, args)

    # Convert max_runtime from hours to seconds if specified
    max_runtime_seconds = args.max_runtime * 3600 if args.max_runtime else None

    # Process the stocks
    final_data = process_stocks(
        symbols_to_process,
        batch_size=args.batch_size,
        max_runtime=max_runtime_seconds
    )

    # Final save
    save_data(final_data)

    # Final stats
    success_count = sum(1 for data in final_data.values() if 'error' not in data)
    total_count = len(symbols_to_process)
    completion_percentage = (len(final_data) / total_count) * 100 if total_count > 0 else 0

    print(f"Data collection complete.")
    print(f"Successfully processed {success_count}/{total_count} stocks ({completion_percentage:.2f}%).")

import requests
import pandas as pd
import yfinance as yf
import json
from datetime import datetime
import os
import time
import math
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def get_all_indian_stocks():
    """Get complete list of stocks from both NSE and BSE"""
    all_symbols = []

    
    try:
        
        nse_main_url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        nse_df = pd.read_csv(nse_main_url)
        nse_symbols = [f"{symbol.strip()}.NS" for symbol in nse_df['SYMBOL'].tolist()]
        all_symbols.extend(nse_symbols)
        print(f"Found {len(nse_symbols)} NSE stocks")
    except Exception as e:
        print(f"Error fetching NSE main list: {e}")

    
    try:
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        bse_url = "https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Scripcode=&industry=&segment=Equity&status=Active"
        response = requests.get(bse_url, headers=headers)
        if response.status_code == 200:
            bse_data = response.json()
            if 'Table' in bse_data:
                bse_symbols = [f"{code}.BO" for code in [item.get('SCRIP_CD', '') for item in bse_data['Table']]]
                all_symbols.extend(bse_symbols)
                print(f"Found {len(bse_symbols)} BSE stocks")
        else:
            print(f"Failed to fetch BSE stocks, status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching BSE stocks: {e}")

   
    if not all_symbols:
        print("All methods failed, using hardcoded list of major Indian stocks")
        
        major_stocks = [
            
            "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "KOTAKBANK.NS",
            "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "ASIANPAINT.NS",
            "HCLTECH.NS", "AXISBANK.NS", "LT.NS", "MARUTI.NS", "TITAN.NS", "BAJAJFINSV.NS",
            "SUNPHARMA.NS", "WIPRO.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS", "TECHM.NS", "DIVISLAB.NS",

            
            "500325.BO", "500570.BO", "500180.BO", "532540.BO", "532174.BO", "500247.BO",
            "500696.BO", "500875.BO", "500112.BO", "532978.BO", "532454.BO", "500820.BO"
        ]
        all_symbols = major_stocks

    
    unique_symbols = list(dict.fromkeys(all_symbols))

    print(f"Total unique stock symbols: {len(unique_symbols)}")
    return unique_symbols


def get_financial_data(symbols):
    """Collect financial data for analysis"""
    financial_data = {}
    total_symbols = len(symbols)

    for i, symbol in enumerate(symbols):
        try:
            
            print(f"Processing {i + 1}/{total_symbols}: {symbol}")

            
            stock = yf.Ticker(symbol)

           
            info = stock.info

            
            if not info or len(info) < 5:
                print(f"Insufficient data for {symbol}, skipping")
                continue

            
            balance_sheet = stock.balance_sheet
            income_stmt = stock.income_stmt
            cash_flow = stock.cashflow

            
            if balance_sheet.empty or income_stmt.empty:
                print(f"Missing financial statements for {symbol}, skipping")
                continue

            
            try:
                
                try:
                    
                    if 'returnOnEquity' in info:
                        roe = info['returnOnEquity'] * 100  
                    else:
                        
                        net_income = income_stmt.loc['Net Income'].iloc[
                            0] if 'Net Income' in income_stmt.index else None
                        if net_income is None:
                            possible_income_fields = ['Net Income From Continuing Operation Net Minority Interest',
                                                      'Net Income Common Stockholders',
                                                      'Net Income Including Noncontrolling Interests']
                            for field in possible_income_fields:
                                if field in income_stmt.index:
                                    net_income = income_stmt.loc[field].iloc[0]
                                    break

                        total_equity = balance_sheet.loc['Stockholders Equity'].iloc[
                            0] if 'Stockholders Equity' in balance_sheet.index else None
                        if total_equity is None and 'Total Equity Gross Minority Interest' in balance_sheet.index:
                            total_equity = balance_sheet.loc['Total Equity Gross Minority Interest'].iloc[0]
                        elif total_equity is None and 'Common Stock Equity' in balance_sheet.index:
                            total_equity = balance_sheet.loc['Common Stock Equity'].iloc[0]

                        roe = (
                                          net_income / total_equity) * 100 if net_income and total_equity and total_equity > 0 else None
                except Exception as e:
                    print(f"Error calculating ROE for {symbol}: {e}")
                    roe = None

                
                try:
                    
                    if 'debtToEquity' in info:
                        debt_to_equity = info['debtToEquity'] / 100  
                    else:
                        
                        total_debt = balance_sheet.loc['Total Debt'].iloc[
                            0] if 'Total Debt' in balance_sheet.index else None
                        if total_debt is None:
                            
                            long_term_debt = balance_sheet.loc['Long Term Debt'].iloc[
                                0] if 'Long Term Debt' in balance_sheet.index else 0
                            short_term_debt = balance_sheet.loc['Current Debt'].iloc[
                                0] if 'Current Debt' in balance_sheet.index else 0
                            total_debt = long_term_debt + short_term_debt

                        total_equity = balance_sheet.loc['Stockholders Equity'].iloc[
                            0] if 'Stockholders Equity' in balance_sheet.index else None
                        if total_equity is None and 'Total Equity Gross Minority Interest' in balance_sheet.index:
                            total_equity = balance_sheet.loc['Total Equity Gross Minority Interest'].iloc[0]
                        elif total_equity is None and 'Common Stock Equity' in balance_sheet.index:
                            total_equity = balance_sheet.loc['Common Stock Equity'].iloc[0]

                        debt_to_equity = total_debt / total_equity if total_debt is not None and total_equity is not None and total_equity > 0 else None
                except Exception as e:
                    print(f"Error calculating debt-to-equity for {symbol}: {e}")
                    debt_to_equity = None

                
                try:
                    operating_cf = cash_flow.loc['Operating Cash Flow'].iloc[
                        0] if 'Operating Cash Flow' in cash_flow.index else None
                    if operating_cf is None and not cash_flow.empty:
                        
                        alternative_names = ['CashFlowFromOperations', 'CashFromOperations', 'OperatingCashFlow']
                        for name in alternative_names:
                            if name in cash_flow.index:
                                operating_cf = cash_flow.loc[name].iloc[0]
                                break

                    capital_expenditure = cash_flow.loc['Capital Expenditure'].iloc[
                        0] if 'Capital Expenditure' in cash_flow.index else None
                    if capital_expenditure is None and not cash_flow.empty:
                        
                        alternative_names = ['CapitalExpenditures', 'Capex', 'PropertyPlantEquipmentPurchases']
                        for name in alternative_names:
                            if name in cash_flow.index:
                                capital_expenditure = cash_flow.loc[name].iloc[0]
                                break

                    fcf = operating_cf - abs(
                        capital_expenditure) if operating_cf is not None and capital_expenditure is not None else None
                except (KeyError, IndexError):
                    fcf = None

                
                earnings_growth = None
                try:
                    if not income_stmt.empty and len(income_stmt.columns) >= 5:
                        current_earnings = income_stmt.loc['Net Income'].iloc[0]
                        past_earnings = income_stmt.loc['Net Income'].iloc[4]
                        if current_earnings and past_earnings and past_earnings > 0:
                            earnings_growth = ((current_earnings / past_earnings) ** (1 / 5) - 1) * 100
                except (KeyError, IndexError):
                    try:
                        
                        eps_key = next((k for k in ['trailingEPS', 'forwardEPS'] if k in info), None)
                        if eps_key and 'previousClose' in info and info['previousClose'] > 0:
                            current_eps = info[eps_key]
                            pe_ratio = info.get('trailingPE', info.get('forwardPE'))

                            if pe_ratio:
                                current_earnings = current_eps
                                five_year_growth = info.get('fiveYearAvgDividendYield',
                                                            10)  
                                earnings_growth = five_year_growth
                    except:
                        earnings_growth = None

               
                intrinsic_value = None
                try:
                    if fcf and fcf > 0:
                        
                        growth_rate = info.get('earningsGrowth', 0.10)  

                        
                        growth_rate = max(0.05, min(growth_rate, 0.20))

                        discount_rate = 0.12  

                       
                        future_fcf = []
                        for i in range(1, 11):
                            future_fcf.append(fcf * (1 + growth_rate) ** i)

                        
                        terminal_value = future_fcf[-1] * (1 + 0.03) / (discount_rate - 0.03)
                        future_fcf.append(terminal_value)

                        
                        present_value = sum(
                            [fcf_i / (1 + discount_rate) ** (i + 1) for i, fcf_i in enumerate(future_fcf)])

                        
                        shares_outstanding = info.get('sharesOutstanding', info.get('impliedSharesOutstanding'))
                        if shares_outstanding and shares_outstanding > 0:
                            intrinsic_value = present_value / shares_outstanding
                except Exception as iv_error:
                    print(f"Error calculating intrinsic value for {symbol}: {iv_error}")
                    intrinsic_value = None

                
                current_price = info.get('currentPrice', info.get('previousClose', info.get('regularMarketPrice')))
                margin_of_safety = ((
                                                intrinsic_value - current_price) / intrinsic_value * 100) if intrinsic_value and current_price and intrinsic_value > current_price else None

                
                profit_margin = info.get('profitMargins', None)
                if profit_margin:
                    profit_margin = profit_margin * 100  

                
                financial_data[symbol] = {
                    'name': info.get('longName', info.get('shortName', symbol)),
                    'sector': info.get('sector', info.get('industry', 'Unknown')),
                    'current_price': current_price,
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('trailingPE', info.get('forwardPE')),
                    'roe': roe,
                    'debt_to_equity': debt_to_equity,
                    'fcf': fcf,
                    'earnings_growth': earnings_growth,
                    'profit_margin': profit_margin,
                    'intrinsic_value': intrinsic_value,
                    'margin_of_safety': margin_of_safety,
                    'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M")
                }

            except Exception as calc_error:
                print(f"Error calculating metrics for {symbol}: {calc_error}")
                financial_data[symbol] = {
                    'name': info.get('longName', info.get('shortName', symbol)),
                    'error': str(calc_error),
                    'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M")
                }

        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    return financial_data


def save_data(data):
    """Save collected data to a JSON file"""
    output_dir = 'data'
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{output_dir}/stock_data_{datetime.now().strftime('%Y-%m-%d')}.json"

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

    
    with open(f"{output_dir}/latest.json", 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Data saved to {filename}")


if __name__ == "__main__":
    print("Starting data collection...")
    symbols = get_all_indian_stocks()
    print(f"Collecting data for {len(symbols)} stocks...")
    batch_size = 100
    all_financial_data = {}

    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        print(f"Processing batch {i // batch_size + 1}/{(len(symbols) - 1) // batch_size + 1} ({len(batch)} stocks)")
        batch_data = get_financial_data(batch)
        all_financial_data.update(batch_data)
        
        if i + batch_size < len(symbols):
            print("Pausing for 60 seconds to respect API limits")
            time.sleep(90)

    save_data(all_financial_data)
    print("Data collection complete.")

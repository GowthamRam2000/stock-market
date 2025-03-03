import yfinance as yf
import pandas as pd
import json


def diagnose_stock(symbol):
    """Diagnose data structure for a single stock from Yahoo Finance API"""
    print(f"\n\n{'=' * 50}")
    print(f"DETAILED DIAGNOSTICS FOR {symbol}")
    print(f"{'=' * 50}")

    # Get stock info
    stock = yf.Ticker(symbol)

    # Basic info
    info = stock.info
    print("\nBASIC INFO:")
    print(f"Number of fields in info: {len(info)}")

    # Check if ROE exists directly in info
    roe_keys = [k for k in info.keys() if 'return' in k.lower() or 'roe' in k.lower()]
    print("\nPossible ROE related keys:")
    for key in roe_keys:
        print(f"  - {key}: {info.get(key)}")

    # Check if debt ratio exists directly in info
    debt_keys = [k for k in info.keys() if 'debt' in k.lower() or 'leverage' in k.lower()]
    print("\nPossible Debt related keys:")
    for key in debt_keys:
        print(f"  - {key}: {info.get(key)}")

    # Get financial statements
    balance_sheet = stock.balance_sheet
    income_stmt = stock.income_stmt
    cash_flow = stock.cashflow

    print("\nBALANCE SHEET:")
    if not balance_sheet.empty:
        print(f"Shape: {balance_sheet.shape}")
        print("Columns (dates):")
        for col in balance_sheet.columns:
            print(f"  - {col}")

        print("\nFirst 15 row indices (accounts):")
        for idx in list(balance_sheet.index)[:15]:
            print(f"  - {idx}")

        # Look for Total Equity
        equity_keywords = ['equity', 'stockholder', 'shareholder']
        equity_rows = [idx for idx in balance_sheet.index if any(kw in idx.lower() for kw in equity_keywords)]
        print("\nPossible equity related rows:")
        for idx in equity_rows:
            try:
                value = balance_sheet.loc[idx].iloc[0]
                print(f"  - {idx}: {value}")
            except:
                print(f"  - {idx}: [Error accessing value]")

        # Look for Debt
        debt_keywords = ['debt', 'loan', 'borrowing', 'liability']
        debt_rows = [idx for idx in balance_sheet.index if any(kw in idx.lower() for kw in debt_keywords)]
        print("\nPossible debt related rows:")
        for idx in debt_rows:
            try:
                value = balance_sheet.loc[idx].iloc[0]
                print(f"  - {idx}: {value}")
            except:
                print(f"  - {idx}: [Error accessing value]")
    else:
        print("  [Empty balance sheet]")

    print("\nINCOME STATEMENT:")
    if not income_stmt.empty:
        print(f"Shape: {income_stmt.shape}")
        print("Columns (dates):")
        for col in income_stmt.columns:
            print(f"  - {col}")

        print("\nFirst 15 row indices (accounts):")
        for idx in list(income_stmt.index)[:15]:
            print(f"  - {idx}")

        # Look for Net Income
        income_keywords = ['income', 'earnings', 'profit', 'net']
        income_rows = [idx for idx in income_stmt.index if any(kw in idx.lower() for kw in income_keywords)]
        print("\nPossible net income related rows:")
        for idx in income_rows:
            try:
                value = income_stmt.loc[idx].iloc[0]
                print(f"  - {idx}: {value}")
            except:
                print(f"  - {idx}: [Error accessing value]")
    else:
        print("  [Empty income statement]")

    # Try to calculate ROE and debt-to-equity with different approaches
    print("\nTRYING DIFFERENT CALCULATIONS:")

    # Approach 1: Using financial statements
    try:
        print("\nApproach 1: Using financial statements")
        if not balance_sheet.empty and not income_stmt.empty:
            # Try different field combinations for ROE
            possible_income_fields = ['Net Income', 'NetIncome', 'Net Income Common Stockholders', 'Net Earnings']
            possible_equity_fields = ['Total Stockholder Equity', 'Total Equity', 'Stockholders Equity',
                                      'ShareholdersEquity']

            income_value = None
            for field in possible_income_fields:
                if field in income_stmt.index:
                    income_value = income_stmt.loc[field].iloc[0]
                    print(f"  Found income as '{field}': {income_value}")
                    break

            equity_value = None
            for field in possible_equity_fields:
                if field in balance_sheet.index:
                    equity_value = balance_sheet.loc[field].iloc[0]
                    print(f"  Found equity as '{field}': {equity_value}")
                    break

            if income_value is not None and equity_value is not None and equity_value != 0:
                roe = (income_value / equity_value) * 100
                print(f"  Calculated ROE: {roe:.2f}%")
            else:
                print("  Could not calculate ROE - missing values")

            # Try different field combinations for debt-to-equity
            possible_debt_fields = ['Total Debt', 'Long Term Debt', 'Current Debt', 'LongTermDebt', 'ShortTermDebt']

            debt_value = None
            for field in possible_debt_fields:
                if field in balance_sheet.index:
                    debt_value = balance_sheet.loc[field].iloc[0]
                    print(f"  Found debt as '{field}': {debt_value}")
                    # If we find one debt field, don't exit the loop - we might want to sum multiple debt fields

            # If we can't find a total debt field, try summing long-term and short-term debt
            if debt_value is None:
                long_term_debt = None
                short_term_debt = None

                for field in ['Long Term Debt', 'LongTermDebt']:
                    if field in balance_sheet.index:
                        long_term_debt = balance_sheet.loc[field].iloc[0]
                        print(f"  Found long-term debt as '{field}': {long_term_debt}")
                        break

                for field in ['Short Term Debt', 'ShortTermDebt', 'Current Debt']:
                    if field in balance_sheet.index:
                        short_term_debt = balance_sheet.loc[field].iloc[0]
                        print(f"  Found short-term debt as '{field}': {short_term_debt}")
                        break

                if long_term_debt is not None and short_term_debt is not None:
                    debt_value = long_term_debt + short_term_debt
                    print(f"  Combined debt value: {debt_value}")

            if debt_value is not None and equity_value is not None and equity_value != 0:
                debt_to_equity = debt_value / equity_value
                print(f"  Calculated Debt-to-Equity: {debt_to_equity:.2f}")
            else:
                print("  Could not calculate Debt-to-Equity - missing values")
        else:
            print("  Missing financial statements - can't calculate using Approach 1")
    except Exception as e:
        print(f"  Error in Approach 1: {e}")

    # Approach 2: Using info fields directly
    try:
        print("\nApproach 2: Using info fields directly")

        # Check for ROE in info
        roe_value = None
        roe_field_candidates = ['returnOnEquity', 'ROE', 'ReturnOnEquity']
        for field in roe_field_candidates:
            if field in info:
                roe_value = info[field]
                if isinstance(roe_value, (int, float)) and roe_value != 0:
                    if abs(roe_value) < 1:  # If it's stored as a decimal
                        roe_value *= 100
                    print(f"  Found ROE in info as '{field}': {roe_value:.2f}%")
                    break

        if roe_value is None:
            print("  Could not find ROE in info fields")

        # Check for Debt-to-Equity in info
        de_value = None
        de_field_candidates = ['debtToEquity', 'totalDebt/totalEquity', 'leverageRatio', 'DebtEquityRatio']
        for field in de_field_candidates:
            if field in info:
                de_value = info[field]
                if isinstance(de_value, (int, float)) and de_value != 0:
                    print(f"  Found Debt-to-Equity in info as '{field}': {de_value:.2f}")
                    break

        if de_value is None:
            print("  Could not find Debt-to-Equity in info fields")
    except Exception as e:
        print(f"  Error in Approach 2: {e}")

    # Approach 3: Using key stats
    try:
        print("\nApproach 3: Using key stats")
        # Get key statistics
        key_stats = stock.get_stats()
        if isinstance(key_stats, pd.DataFrame) and not key_stats.empty:
            print(f"  Key stats available: {key_stats.shape[0]} items")

            # Look for ROE
            roe_stats = key_stats[key_stats['Attribute'].str.contains('Return on Equity', case=False, na=False)]
            if not roe_stats.empty:
                roe_stat = roe_stats.iloc[0]['Value']
                print(f"  Found ROE in key stats: {roe_stat}")
            else:
                print("  Could not find ROE in key stats")

            # Look for Debt-to-Equity
            de_stats = key_stats[key_stats['Attribute'].str.contains('Debt to Equity', case=False, na=False)]
            if not de_stats.empty:
                de_stat = de_stats.iloc[0]['Value']
                print(f"  Found Debt-to-Equity in key stats: {de_stat}")
            else:
                print("  Could not find Debt-to-Equity in key stats")
        else:
            print("  No key stats available")
    except Exception as e:
        print(f"  Error in Approach 3: {e}")

    print("\nCONCLUSION:")
    print("Based on the available data, here are the recommended field names or calculation methods:")

    # For ROE
    if info.get('returnOnEquity') is not None:
        print(f"ROE: Use info['returnOnEquity'] * 100 = {info.get('returnOnEquity', 0) * 100:.2f}%")
    elif not income_stmt.empty and not balance_sheet.empty:
        income_field = next((f for f in ['Net Income', 'NetIncome'] if f in income_stmt.index), None)
        equity_field = next((f for f in ['Total Stockholder Equity', 'Total Equity'] if f in balance_sheet.index), None)
        if income_field and equity_field:
            income_val = income_stmt.loc[income_field].iloc[0]
            equity_val = balance_sheet.loc[equity_field].iloc[0]
            if equity_val != 0:
                roe_calc = (income_val / equity_val) * 100
                print(f"ROE: Calculate from {income_field}/{equity_field} * 100 = {roe_calc:.2f}%")

    # For Debt-to-Equity
    if info.get('debtToEquity') is not None:
        print(f"Debt-to-Equity: Use info['debtToEquity'] = {info.get('debtToEquity', 0):.2f}")
    elif not balance_sheet.empty:
        debt_field = next((f for f in ['Total Debt', 'LongTermDebt'] if f in balance_sheet.index), None)
        equity_field = next((f for f in ['Total Stockholder Equity', 'Total Equity'] if f in balance_sheet.index), None)
        if debt_field and equity_field:
            debt_val = balance_sheet.loc[debt_field].iloc[0]
            equity_val = balance_sheet.loc[equity_field].iloc[0]
            if equity_val != 0:
                de_calc = debt_val / equity_val
                print(f"Debt-to-Equity: Calculate from {debt_field}/{equity_field} = {de_calc:.2f}")


def main():
    # List of stocks to diagnose - major Indian stocks
    indian_stocks = [
        "TCS.NS",  # Tata Consultancy Services
        "RELIANCE.NS",  # Reliance Industries
        "HDFCBANK.NS",  # HDFC Bank
        "INFY.NS",  # Infosys
        "ICICIBANK.NS"  # ICICI Bank
    ]

    for symbol in indian_stocks:
        try:
            diagnose_stock(symbol)
        except Exception as e:
            print(f"\nError analyzing {symbol}: {e}")

    print("\n\nDiagnostic complete. Review the output to understand how to extract ROE and Debt-to-Equity ratio data.")


if __name__ == "__main__":
    main()
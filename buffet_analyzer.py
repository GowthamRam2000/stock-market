import json
import os
import numpy as np
from datetime import datetime
import pytz
import re
import math
import statistics
from collections import defaultdict


def safe_format(value, format_spec=".2f"):
    if value is None:
        return f"{0:{format_spec}}"
    return f"{value:{format_spec}}"


def load_latest_data():
    try:
        with open('data/latest.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}

def analyze_operating_efficiency(symbol, data):
    """Analyze operating efficiency and profitability metrics"""
    score = 0
    reasons = []
    warnings = []

    # Check for profit margin - if not available, use ROE as a proxy
    profit_margin = data.get('profit_margin')
    roe = data.get('roe')

    if roe is not None:
        if roe > 20:
            score += 3
            reasons.append(f"Exceptional ROE of {roe:.2f}%")
        elif roe > 15:
            score += 2
            reasons.append(f"Strong ROE of {roe:.2f}%")
        elif roe > 10:
            score += 1
            reasons.append(f"Good ROE of {roe:.2f}%")
    else:
        warnings.append("ROE data not available")


    fcf = data.get('fcf')
    if fcf is not None:
        if fcf > 0:
            market_cap = data.get('market_cap')
            if market_cap and market_cap > 0:
                fcf_yield = (fcf / market_cap) * 100
                if fcf_yield > 8:
                    score += 3
                    reasons.append(f"Excellent FCF yield of {fcf_yield:.2f}%")
                elif fcf_yield > 5:
                    score += 2
                    reasons.append(f"Strong FCF yield of {fcf_yield:.2f}%")
                elif fcf_yield > 3:
                    score += 1
                    reasons.append(f"Positive FCF yield of {fcf_yield:.2f}%")
            else:
                score += 1
                reasons.append("Positive free cash flow")
        elif fcf < 0:
            score -= 1
            warnings.append(f"Negative free cash flow of {fcf:.2f}")
    else:
        warnings.append("Free cash flow data not available")

    return score, reasons, warnings


def analyze_financial_health(symbol, data):
    """Analyze balance sheet strength and financial health"""
    score = 0
    reasons = []
    warnings = []


    debt_to_equity = data.get('debt_to_equity')
    if debt_to_equity is not None:
        if debt_to_equity < 0.3:
            score += 3
            reasons.append(f"Minimal debt-to-equity ratio of {debt_to_equity:.2f}")
        elif debt_to_equity < 0.5:
            score += 2
            reasons.append(f"Low debt-to-equity ratio of {debt_to_equity:.2f}")
        elif debt_to_equity < 0.7:
            score += 1
            reasons.append(f"Moderate debt-to-equity ratio of {debt_to_equity:.2f}")
        elif debt_to_equity > 1.5:
            score -= 1
            warnings.append(f"High debt-to-equity ratio of {debt_to_equity:.2f}")
    else:
        warnings.append("Debt-to-equity data not available")


    pb_ratio = data.get('pb_ratio')
    if pb_ratio is not None:
        if pb_ratio < 1.0:
            score += 3
            reasons.append(f"Trading below book value (P/B ratio: {pb_ratio:.2f})")
        elif pb_ratio < 2.0:
            score += 2
            reasons.append(f"Reasonable P/B ratio of {pb_ratio:.2f}")
        elif pb_ratio < 3.0:
            score += 1
            reasons.append(f"Acceptable P/B ratio of {pb_ratio:.2f}")
        elif pb_ratio > 5.0:
            score -= 1
            warnings.append(f"High P/B ratio of {pb_ratio:.2f}")
    else:
        warnings.append("P/B ratio not available")

    return score, reasons, warnings


def analyze_industry_dynamics(symbol, data):
    sector = data.get('sector', 'Unknown')

    favorable_industries = [
        'Consumer Staples', 'Consumer Defensive', 'Consumer Goods', 'Utilities',
        'Insurance', 'Banking', 'Financial Services', 'Financial'
    ]

    moderate_industries = [
        'Healthcare', 'Technology', 'Communication Services', 'Industrial',
        'Energy', 'Telecom', 'Real Estate', 'Pharmaceutical'
    ]

    unfavorable_industries = [
        'Biotechnology', 'Cryptocurrency', 'Cannabis', 'Airlines', 'Mining',
        'Oil & Gas E&P', 'Fashion', 'Retail'
    ]

    if any(ind in sector for ind in favorable_industries):
        score = 2
        reason = f"Industry with stable cash flows and high entry barriers: {sector}"
    elif any(ind in sector for ind in moderate_industries):
        score = 1
        reason = f"Industry with moderate business stability: {sector}"
    elif any(ind in sector for ind in unfavorable_industries):
        score = -1
        reason = f"Industry that Buffett typically avoids: {sector}"
    else:
        score = 0
        reason = f"Neutral industry assessment: {sector}"

    return score, reason


def analyze_regulatory_environment(symbol, data):
    sector = data.get('sector', 'Unknown')

    stable_regulatory_sectors = [
        'Consumer Staples', 'Consumer Goods', 'Insurance', 'Banking', 'Pharmaceutical',
        'Financial Services', 'Utilities'
    ]

    challenging_regulatory_sectors = [
        'Healthcare', 'Telecom', 'Energy', 'Banking',
        'Technology', 'Oil & Gas'
    ]

    if '.NS' in symbol:
        india_favorable_sectors = [
            'IT Services', 'Technology', 'Consumer Goods', 'Automotive', 'Pharmaceutical'
        ]

        india_challenging_sectors = [
            'Telecom', 'Banking', 'Energy', 'Real Estate'
        ]

        if any(ind in sector for ind in india_favorable_sectors):
            score = 1
            reason = f"Favorable regulatory environment in India for {sector}"
        elif any(ind in sector for ind in india_challenging_sectors):
            score = -1
            reason = f"Challenging regulatory environment in India for {sector}"
        else:
            score = 0
            reason = "Neutral regulatory assessment"
    else:
        if any(ind in sector for ind in stable_regulatory_sectors):
            score = 1
            reason = f"Generally stable regulatory environment for {sector}"
        elif any(ind in sector for ind in challenging_regulatory_sectors):
            score = -1
            reason = f"Often faces regulatory challenges in {sector}"
        else:
            score = 0
            reason = "Neutral regulatory assessment"

    return score, reason


def analyze_macroeconomic_factors(symbol, data):
    sector = data.get('sector', 'Unknown')

    recession_resistant_sectors = [
        'Consumer Staples', 'Healthcare', 'Utilities', 'Discount Retail',
        'Essential Services', 'Consumer Defensive'
    ]

    economically_sensitive_sectors = [
        'Luxury Goods', 'Travel', 'Hospitality', 'Automotive', 'Construction',
        'Real Estate', 'Discretionary', 'Industrial', 'Banking'
    ]

    if '.NS' in symbol:
        if any(ind in sector for ind in recession_resistant_sectors):
            score = 2
            reason = f"Recession-resistant sector in fast-growing Indian economy: {sector}"
        elif any(ind in sector for ind in economically_sensitive_sectors):
            score = 0
            reason = f"Economically sensitive but benefits from India's growth: {sector}"
        else:
            score = 1
            reason = f"Neutral macroeconomic assessment in Indian context"
    else:
        if any(ind in sector for ind in recession_resistant_sectors):
            score = 1
            reason = f"Business relatively resistant to economic downturns: {sector}"
        elif any(ind in sector for ind in economically_sensitive_sectors):
            score = -1
            reason = f"Business sensitive to economic cycles: {sector}"
        else:
            score = 0
            reason = "Neutral macroeconomic assessment"

    return score, reason


def analyze_economic_moat(symbol, data):
    name = data.get('name', '')
    sector = data.get('sector', 'Unknown')
    roe = data.get('roe', 0) or 0

    exceptional_roe = roe > 25

    network_effect_sectors = [
        'Technology', 'Social Media', 'Payments', 'E-commerce', 'Telecom',
        'Software', 'IT Services', 'Platform'
    ]

    brand_moat_sectors = [
        'Consumer Goods', 'Luxury', 'FMCG', 'Automotive', 'Consumer Defensive',
        'Beverages', 'Fast Food', 'Retail'
    ]

    switching_cost_sectors = [
        'Banking', 'Enterprise Software', 'Insurance', 'Financial Services',
        'Healthcare', 'IT Services'
    ]

    strong_moat_companies = [
        'HDFC Bank', 'Asian Paints', 'Hindustan Unilever', 'Nestlé India',
        'Bajaj Finance', 'TCS', 'Titan Company', 'ITC', 'Britannia',
        'Page Industries', 'Pidilite Industries'
    ]

    score = 0
    moat_types = []

    for company in strong_moat_companies:
        if company.lower() in name.lower():
            score += 2
            moat_types.append(f"Known for strong historical moat ({company})")
            break

    if any(s in sector for s in network_effect_sectors):
        score += 1
        moat_types.append(f"Sector with potential network effects ({sector})")

    if any(s in sector for s in brand_moat_sectors):
        score += 1
        moat_types.append(f"Sector with potential brand moat ({sector})")

    if any(s in sector for s in switching_cost_sectors):
        score += 1
        moat_types.append(f"Sector with potential switching costs ({sector})")

    if exceptional_roe:
        score += 1
        moat_types.append(f"Exceptional ROE ({roe:.1f}%) indicates sustainable competitive advantage")

    score = min(score, 4)

    if not moat_types:
        moat_types.append("No clear economic moat identified")

    return score, ", ".join(moat_types)


def analyze_valuation(symbol, data):
    """Analyze valuation metrics"""
    score = 0
    reasons = []
    warnings = []

    # P/E Ratio analysis
    pe_ratio = data.get('pe_ratio')
    if pe_ratio is not None and pe_ratio > 0:
        if pe_ratio < 15:
            score += 3
            reasons.append(f"Attractive P/E ratio of {pe_ratio:.2f}")
        elif pe_ratio < 20:
            score += 2
            reasons.append(f"Reasonable P/E ratio of {pe_ratio:.2f}")
        elif pe_ratio < 25:
            score += 1
            reasons.append(f"Acceptable P/E ratio of {pe_ratio:.2f}")
        elif pe_ratio > 30:
            score -= 1
            warnings.append(f"High P/E ratio of {pe_ratio:.2f}")
    else:
        warnings.append("P/E ratio data not available")


    pb_ratio = data.get('pb_ratio')
    if pb_ratio is not None and pb_ratio > 0:
        sector = data.get('sector', 'Unknown')
        is_financial = any(s in sector for s in ['Bank', 'Financial', 'Insurance'])

        threshold = 2 if is_financial else 3
        if pb_ratio < threshold * 0.5:
            score += 2
            reasons.append(f"Very attractive P/B ratio of {pb_ratio:.2f}")
        elif pb_ratio < threshold:
            score += 1
            reasons.append(f"Reasonable P/B ratio of {pb_ratio:.2f}")
        elif pb_ratio > threshold * 2:
            score -= 1
            warnings.append(f"High P/B ratio of {pb_ratio:.2f}")


    dividend_yield = data.get('dividendYield')
    if dividend_yield is not None and dividend_yield > 0:
        if dividend_yield > 4:
            score += 2
            reasons.append(f"High dividend yield of {dividend_yield:.2f}%")
        elif dividend_yield > 2:
            score += 1
            reasons.append(f"Good dividend yield of {dividend_yield:.2f}%")

    return score, reasons, warnings



def analyze_technical_indicators(symbol, data):
    """Analyze technical indicators when available"""
    score = 0
    reasons = []
    warnings = []


    price_history_available = data.get('price_history_available', False)
    if not price_history_available:
        warnings.append("Technical analysis skipped - price history not available")
        return score, reasons, warnings


    rsi = data.get('rsi')
    if rsi is not None:
        if rsi < 30:
            score += 2
            reasons.append(f"Oversold RSI ({rsi:.2f}) suggests potential buying opportunity")
        elif rsi < 40:
            score += 1
            reasons.append(f"RSI ({rsi:.2f}) indicates potential undervaluation")
        elif rsi > 70:
            score -= 1
            reasons.append(f"Overbought RSI ({rsi:.2f}) suggests potential overvaluation")
    else:
        warnings.append("RSI data not available")


    ma_50 = data.get('ma_50')
    current_price = data.get('current_price')

    if ma_50 is not None and current_price is not None:
        if current_price > ma_50:
            score += 1
            reasons.append(f"Price above 50-day moving average, suggesting bullish trend")
        elif current_price < ma_50:
            score -= 1
            reasons.append(f"Price below 50-day moving average, suggesting bearish trend")
    else:
        warnings.append("50-day moving average data not available")


    historical_prices = data.get('historical_prices', [])
    if len(historical_prices) >= 30:

        recent_avg = sum(historical_prices[-5:]) / 5
        older_avg = sum(historical_prices[-30:-25]) / 5

        if recent_avg > older_avg * 1.1:
            score += 1
            reasons.append(f"Strong price momentum over the past month (+{((recent_avg / older_avg) - 1) * 100:.1f}%)")
        elif recent_avg < older_avg * 0.9:
            score -= 1
            reasons.append(f"Declining price trend over the past month ({((recent_avg / older_avg) - 1) * 100:.1f}%)")

    return score, reasons, warnings



def analyze_sector_performance(symbol, data, all_stocks_data):
    """Compare stock against sector averages using consistently available metrics"""
    score = 0
    reasons = []
    warnings = []

    sector = data.get('sector', 'Unknown')
    if sector == 'Unknown':
        warnings.append("Unable to perform sector analysis: sector information missing")
        return score, reasons, warnings


    reliable_metrics = {
        'roe': {'higher_better': True, 'name': 'Return on Equity'},
        'debt_to_equity': {'higher_better': False, 'name': 'Debt-to-Equity Ratio'},
        'pe_ratio': {'higher_better': False, 'name': 'P/E Ratio'},
        'pb_ratio': {'higher_better': False, 'name': 'P/B Ratio'}
    }


    sector_stocks = {}
    for sym, stock_data in all_stocks_data.items():
        if 'error' in stock_data:
            continue
        if stock_data.get('sector') == sector and sym != symbol:
            sector_stocks[sym] = stock_data

    if len(sector_stocks) < 2:
        warnings.append(f"Not enough peers in {sector} sector for comparison")
        return score, reasons, warnings


    outperformance_count = 0
    total_metrics_compared = 0

    for metric, props in reliable_metrics.items():

        if metric not in data or data[metric] is None:
            continue


        peer_values = [s[metric] for s in sector_stocks.values()
                       if metric in s and s[metric] is not None]

        if len(peer_values) < 2:
            continue


        sector_avg = sum(peer_values) / len(peer_values)
        data[f'sector_avg_{metric}'] = sector_avg


        total_metrics_compared += 1
        performance_ratio = data[metric] / sector_avg if sector_avg != 0 else 1


        if props['higher_better'] and performance_ratio > 1.2:
            score += 1
            outperformance_count += 1
            reasons.append(
                f"Superior {props['name']} ({data[metric]:.2f}) compared to sector average ({sector_avg:.2f})")


        elif not props['higher_better'] and performance_ratio < 0.8:
            score += 1
            outperformance_count += 1
            reasons.append(
                f"Superior {props['name']} ({data[metric]:.2f}) compared to sector average ({sector_avg:.2f})")


    if total_metrics_compared >= 2:
        if outperformance_count == total_metrics_compared:
            score += 1
            reasons.append(f"Outperforms sector in all {total_metrics_compared} key metrics")
    else:
        warnings.append(f"Limited sector comparison: only {total_metrics_compared} metrics available")

    return score, reasons, warnings




def analyze_dividend_policy(symbol, data):
    """Analyze dividends and payout ratio"""
    score = 0
    reasons = []
    warnings = []


    dividend_yield = data.get('dividendYield')
    if dividend_yield is not None and dividend_yield > 0:
        sector = data.get('sector', 'Unknown')
        is_high_yield_sector = any(s in sector for s in ['Utility', 'REIT', 'Energy'])

        threshold = 4 if is_high_yield_sector else 2
        if dividend_yield > threshold * 1.5:
            score += 2
            reasons.append(f"Excellent dividend yield of {dividend_yield:.2f}%")
        elif dividend_yield > threshold:
            score += 1
            reasons.append(f"Good dividend yield of {dividend_yield:.2f}%")
    else:
        warnings.append("No dividend yield data available")


    payout_ratio = data.get('payoutRatio')
    if payout_ratio is not None:
        if 30 <= payout_ratio <= 60:
            score += 1
            reasons.append(f"Healthy dividend payout ratio of {payout_ratio:.2f}%")
        elif payout_ratio > 80:
            score -= 1
            warnings.append(f"High payout ratio of {payout_ratio:.2f}% may be unsustainable")

    return score, reasons, warnings




def calculate_intrinsic_value_alternative(data):
    """Calculate intrinsic value using alternative methods based on available data"""
    methods = {}

    # Method 1: Graham's formula
    try:
        eps = data.get('eps')
        if eps and eps > 0:
            # Basic growth estimate based on industry
            sector = data.get('sector', '')
            growth_rate = 5  # Default growth rate

            if 'Technology' in sector or 'Software' in sector:
                growth_rate = 8
            elif 'Consumer' in sector:
                growth_rate = 6
            elif 'Health' in sector:
                growth_rate = 7
            elif 'Financial' in sector or 'Bank' in sector:
                growth_rate = 5

            graham_value = (eps * (8.5 + (2 * growth_rate)))
            methods['graham'] = {
                'value': graham_value,
                'description': f"Graham's formula with {growth_rate}% growth estimate"
            }
    except:
        pass


    try:
        dividend_yield = data.get('dividendYield')
        current_price = data.get('current_price')

        if dividend_yield and dividend_yield > 0 and current_price and current_price > 0:
            current_dividend = (dividend_yield / 100) * current_price


            sector = data.get('sector', '')
            growth_rate = 3

            if 'Technology' in sector or 'Software' in sector:
                growth_rate = 5
            elif 'Consumer' in sector:
                growth_rate = 4


            discount_rate = 0.10
            ddm_value = current_dividend * (1 + growth_rate / 100) / (discount_rate - growth_rate / 100)

            methods['ddm'] = {
                'value': ddm_value,
                'description': f"Dividend Discount Model with {growth_rate}% growth"
            }
    except:
        pass


    try:
        eps = data.get('eps')
        if eps and eps > 0:
            sector = data.get('sector', '')
            pe_multiple = 15

            if 'Technology' in sector:
                pe_multiple = 20
            elif 'Consumer' in sector:
                pe_multiple = 18
            elif 'Utilities' in sector:
                pe_multiple = 14
            elif 'Financial' in sector:
                pe_multiple = 12

            pe_value = eps * pe_multiple
            methods['pe_multiple'] = {
                'value': pe_value,
                'description': f"P/E Multiple Method ({pe_multiple}x earnings)"
            }
    except:
        pass


    try:
        book_value = data.get('bookValue')
        if book_value and book_value > 0:
            sector = data.get('sector', '')
            pb_multiple = 1.5

            if 'Financial' in sector or 'Bank' in sector:
                pb_multiple = 1.2
            elif 'Technology' in sector:
                pb_multiple = 3.0
            elif 'Consumer' in sector:
                pb_multiple = 2.5

            book_value_based = book_value * pb_multiple
            methods['book_value'] = {
                'value': book_value_based,
                'description': f"Book Value Method ({pb_multiple}x book value)"
            }
    except:
        pass

    return methods


def calculate_final_intrinsic_value(data, alternative_methods):
    """Calculate final intrinsic value based on available methods"""
    intrinsic_value = data.get('intrinsic_value', 0)

    if not intrinsic_value or intrinsic_value == 0:
        if alternative_methods:
            values = [method_data['value'] for method_data in alternative_methods.values()]

            if values:
                # Use median instead of mean to avoid outliers
                intrinsic_value = statistics.median(values)

                current_price = data.get('current_price', 0) or 0
                if current_price > 0 and intrinsic_value > current_price:
                    margin_of_safety = ((intrinsic_value - current_price) / intrinsic_value) * 100
                else:
                    margin_of_safety = 0

                return intrinsic_value, margin_of_safety, alternative_methods

    return intrinsic_value, data.get('margin_of_safety', 0), alternative_methods


# ----- INTEGRATED ANALYSIS FUNCTION -----

def buffett_analysis(stock_data):
    buffett_picks = {}
    detailed_analysis = {}

    for symbol, data in stock_data.items():
        if 'error' in data:
            continue


        buffett_score = 0
        technical_score = 0
        buffett_reasons = []
        technical_reasons = []
        warnings = []
        missing_data = []
        qualitative_factors = {}

        # Check for missing key metrics
        for key_metric in ['roe', 'debt_to_equity', 'pe_ratio', 'market_cap', 'current_price']:
            if key_metric not in data or data[key_metric] is None:
                missing_data.append(key_metric)


        if data.get('debt_to_equity') and data['debt_to_equity'] > 3:
            data['debt_to_equity'] = data['debt_to_equity'] / 100

        # ----- FUNDAMENTAL ANALYSIS (BUFFETT CRITERIA) -----

        # 1. Analyze operating efficiency
        efficiency_score, efficiency_reasons, efficiency_warnings = analyze_operating_efficiency(symbol, data)
        buffett_score += efficiency_score
        buffett_reasons.extend(efficiency_reasons)
        warnings.extend(efficiency_warnings)

        # 2. Analyze financial health
        health_score, health_reasons, health_warnings = analyze_financial_health(symbol, data)
        buffett_score += health_score
        buffett_reasons.extend(health_reasons)
        warnings.extend(health_warnings)

        # 3. Analyze valuation
        valuation_score, valuation_reasons, valuation_warnings = analyze_valuation(symbol, data)
        buffett_score += valuation_score
        buffett_reasons.extend(valuation_reasons)
        warnings.extend(valuation_warnings)

        # 4. Analyze qualitative factors
        industry_score, industry_reason = analyze_industry_dynamics(symbol, data)
        qualitative_factors['industry_dynamics'] = {
            'score': industry_score,
            'reason': industry_reason
        }
        buffett_score += industry_score
        if industry_score > 0:
            buffett_reasons.append(industry_reason)
        elif industry_score < 0:
            warnings.append(industry_reason)

        regulatory_score, regulatory_reason = analyze_regulatory_environment(symbol, data)
        qualitative_factors['regulatory_environment'] = {
            'score': regulatory_score,
            'reason': regulatory_reason
        }
        buffett_score += regulatory_score
        if regulatory_score > 0:
            buffett_reasons.append(regulatory_reason)
        elif regulatory_score < 0:
            warnings.append(regulatory_reason)

        macro_score, macro_reason = analyze_macroeconomic_factors(symbol, data)
        qualitative_factors['macroeconomic_factors'] = {
            'score': macro_score,
            'reason': macro_reason
        }
        buffett_score += macro_score
        if macro_score > 0:
            buffett_reasons.append(macro_reason)
        elif macro_score < 0:
            warnings.append(macro_reason)

        moat_score, moat_reason = analyze_economic_moat(symbol, data)
        qualitative_factors['economic_moat'] = {
            'score': moat_score,
            'reason': moat_reason
        }
        buffett_score += moat_score
        if moat_score > 0:
            buffett_reasons.append(moat_reason)
        elif moat_score < 0:
            warnings.append(moat_reason)

        # ----- CALCULATE INTRINSIC VALUE -----
        alternative_valuation_methods = calculate_intrinsic_value_alternative(data)
        intrinsic_value, margin_of_safety, valuation_methods = calculate_final_intrinsic_value(
            data, alternative_valuation_methods)

        if intrinsic_value and intrinsic_value > 0:
            data['intrinsic_value'] = intrinsic_value
            data['margin_of_safety'] = margin_of_safety
            data['valuation_methods'] = valuation_methods


            if margin_of_safety > 40:
                buffett_score += 4
                buffett_reasons.append(f"Huge margin of safety: {margin_of_safety:.2f}%")
            elif margin_of_safety > 30:
                buffett_score += 3
                buffett_reasons.append(f"Substantial margin of safety: {margin_of_safety:.2f}%")
            elif margin_of_safety > 20:
                buffett_score += 2
                buffett_reasons.append(f"Good margin of safety: {margin_of_safety:.2f}%")
            elif margin_of_safety > 10:
                buffett_score += 1
                buffett_reasons.append(f"Some margin of safety: {margin_of_safety:.2f}%")

        # ----- TECHNICAL ANALYSIS (OPTIONAL) -----

        # 1. Analyze technical indicators
        tech_score, tech_reasons, tech_warnings = analyze_technical_indicators(symbol, data)
        technical_score += tech_score
        technical_reasons.extend(tech_reasons)
        warnings.extend(tech_warnings)

        # 2. Sector comparison (using available metrics)
        sector_score, sector_reasons, sector_warnings = analyze_sector_performance(symbol, data, stock_data)
        technical_score += sector_score
        technical_reasons.extend(sector_reasons)
        warnings.extend(sector_warnings)

        # 3. Dividend analysis
        dividend_score, dividend_reasons, dividend_warnings = analyze_dividend_policy(symbol, data)
        technical_score += dividend_score
        technical_reasons.extend(dividend_reasons)
        warnings.extend(dividend_warnings)

        # ----- CALCULATE TOTAL SCORE -----
        total_score = buffett_score + technical_score

        # Record detailed analysis for all stocks
        detailed_analysis[symbol] = {
            'name': data['name'],
            'sector': data.get('sector', 'Unknown'),
            'buffett_score': buffett_score,
            'technical_score': technical_score,
            'total_score': total_score,
            'buffett_reasons': buffett_reasons,
            'technical_reasons': technical_reasons,
            'warnings': warnings,
            'missing_data': missing_data
        }

        # Add to picks if it meets the threshold
        if total_score >= 16:
            buffett_picks[symbol] = {
                'name': data['name'],
                'sector': data.get('sector', 'Unknown'),
                'price': data.get('current_price', 0),
                'intrinsic_value': data.get('intrinsic_value', 0),
                'margin_of_safety': data.get('margin_of_safety', 0),
                'pe_ratio': data.get('pe_ratio', 0),
                'roe': data.get('roe', 0),
                'debt_to_equity': data.get('debt_to_equity', 0),
                'market_cap': data.get('market_cap', 0),
                'buffett_score': buffett_score,
                'technical_score': technical_score,
                'total_score': total_score,
                'buffett_reasons': buffett_reasons,
                'technical_reasons': technical_reasons,
                'warnings': warnings,
                'missing_data': missing_data,
                'qualitative_factors': qualitative_factors,
                'valuation_methods': data.get('valuation_methods', {}),
                'technical_indicators': {
                    'rsi': data.get('rsi'),
                    'ma_50': data.get('ma_50')
                }
            }


    os.makedirs('data', exist_ok=True)
    with open('data/detailed_analysis.json', 'w') as f:
        json.dump(detailed_analysis, f, indent=2)

    # Sort picks by total score
    sorted_picks = dict(sorted(buffett_picks.items(), key=lambda x: x[1]['total_score'], reverse=True))
    return sorted_picks


def increment_visit_count():
    """Track the number of visits to the analysis page"""
    visit_file = 'data/visit_counter.json'
    today = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d')

    try:
        if os.path.exists(visit_file):
            with open(visit_file, 'r') as f:
                visit_data = json.load(f)
        else:
            visit_data = {'total_visits': 0, 'daily_visits': {}}

        visit_data['total_visits'] += 1

        if today in visit_data['daily_visits']:
            visit_data['daily_visits'][today] += 1
        else:
            visit_data['daily_visits'][today] = 1

        with open(visit_file, 'w') as f:
            json.dump(visit_data, f, indent=2)

        return visit_data['total_visits'], visit_data['daily_visits'][today]
    except Exception as e:
        print(f"Error tracking visits: {e}")
        return 1, 1


def generate_html_report(buffett_picks):
    """Generate HTML report of Buffett picks"""
    total_visits, today_visits = increment_visit_count()

    # Format time
    ist_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    formatted_time = ist_time.strftime("%I:%M %p, %d %b %Y")

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enhanced Indian Stock Analysis Disclaimer not investment advice do your own analysis and research - Buffett + Technical</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.0/font/bootstrap-icons.css">
        <style>
            body { padding: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .stock-card { 
                margin-bottom: 20px; 
                transition: transform 0.3s; 
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .stock-card:hover { 
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }
            .reasons { font-size: 0.9rem; }
            .warnings { font-size: 0.9rem; color: #dc3545; }
            .missing-data { font-size: 0.9rem; color: #fd7e14; }
            .data-quality { font-size: 0.9rem; color: #6f42c1; }
            .card-header { 
                border-top-left-radius: 10px !important;
                border-top-right-radius: 10px !important;
                background-color: #f8f9fa;
                border-bottom: 1px solid rgba(0,0,0,0.125);
            }
            .buffett-quote {
                font-style: italic;
                color: #6c757d;
                border-left: 4px solid #20c997;
                padding-left: 1rem;
                margin: 1.5rem 0;
            }
            .filters {
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            .badge-buffett {
                background-color: #FFD700;
                color: #212529;
            }
            .badge-technical {
                background-color: #20c997;
                color: #212529;
            }
            .ticker-symbol {
                font-weight: bold;
                color: #0d6efd;
                cursor: pointer;
            }
            .qualitative-section {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 12px;
                margin-top: 15px;
            }
            .technical-section {
                background-color: #e9f7f2;
                border-radius: 8px;
                padding: 12px;
                margin-top: 15px;
            }
            .qualitative-item {
                padding: 8px 0;
                border-bottom: 1px solid #e9ecef;
            }
            .qualitative-item:last-child {
                border-bottom: none;
            }
            .qualitative-score {
                font-weight: bold;
                float: right;
            }
            .positive-score { color: #198754; }
            .negative-score { color: #dc3545; }
            .neutral-score { color: #6c757d; }
            .data-error {
                background-color: #fff3cd;
                border-radius: 8px;
                padding: 12px;
                margin-top: 15px;
                color: #664d03;
                border: 1px solid #ffe69c;
            }
            .debug-info {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
                margin-top: 10px;
                font-family: monospace;
                font-size: 0.8rem;
            }
            .collapsible-section {
                cursor: pointer;
            }
            .collapsible-content {
                max-height: 0;
                overflow: hidden;
                transition: max-height 0.2s ease-out;
            }
            .valuation-methods {
                background-color: #e8f4f8;
                border-radius: 8px;
                padding: 12px;
                margin-top: 15px;
                font-size: 0.9rem;
            }
            .search-container {
                margin-bottom: 20px;
            }
            .visit-counter {
                font-size: 0.8rem;
                color: #6c757d;
                text-align: right;
                margin-bottom: 10px;
            }
            .score-pill {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                margin-right: 5px;
                font-weight: bold;
                text-align: center;
                min-width: 80px;
            }
            .nav-tabs .nav-link {
                border-radius: 8px 8px 0 0;
            }
            .nav-tabs .nav-link.active {
                font-weight: bold;
            }
            .data-warning-badge {
                padding: 0.25rem 0.5rem;
                font-size: 0.75rem;
                font-weight: 600;
                position: absolute;
                top: 10px;
                right: 10px;
                border-radius: 50px;
                background-color: #fff3cd;
                color: #664d03;
                border: 1px solid #ffe69c;
                z-index: 10;
            }
            .warning-icon {
                color: #dc3545;
                margin-right: 5px;
            }
            .disclaimer-badge {
                font-size: 0.75rem;
                display: inline-block;
                margin-left: 8px;
                padding: 2px 6px;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row mt-4 mb-2">
                <div class="col-md-8">
                    <h1 class="display-4">Enhanced Indian Stock Analysis -Disclaimer not investment advice do your own analysis and research</h1>
                    <p class="text-muted">Combining Buffett's principles with technical indicators | Last updated: """ + formatted_time + """</p>
                </div>
                <div class="col-md-4">
                    <div class="visit-counter text-end">
                        <span><i class="bi bi-eye"></i> Today: """ + str(today_visits) + """ visits</span><br>
                        <span><i class="bi bi-graph-up"></i> Total: """ + str(total_visits) + """ visits</span>
                    </div>
                </div>
            </div>

            <div class="alert alert-warning">
                <strong><i class="bi bi-exclamation-triangle-fill"></i> Data Quality Disclaimer:</strong> 
                This analysis relies on the accuracy of data from various sources. When metrics are missing or suspicious values are detected, 
                a warning flag <span class="badge bg-warning text-dark"><i class="bi bi-exclamation-triangle"></i></span> will be displayed. 
                Always verify important data points before making investment decisions.
            </div>

            <div class="buffett-quote">
                "Price is what you pay. Value is what you get." - Warren Buffett
            </div>

            <div class="search-container">
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-search"></i></span>
                    <input type="text" class="form-control" id="stockSearch" placeholder="Search by company name, symbol, or sector...">
                    <button class="btn btn-outline-secondary" type="button" onclick="clearSearch()">Clear</button>
                </div>
            </div>

            <div class="filters p-3 mb-4">
                <ul class="nav nav-tabs" id="analysisTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="buffett-tab" data-bs-toggle="tab" data-bs-target="#buffett-principles" type="button" role="tab">Buffett's Principles</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="technical-tab" data-bs-toggle="tab" data-bs-target="#technical-factors" type="button" role="tab">Technical Factors</button>
                    </li>
                </ul>

                <div class="tab-content pt-3" id="analysisTabsContent">
                    <div class="tab-pane fade show active" id="buffett-principles" role="tabpanel">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Quantitative Factors:</h6>
                                <ol>
                                    <li>Circle of Competence: Only invest in businesses you understand</li>
                                    <li>Margin of Safety: Buy companies at a significant discount to intrinsic value</li>
                                    <li>Financial Strength: Low debt, high ROE, consistent earnings</li>
                                    <li>Economic Moat: Companies with sustainable competitive advantages</li>
                                </ol>
                            </div>
                            <div class="col-md-6">
                                <h6>Qualitative Factors:</h6>
                                <ol>
                                    <li>Industry Dynamics: Understanding competitive forces in the industry</li>
                                    <li>Regulatory Environment: Assessing impact of regulations on business</li>
                                    <li>Macroeconomic Factors: Considering overall economic outlook</li>
                                    <li>Corporate Governance: Management transparency and accountability</li>
                                    <li>India Cultural Fit: Local market understanding and adaptation</li>
                                    <li>Economic Moat: Sustainable competitive advantages</li>
                                    <li>Owner-Oriented Management: Insider ownership and capital allocation</li>
                                </ol>
                            </div>
                        </div>
                    </div>
                    <div class="tab-pane fade" id="technical-factors" role="tabpanel">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Technical Indicators:</h6>
                                <ol>
                                    <li>RSI (Relative Strength Index): Identifies overbought/oversold conditions</li>
                                    <li>Moving Averages: 50-day MA for trends and support/resistance</li>
                                    <li>Price Momentum: Recent trend strength analysis</li>
                                </ol>
                            </div>
                            <div class="col-md-6">
                                <h6>Additional Analysis:</h6>
                                <ol>
                                    <li>Sector Performance: Comparison against sector averages</li>
                                    <li>Dividend Analysis: Dividend yield and payout sustainability</li>
                                    <li>Valuation Metrics: P/E ratio, P/B ratio evaluation</li>
                                </ol>
                            </div>
                        </div>
                    </div>
                </div>

                <p class="small mb-0 mt-3">Stocks are scored based on both fundamental Buffett principles and technical indicators. Minimum threshold: 10 total points.</p>
            </div>

            <div class="row" id="stockContainer">
    """

    total_market_cap = sum(data.get('market_cap', 0) or 0 for data in buffett_picks.values())
    total_market_cap_billions = total_market_cap / 1_000_000_000

    html += f"""
            <div class="col-12 mb-4">
                <div class="alert alert-info">
                    <strong>Found {len(buffett_picks)} companies</strong> matching enhanced investment criteria 
                    with a combined market cap of ₹{total_market_cap_billions:,.2f} billion.
                </div>
            </div>
    """

    for symbol, data in buffett_picks.items():
        display_symbol = symbol.replace('.NS', '').replace('.BO', '')
        exchange = "NSE" if '.NS' in symbol else "BSE" if '.BO' in symbol else "Unknown"

        market_cap = data.get('market_cap', 0) or 0
        market_cap_billions = market_cap / 1_000_000_000

        price = data.get('price', 0) or 0
        intrinsic_value = data.get('intrinsic_value', 0) or 0
        margin_of_safety = data.get('margin_of_safety', 0) or 0
        pe_ratio = data.get('pe_ratio', 0) or 0
        roe = data.get('roe', 0) or 0
        debt_to_equity = data.get('debt_to_equity', 0) or 0

        buffett_score = data.get('buffett_score', 0) or 0
        technical_score = data.get('technical_score', 0) or 0
        total_score = data.get('total_score', 0) or 0

        buffett_class = "success"
        if buffett_score >= 15:
            buffett_class = "success"
            buffett_text = "Excellent"
        elif buffett_score >= 12:
            buffett_class = "primary"
            buffett_text = "Very Good"
        elif buffett_score >= 10:
            buffett_class = "info"
            buffett_text = "Good"
        else:
            buffett_class = "secondary"
            buffett_text = "Fair"

        technical_class = "success"
        if technical_score >= 10:
            technical_class = "success"
            technical_text = "Excellent"
        elif technical_score >= 7:
            technical_class = "primary"
            technical_text = "Very Good"
        elif technical_score >= 4:
            technical_class = "info"
            technical_text = "Good"
        else:
            technical_class = "secondary"
            technical_text = "Fair"

        total_class = "success"
        if total_score >= 25:
            total_class = "success"
            total_text = "Excellent"
        elif total_score >= 20:
            total_class = "primary"
            total_text = "Very Good"
        elif total_score >= 15:
            total_class = "info"
            total_text = "Good"
        else:
            total_class = "secondary"
            total_text = "Fair"

        qualitative_factors = data.get('qualitative_factors', {})
        technical_indicators = data.get('technical_indicators', {})

        missing_data = data.get('missing_data', [])
        warnings_list = data.get('warnings', [])

        has_missing_data = len(missing_data) > 0
        has_warnings = len(warnings_list) > 0
        has_data_warnings = has_missing_data or has_warnings

        valuation_methods = data.get('valuation_methods', {})
        has_alternative_valuations = len(valuation_methods) > 0

        html += f"""
                <div class="col-md-6 col-lg-4 stock-card-container" 
                     data-name="{data['name'].lower()}" 
                     data-symbol="{display_symbol.lower()}"
                     data-sector="{data['sector'].lower()}">
                    <div class="card stock-card position-relative">
                        {f'<span class="data-warning-badge"><i class="bi bi-exclamation-triangle"></i> Data warnings</span>' if has_data_warnings else ''}
                        <div class="card-header">
                            <h5 class="card-title mb-0">{data['name']}</h5>
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="ticker-symbol" onclick="window.open('https://www.nseindia.com/get-quotes/equity?symbol={display_symbol}', '_blank')">{display_symbol}</span>
                                    <span class="badge bg-secondary">{exchange}</span>
                                </div>
                                <div>
                                    <span class="badge bg-{total_class}">Total: {total_score:.1f}</span>
                                </div>
                            </div>
                        </div>
                        <div class="card-body">
                            <h6 class="card-subtitle mb-3 text-muted">{data['sector']}</h6>

                            <div class="d-flex justify-content-between mb-3">
                                <span class="score-pill bg-warning bg-opacity-25">Buffett: {buffett_score:.1f}</span>
                                <span class="score-pill bg-info bg-opacity-25">Technical: {technical_score:.1f}</span>
                                <span class="score-pill bg-success bg-opacity-25">Total: {total_score:.1f}</span>
                            </div>
        """

        if has_missing_data:
            html += f"""
                            <div class="data-error mb-3">
                                <strong><i class="bi bi-exclamation-triangle"></i> Missing Data:</strong> 
                                <span>{', '.join(missing_data)}</span>
                            </div>
            """

        html += f"""                    
                            <div class="row mb-1">
                                <div class="col-6">Current Price:</div>
                                <div class="col-6 text-end fw-bold">₹{price:,.2f}</div>
                            </div>

                            <div class="row mb-1">
                                <div class="col-6">Intrinsic Value:</div>
                                <div class="col-6 text-end fw-bold">
                                    ₹{intrinsic_value:,.2f}
                                    {f'<span class="disclaimer-badge bg-warning text-dark" data-bs-toggle="tooltip" title="Using multiple valuation methods"><i class="bi bi-info-circle"></i></span>' if has_alternative_valuations else ''}
                                </div>
                            </div>

                            <div class="row mb-1">
                                <div class="col-6">Margin of Safety:</div>
                                <div class="col-6 text-end fw-bold">{margin_of_safety:.2f}%</div>
                            </div>

                            <div class="row mb-1">
                                <div class="col-6">P/E Ratio:</div>
                                <div class="col-6 text-end fw-bold">{pe_ratio:.2f}</div>
                            </div>

                            <div class="row mb-1">
                                <div class="col-6">ROE:</div>
                                <div class="col-6 text-end fw-bold">{roe:.2f}%</div>
                            </div>

                            <div class="row mb-1">
                                <div class="col-6">Debt-to-Equity:</div>
                                <div class="col-6 text-end fw-bold">{debt_to_equity:.2f}</div>
                            </div>

                            <div class="row mb-1">
                                <div class="col-6">Market Cap:</div>
                                <div class="col-6 text-end fw-bold">₹{market_cap_billions:.2f}B</div>
                            </div>
        """

        # Display technical indicators if available
        rsi = technical_indicators.get('rsi')
        ma_50 = technical_indicators.get('ma_50')

        has_technical_data = rsi is not None or ma_50 is not None

        if has_technical_data:
            html += """
                            <div class="technical-section mt-3 mb-3">
                                <h6 class="mb-2"><i class="bi bi-graph-up"></i> Technical Indicators:</h6>
                                <div class="row">
            """

            if rsi is not None:
                rsi_class = "success" if 30 <= rsi <= 70 else "danger" if rsi > 70 else "warning"
                html += f"""
                                    <div class="col-6 text-center">
                                        <small>RSI</small>
                                        <div class="text-{rsi_class} fw-bold">{rsi:.1f}</div>
                                    </div>
                """

            if ma_50 is not None and price:
                ma_status = "Above MA" if price > ma_50 else "Below MA"
                ma_class = "success" if price > ma_50 else "danger"
                html += f"""
                                    <div class="col-6 text-center">
                                        <small>50-day MA</small>
                                        <div class="text-{ma_class} fw-bold">{ma_status}</div>
                                    </div>
                """

            html += """
                                </div>
                            </div>
            """
        else:
            html += """
                            <div class="alert alert-secondary mt-3 mb-3 py-2">
                                <small><i class="bi bi-info-circle"></i> Technical indicator data not available</small>
                            </div>
            """

        if has_alternative_valuations:
            html += """
                            <div class="valuation-methods collapsible-section" onclick="toggleSection(this)">
                                <strong><i class="bi bi-calculator"></i> Valuation Methods (Click to expand)</strong>
                                <div class="collapsible-content">
                                    <ul class="mt-2 mb-0">
            """
            for method_name, method_data in valuation_methods.items():
                method_value = method_data.get('value', 0)
                method_desc = method_data.get('description', '')
                html += f"""
                                        <li><strong>{method_name.capitalize()}</strong>: ₹{method_value:,.2f} 
                                            <div><small class="text-muted">{method_desc}</small></div>
                                        </li>
                """
            html += """
                                    </ul>
                                </div>
                            </div>
            """

        # Add tabbed content for Buffett and Technical reasons
        html += """
                            <ul class="nav nav-tabs mt-4" role="tablist">
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#buffett-reasons-""" + display_symbol + """" type="button" role="tab">Buffett Analysis</button>
                                </li>
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#technical-reasons-""" + display_symbol + """" type="button" role="tab">Technical Analysis</button>
                                </li>
                            </ul>

                            <div class="tab-content mt-3">
                                <div class="tab-pane fade show active" id="buffett-reasons-""" + display_symbol + """" role="tabpanel">
                                    <h6 class="mb-2">Why Buffett Would Like It:</h6>
        """

        buffett_reasons = data.get('buffett_reasons', [])
        if buffett_reasons:
            html += """
                                    <ul class="reasons">
            """
            for reason in buffett_reasons:
                html += f"                                        <li>{reason}</li>\n"
            html += """
                                    </ul>
            """
        else:
            html += """
                                    <p class="text-muted"><small>No specific Buffett criteria found.</small></p>
            """

        html += """
                                </div>
                                <div class="tab-pane fade" id="technical-reasons-""" + display_symbol + """" role="tabpanel">
                                    <h6 class="mb-2">Technical & Quantitative Factors:</h6>
        """

        technical_reasons = data.get('technical_reasons', [])
        if technical_reasons:
            html += """
                                    <ul class="reasons">
            """
            for reason in technical_reasons:
                html += f"                                        <li>{reason}</li>\n"
            html += """
                                    </ul>
            """
        else:
            html += """
                                    <p class="text-muted"><small>No technical analysis data available.</small></p>
            """

        html += """
                                </div>
                            </div>
        """

        if warnings_list:
            html += """
                            <div class="mt-3">
                                <h6 class="text-danger"><i class="bi bi-exclamation-triangle"></i> Potential Concerns:</h6>
                                <ul class="warnings">
            """

            for warning in warnings_list:
                html += f"                                    <li>{warning}</li>\n"

            html += """
                                </ul>
                            </div>
            """

        html += """
                        </div>
                    </div>
                </div>
        """

    # Close the container and add scripts
    html += """
            </div>

            <div class="row mt-5 mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <h4>Enhanced Investment Philosophy</h4>
                            <p>This analysis combines Warren Buffett's value investing approach with technical indicators and quantitative metrics to provide a comprehensive view of potential investments.</p>

                            <div class="row">
                                <div class="col-md-6">
                                    <h5>Buffett's Value Approach</h5>
                                    <ul>
                                        <li><strong>Simple, Understandable Business Models</strong></li>
                                        <li><strong>Consistent Operating History</strong></li>
                                        <li><strong>Financial Strength</strong></li>
                                        <li><strong>Margin of Safety</strong></li>
                                        <li><strong>Economic Moat</strong></li>
                                    </ul>
                                </div>

                                <div class="col-md-6">
                                    <h5>Technical & Quantitative Factors</h5>
                                    <ul>
                                        <li><strong>Technical Indicators</strong>: RSI, Moving Averages</li>
                                        <li><strong>Sector Performance</strong>: Comparison against peers and sector trends</li>
                                        <li><strong>Dividend Analysis</strong>: Yield and payout sustainability</li>
                                        <li><strong>Valuation Metrics</strong>: P/E ratio, P/B ratio analysis</li>
                                    </ul>
                                </div>
                            </div>

                            <div class="alert alert-warning mt-3">
                                <strong>Data Quality Disclaimer:</strong> This analysis uses various data sources which may contain inaccuracies or missing information.
                                When data appears suspicious or important metrics are missing, disclaimers are displayed. Always conduct your own research 
                                and verify key metrics before making investment decisions.
                            </div>

                            <p>Remember these investment principles:</p>
                            <div class="buffett-quote">"Be fearful when others are greedy, and greedy when others are fearful." - Warren Buffett</div>
                            <div class="buffett-quote">"The trend is your friend until the end when it bends." - Ed Seykota</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="bg-light py-3 mt-5">
            <div class="container text-center">
                <p class="mb-0 text-muted">This analysis is for educational purposes only. Always do your own research before making investment decisions.</p>
                <p class="mb-0 text-muted small">Updated daily after market close.</p>
            </div>
        </footer>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Search functionality
            document.getElementById('stockSearch').addEventListener('input', function(e) {
                const searchTerm = e.target.value.toLowerCase().trim();
                const stockCards = document.querySelectorAll('.stock-card-container');

                stockCards.forEach(card => {
                    const name = card.getAttribute('data-name');
                    const symbol = card.getAttribute('data-symbol');
                    const sector = card.getAttribute('data-sector');

                    if (name.includes(searchTerm) || symbol.includes(searchTerm) || sector.includes(searchTerm)) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });

            function clearSearch() {
                document.getElementById('stockSearch').value = '';
                const stockCards = document.querySelectorAll('.stock-card-container');
                stockCards.forEach(card => {
                    card.style.display = 'block';
                });
            }

            // Toggle collapsible sections
            function toggleSection(element) {
                const content = element.querySelector('.collapsible-content');
                if (content.style.maxHeight) {
                    content.style.maxHeight = null;
                } else {
                    content.style.maxHeight = content.scrollHeight + "px";
                }
            }

            // Initialize tooltips
            document.addEventListener('DOMContentLoaded', function() {
                // Auto-expand collapsible sections with warnings for better visibility
                const dataWarningCards = document.querySelectorAll('.stock-card:has(.data-warning-badge)');
                dataWarningCards.forEach(card => {
                    const collapsibles = card.querySelectorAll('.collapsible-section');
                    collapsibles.forEach(section => {
                        const content = section.querySelector('.collapsible-content');
                        if (content) {
                            content.style.maxHeight = content.scrollHeight + "px";
                        }
                    });
                });

                // Initialize tooltips
                var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                    return new bootstrap.Tooltip(tooltipTriggerEl);
                });
            });
        </script>
    </body>
    </html>
    """

    os.makedirs('output', exist_ok=True)

    with open('output/index.html', 'w') as f:
        f.write(html)

    print("Enhanced HTML report generated at output/index.html")


if __name__ == "__main__":
    print("Starting enhanced Buffett analysis")
    stock_data = load_latest_data()
    buffett_picks = buffett_analysis(stock_data)
    generate_html_report(buffett_picks)
    print(f"Analysis complete. Found {len(buffett_picks)} stocks matching Buffett criteria.")

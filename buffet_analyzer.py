import json
import os
from datetime import datetime
import pytz
import re


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

    high_concentration_keywords = [
        'monopoly', 'duopoly', 'market leader', 'dominant', 'leading'
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

    company_name = data.get('name', '')
    company_desc = data.get('longBusinessSummary', '')

    if company_desc and any(
            keyword in (company_name + company_desc).lower() for keyword in high_concentration_keywords):
        score += 1
        reason += ". Appears to have strong market position"

    return score, reason


def analyze_regulatory_environment(symbol, data):
    sector = data.get('sector', 'Unknown')

    stable_regulatory_sectors = [
        'Consumer Staples', 'Consumer Goods', 'Insurance', 'Banking',
        'Financial Services', 'Utilities','Pharmaceutical'
    ]

    challenging_regulatory_sectors = [
        'Healthcare', 'Telecom', 'Energy', 'Banking',
        'Technology', 'Oil & Gas'
    ]

    if '.NS' in symbol:
        india_favorable_sectors = [
            'IT Services', 'Technology', 'Consumer Goods', 'Automotive' 'Pharmaceutical'
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


def analyze_corporate_governance(symbol, data):
    name = data.get('name', '')

    family_name_indicators = ["Tata", "Birla", "Ambani", "Bajaj", "Mahindra", "Godrej", "Hinduja", "Adani"]
    is_family_business = any(family in name for family in family_name_indicators)

    market_cap = data.get('market_cap', 0)
    market_cap_billions = market_cap / 1_000_000_000 if market_cap else 0

    dividend_yield = data.get('dividendYield', 0)
    has_dividend = dividend_yield and dividend_yield > 0

    score = 0
    reasons = []

    if is_family_business:
        score += 1
        reasons.append("Family-owned business with long-term focus")

    if market_cap_billions > 50:
        score += 1
        reasons.append("Large established company with likely strong governance controls")
    elif market_cap_billions > 10:
        score += 0.5
        reasons.append("Mid-sized company with established governance structures")

    if has_dividend:
        score += 1
        reasons.append("Pays dividend, indicating shareholder-friendly management")

    if not reasons:
        reasons.append("Neutral corporate governance assessment")

    return score, ", ".join(reasons)


def analyze_india_cultural_fit(symbol, data):
    name = data.get('name', '')
    sector = data.get('sector', 'Unknown')

    is_indian_company = '.NS' in symbol

    culturally_aligned_sectors = [
        'Consumer Goods', 'Food', 'Retail', 'Textiles', 'FMCG',
        'Automotive', 'Entertainment', 'Media'
    ]

    local_adaptation_sectors = [
        'Financial Services', 'Banking', 'Insurance', 'Healthcare'
    ]

    rural_market_keywords = [
        'rural', 'village', 'tier 3', 'tier-3', 'bharat', 'gram', 'panchayat'
    ]

    company_desc = data.get('longBusinessSummary', '').lower() if data.get('longBusinessSummary') else ''
    has_rural_focus = any(keyword in company_desc for keyword in rural_market_keywords)

    trusted_indian_conglomerates = [
        'Tata', 'Birla', 'Reliance', 'Mahindra', 'Bajaj', 'ITC',
        'Godrej', 'Infosys', 'Wipro', 'HDFC'
    ]

    has_trusted_brand = any(brand in name for brand in trusted_indian_conglomerates)

    score = 0
    reasons = []

    if is_indian_company:
        score += 1
        reasons.append("Indian company with inherent understanding of local market")

        if any(ind in sector for ind in culturally_aligned_sectors):
            score += 1
            reasons.append(f"Strong cultural alignment in {sector} sector")

        if has_rural_focus:
            score += 1
            reasons.append("Demonstrated focus on rural Indian markets")

        if has_trusted_brand:
            score += 1
            reasons.append("Trusted Indian brand with established cultural relevance")
    else:
        if has_rural_focus:
            score += 1
            reasons.append("Foreign company with demonstrated rural India focus")

        if any(ind in sector for ind in local_adaptation_sectors):
            score -= 1
            reasons.append(f"Foreign company in {sector} sector that requires deep local knowledge")

    if not reasons:
        if is_indian_company:
            reasons.append("Indian company with neutral cultural fit assessment")
        else:
            reasons.append("Foreign company with unassessed cultural adaptation")

    return score, ", ".join(reasons)


def analyze_economic_moat(symbol, data):
    name = data.get('name', '')
    sector = data.get('sector', 'Unknown')
    profit_margin = data.get('profit_margin', 0) or 0
    roe = data.get('roe', 0) or 0
    company_desc = data.get('longBusinessSummary', '').lower() if data.get('longBusinessSummary') else ''

    high_margin = profit_margin > 20
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

    moat_keywords = {
        'brand': ['brand', 'premium', 'loyalty', 'trusted', 'heritage'],
        'network': ['network effect', 'platform', 'marketplace', 'ecosystem'],
        'switching': ['switching cost', 'customer lock-in', 'retention', 'stickiness'],
        'cost': ['low cost', 'scale advantage', 'efficient', 'market share']
    }

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

    if high_margin:
        score += 1
        moat_types.append(f"High profit margin ({profit_margin:.1f}%) suggests pricing power")

    if exceptional_roe:
        score += 1
        moat_types.append(f"Exceptional ROE ({roe:.1f}%) indicates sustainable competitive advantage")

    for moat_type, keywords in moat_keywords.items():
        if any(keyword in company_desc for keyword in keywords):
            score += 0.5
            moat_types.append(f"Potential {moat_type} advantage indicated")

    score = min(score, 4)

    if not moat_types:
        moat_types.append("No clear economic moat identified")

    return score, ", ".join(moat_types)


def analyze_owner_oriented_management(symbol, data):
    name = data.get('name', '')

    family_owned_indicators = ["Tata", "Birla", "Ambani", "Bajaj", "Mahindra",
                               "Godrej", "Hinduja", "Adani", "Premji"]

    is_family_owned = any(family in name for family in family_owned_indicators)

    insider_ownership = data.get('heldPercentInsiders', 0)

    buyback_keywords = ['buyback', 'share repurchase', 'treasury stock']
    company_desc = data.get('longBusinessSummary', '').lower() if data.get('longBusinessSummary') else ''

    recent_buybacks = any(keyword in company_desc for keyword in buyback_keywords)

    score = 0
    reasons = []

    if is_family_owned:
        score += 1
        reasons.append("Family-owned or founder-led business with long-term orientation")

    if insider_ownership > 0:
        if insider_ownership > 0.25:
            score += 2
            reasons.append(f"High insider ownership ({insider_ownership * 100:.1f}%)")
        elif insider_ownership > 0.10:
            score += 1
            reasons.append(f"Moderate insider ownership ({insider_ownership * 100:.1f}%)")

    if recent_buybacks:
        score += 1
        reasons.append("History of share repurchases indicates shareholder-friendly capital allocation")

    if '.NS' in symbol:
        dividend_yield = data.get('dividendYield', 0)
        if dividend_yield and dividend_yield > 0:
            if dividend_yield > 3:
                score += 1
                reasons.append(f"Strong dividend yield ({dividend_yield:.1f}%) indicates shareholder-friendly policies")
            elif dividend_yield > 1:
                score += 0.5
                reasons.append(f"Modest dividend yield ({dividend_yield:.1f}%) indicates shareholder return focus")

    if not reasons:
        reasons.append("Insufficient information on management orientation")

    return score, ", ".join(reasons)


def check_recent_performance_decline(symbol, data):
    earnings_growth = data.get('earningsGrowth', 0)
    revenue_growth = data.get('revenueGrowth', 0)
    earnings_quarterly_growth = data.get('earningsQuarterlyGrowth', 0)

    score_penalty = 0
    reasons = []

    if earnings_growth is not None and earnings_growth < -0.05:
        score_penalty -= 3
        reasons.append(f"Recent earnings decline of {earnings_growth * 100:.1f}%")

    if revenue_growth is not None and revenue_growth < -0.05:
        score_penalty -= 2
        reasons.append(f"Recent revenue decline of {revenue_growth * 100:.1f}%")

    if earnings_quarterly_growth is not None and earnings_quarterly_growth < -0.05:
        score_penalty -= 2
        reasons.append(f"Recent quarterly earnings decline of {earnings_quarterly_growth * 100:.1f}%")

    if reasons:
        return score_penalty, ", ".join(reasons)
    else:
        return 0, ""


def validate_unusual_metrics(symbol, data):
    sector = data.get('sector', '')
    market_cap = data.get('market_cap', 0) or 0
    fcf = data.get('fcf', 0) or 0

    score_penalty = 0
    reasons = []

    if market_cap > 0 and fcf > 0:
        fcf_yield = fcf / market_cap

        if 'Financial' in sector and fcf_yield > 0.10:
            score_penalty -= 3
            reasons.append(f"Unusually high FCF yield ({fcf_yield * 100:.1f}%) for financial sector")
        elif fcf_yield > 0.20:
            score_penalty -= 2
            reasons.append(f"Suspiciously high FCF yield ({fcf_yield * 100:.1f}%)")

    debt_to_equity = data.get('debt_to_equity', 0)
    if debt_to_equity is not None:
        if debt_to_equity > 10:
            score_penalty -= 2
            reasons.append(f"Suspiciously high debt-to-equity ratio of {debt_to_equity:.2f}")

    if reasons:
        return score_penalty, ", ".join(reasons)
    else:
        return 0, ""


def calculate_intrinsic_value(data):
    eps = data.get('eps', 0) or data.get('trailingEPS', 0) or 0
    pe_ratio = data.get('pe_ratio', 0) or 0
    fcf = data.get('fcf', 0) or 0
    market_cap = data.get('market_cap', 0) or 0
    shares_outstanding = data.get('sharesOutstanding', 0) or 0

    if eps <= 0 or pe_ratio <= 0:
        return 0

    try:
        growth_rate = data.get('earningsGrowth', 0.10) or 0.10
        growth_rate = max(0.05, min(growth_rate, 0.20))
        discount_rate = 0.12

        future_eps = []
        for i in range(1, 11):
            future_eps.append(eps * (1 + growth_rate) ** i)

        terminal_value = future_eps[-1] * (1 + 0.03) / (discount_rate - 0.03)
        future_eps.append(terminal_value)

        present_value = sum([eps_i / (1 + discount_rate) ** (i + 1) for i, eps_i in enumerate(future_eps)])

        return present_value
    except:
        if market_cap > 0 and shares_outstanding > 0:
            avg_pe = 15
            if pe_ratio > 0 and pe_ratio < 50:
                avg_pe = pe_ratio
            expected_eps_growth = 0.10
            future_value = eps * (1 + expected_eps_growth) * avg_pe
            return future_value
        else:
            return 0


def buffett_analysis(stock_data):
    buffett_picks = {}

    buffett_preferred_sectors = [
        'Financial Services', 'Consumer Defensive', 'Technology', 'Financial',
        'Consumer Goods', 'Healthcare', 'Consumer Staples', 'Insurance', 'Banking',
        'Food & Beverage', 'Retail', 'Communication Services', 'Utilities', 'Pharmaceuticals'
    ]

    buffett_avoided_sectors = [
        'Biotechnology', 'Cryptocurrency', 'Cannabis',
        'Mining', 'Oil & Gas E&P', 'Airlines'
    ]

    for symbol, data in stock_data.items():
        if 'error' in data:
            continue

        if '.BO' in symbol:
            continue

        score = 0
        reasons = []
        warnings = []
        missing_data = []
        qualitative_factors = {}
        data_quality_issues = []

        for key_metric in ['roe', 'debt_to_equity', 'pe_ratio', 'market_cap', 'current_price']:
            if key_metric not in data or data[key_metric] is None:
                missing_data.append(key_metric)

        if data.get('debt_to_equity') and data['debt_to_equity'] > 3:
            data['debt_to_equity'] = data['debt_to_equity'] / 100

        if 'intrinsic_value' not in data or data['intrinsic_value'] is None or data['intrinsic_value'] == 0:
            data['intrinsic_value'] = calculate_intrinsic_value(data)

            if data['intrinsic_value'] > 0 and data.get('current_price', 0) > 0:
                current_price = data['current_price']
                intrinsic_value = data['intrinsic_value']

                if intrinsic_value > current_price:
                    data['margin_of_safety'] = ((intrinsic_value - current_price) / intrinsic_value) * 100
                else:
                    data['margin_of_safety'] = 0
            else:
                data['margin_of_safety'] = 0

        validation_score, validation_reason = validate_unusual_metrics(symbol, data)
        if validation_score < 0:
            score += validation_score
            data_quality_issues.append(validation_reason)

        decline_score, decline_reason = check_recent_performance_decline(symbol, data)
        if decline_score < 0:
            score += decline_score
            warnings.append(decline_reason)

        sector = data.get('sector', 'Unknown')
        if any(preferred in sector for preferred in buffett_preferred_sectors):
            score += 1
            reasons.append(f"Within Buffett's circle of competence: {sector}")
        elif any(avoided in sector for avoided in buffett_avoided_sectors):
            warnings.append(f"Outside Buffett's typical interests: {sector}")

        if data.get('roe'):
            if data['roe'] > 20:
                score += 3
                reasons.append(f"Exceptional ROE of {data['roe']:.2f}%")
            elif data['roe'] > 15:
                score += 2
                reasons.append(f"Strong ROE of {data['roe']:.2f}%")
            elif data['roe'] > 10:
                score += 1
                reasons.append(f"Decent ROE of {data['roe']:.2f}%")

        if data.get('debt_to_equity') is not None:
            if data['debt_to_equity'] < 0.3:
                score += 3
                reasons.append(f"Minimal debt-to-equity ratio of {data['debt_to_equity']:.2f}")
            elif data['debt_to_equity'] < 0.5:
                score += 2
                reasons.append(f"Low debt-to-equity ratio of {data['debt_to_equity']:.2f}")
            elif data['debt_to_equity'] < 0.7:
                score += 1
                reasons.append(f"Moderate debt-to-equity ratio of {data['debt_to_equity']:.2f}")
            else:
                warnings.append(f"High debt-to-equity ratio of {data['debt_to_equity']:.2f}")

        if data.get('earnings_growth'):
            if data['earnings_growth'] > 15:
                score += 3
                reasons.append(f"Excellent earnings growth of {data['earnings_growth']:.2f}%")
            elif data['earnings_growth'] > 10:
                score += 2
                reasons.append(f"Strong earnings growth of {data['earnings_growth']:.2f}%")
            elif data['earnings_growth'] > 5:
                score += 1
                reasons.append(f"Positive earnings growth of {data['earnings_growth']:.2f}%")
            elif data['earnings_growth'] < 0:
                warnings.append(f"Negative earnings growth of {data['earnings_growth']:.2f}%")

        if data.get('fcf'):
            if data['fcf'] > 0:
                if data.get('market_cap') and data['market_cap'] > 0:
                    fcf_yield = (data['fcf'] / data['market_cap']) * 100
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

        if data.get('margin_of_safety') and data.get('intrinsic_value', 0) > 0:
            if data['margin_of_safety'] > 40:
                score += 4
                reasons.append(f"Huge margin of safety: {data['margin_of_safety']:.2f}%")
            elif data['margin_of_safety'] > 30:
                score += 3
                reasons.append(f"Substantial margin of safety: {data['margin_of_safety']:.2f}%")
            elif data['margin_of_safety'] > 20:
                score += 2
                reasons.append(f"Good margin of safety: {data['margin_of_safety']:.2f}%")
            elif data['margin_of_safety'] > 10:
                score += 1
                reasons.append(f"Some margin of safety: {data['margin_of_safety']:.2f}%")

        if data.get('pe_ratio') and data['pe_ratio'] > 0:
            if data['pe_ratio'] < 15:
                score += 3
                reasons.append(f"Attractive P/E ratio of {data['pe_ratio']:.2f}")
            elif data['pe_ratio'] < 20:
                score += 2
                reasons.append(f"Reasonable P/E ratio of {data['pe_ratio']:.2f}")
            elif data['pe_ratio'] < 25:
                score += 1
                reasons.append(f"Acceptable P/E ratio of {data['pe_ratio']:.2f}")
            else:
                warnings.append(f"High P/E ratio of {data['pe_ratio']:.2f}")

        if data.get('market_cap'):
            market_cap_billions = data['market_cap'] / 1_000_000_000
            if market_cap_billions >= 10:
                score += 1
                reasons.append(f"Large established company (₹{market_cap_billions:.2f}B market cap)")
            elif market_cap_billions >= 1:
                score += 0.5
            elif market_cap_billions < 0.2:
                warnings.append(f"Very small company (₹{market_cap_billions:.2f}B market cap)")

        industry_score, industry_reason = analyze_industry_dynamics(symbol, data)
        qualitative_factors['industry_dynamics'] = {
            'score': industry_score,
            'reason': industry_reason
        }
        score += industry_score
        if industry_score > 0:
            reasons.append(industry_reason)
        elif industry_score < 0:
            warnings.append(industry_reason)

        regulatory_score, regulatory_reason = analyze_regulatory_environment(symbol, data)
        qualitative_factors['regulatory_environment'] = {
            'score': regulatory_score,
            'reason': regulatory_reason
        }
        score += regulatory_score
        if regulatory_score > 0:
            reasons.append(regulatory_reason)
        elif regulatory_score < 0:
            warnings.append(regulatory_reason)

        macro_score, macro_reason = analyze_macroeconomic_factors(symbol, data)
        qualitative_factors['macroeconomic_factors'] = {
            'score': macro_score,
            'reason': macro_reason
        }
        score += macro_score
        if macro_score > 0:
            reasons.append(macro_reason)
        elif macro_score < 0:
            warnings.append(macro_reason)

        governance_score, governance_reason = analyze_corporate_governance(symbol, data)
        qualitative_factors['corporate_governance'] = {
            'score': governance_score,
            'reason': governance_reason
        }
        score += governance_score
        if governance_score > 0:
            reasons.append(governance_reason)
        elif governance_score < 0:
            warnings.append(governance_reason)

        india_fit_score, india_fit_reason = analyze_india_cultural_fit(symbol, data)
        qualitative_factors['india_cultural_fit'] = {
            'score': india_fit_score,
            'reason': india_fit_reason
        }
        score += india_fit_score
        if india_fit_score > 0:
            reasons.append(india_fit_reason)
        elif india_fit_score < 0:
            warnings.append(india_fit_reason)

        moat_score, moat_reason = analyze_economic_moat(symbol, data)
        qualitative_factors['economic_moat'] = {
            'score': moat_score,
            'reason': moat_reason
        }
        score += moat_score
        if moat_score > 0:
            reasons.append(moat_reason)
        elif moat_score < 0:
            warnings.append(moat_reason)

        management_score, management_reason = analyze_owner_oriented_management(symbol, data)
        qualitative_factors['owner_oriented_management'] = {
            'score': management_score,
            'reason': management_reason
        }
        score += management_score
        if management_score > 0:
            reasons.append(management_reason)
        elif management_score < 0:
            warnings.append(management_reason)

        raw_api_debt = data.get('debtToEquity', 'Not in API')

        if score >= 13:
            buffett_picks[symbol] = {
                'name': data['name'],
                'sector': data.get('sector', 'Unknown'),
                'price': data.get('current_price', 0),
                'intrinsic_value': data.get('intrinsic_value', 0),
                'margin_of_safety': data.get('margin_of_safety', 0),
                'pe_ratio': data.get('pe_ratio', 0),
                'roe': data.get('roe', 0),
                'debt_to_equity': data.get('debt_to_equity', 0),
                'raw_api_debt': raw_api_debt,
                'market_cap': data.get('market_cap', 0),
                'score': score,
                'reasons': reasons,
                'warnings': warnings,
                'missing_data': missing_data,
                'data_quality_issues': data_quality_issues,
                'qualitative_factors': qualitative_factors
            }

    sorted_picks = dict(sorted(buffett_picks.items(), key=lambda x: x[1]['score'], reverse=True))
    return sorted_picks


def increment_visit_counter():
    counter_file = 'data/visit_counter.json'
    today = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d')

    try:
        if os.path.exists(counter_file):
            with open(counter_file, 'r') as f:
                counter_data = json.load(f)
        else:
            counter_data = {}

        if today in counter_data:
            counter_data[today] += 1
        else:
            counter_data[today] = 1

        with open(counter_file, 'w') as f:
            json.dump(counter_data, f, indent=2)

        return counter_data.get(today, 0)
    except:
        return 1


def generate_html_report(buffett_picks):
    india_timezone = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(india_timezone)
    formatted_time = current_time.strftime("%d-%b-%Y %I:%M %p IST")
    visit_count = increment_visit_counter()

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Warren Buffett Indian Stock Picks</title>
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
            .search-container {
                margin-bottom: 20px;
            }
            #stockSearch {
                padding: 10px 15px;
                border-radius: 50px;
                border: 1px solid #ced4da;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                width: 100%;
            }
            .visit-counter {
                font-size: 0.8rem;
                color: #6c757d;
                text-align: center;
                margin-top: 5px;
            }
            .hidden {
                display: none !important;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row mt-4 mb-2">
                <div class="col-md-8">
                    <h1 class="display-4">Warren Buffett Indian Stock Picks-Disclaimer This is not investment advice do your own analysis and research </h1>
                    <p class="text-muted">Last updated: """ + formatted_time + """</p>
                    <p class="visit-counter">Today's visitor count: """ + str(visit_count) + """</p>
                </div>
                <div class="col-md-4">
                    <div class="search-container">
                        <input type="text" id="stockSearch" placeholder="Search for stocks by name or symbol..." 
                               class="form-control" onkeyup="searchStocks()">
                    </div>
                    <div class="buffett-quote">
                        "Price is what you pay. Value is what you get." - Warren Buffett
                    </div>
                </div>
            </div>

            <div class="filters p-3 mb-4">
                <h5>Buffett's Key Investment Principles:</h5>
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
                <p class="small mb-0">Stocks are scored based on how well they align with these principles. Minimum score threshold: 12 points.</p>
            </div>

            <div class="row" id="stockCardsContainer">
    """

    total_market_cap = sum(data.get('market_cap', 0) or 0 for data in buffett_picks.values())
    total_market_cap_billions = total_market_cap / 1_000_000_000

    html += f"""
            <div class="col-12 mb-4">
                <div class="alert alert-info">
                    <strong>Found {len(buffett_picks)} companies</strong> matching Warren Buffett's investment criteria 
                    with a combined market cap of ₹{total_market_cap_billions:,.2f} billion.
                </div>
            </div>
    """

    for symbol, data in buffett_picks.items():
        display_symbol = symbol.replace('.NS', '')
        exchange = "NSE"

        market_cap = data.get('market_cap', 0) or 0
        market_cap_billions = market_cap / 1_000_000_000

        price = data.get('price', 0) or 0
        intrinsic_value = data.get('intrinsic_value', 0) or 0
        margin_of_safety = data.get('margin_of_safety', 0) or 0
        pe_ratio = data.get('pe_ratio', 0) or 0
        roe = data.get('roe', 0) or 0
        debt_to_equity = data.get('debt_to_equity', 0) or 0

        raw_api_debt = data.get('raw_api_debt', 'N/A')

        score = data.get('score', 0) or 0
        score_class = "success"
        if score >= 15:
            score_class = "success"
            score_text = "Excellent"
        elif score >= 13:
            score_class = "primary"
            score_text = "Very Good"
        elif score >= 10:
            score_class = "info"
            score_text = "Good"
        else:
            score_class = "secondary"
            score_text = "Fair"

        qualitative_factors = data.get('qualitative_factors', {})

        missing_data = data.get('missing_data', [])
        data_quality_issues = data.get('data_quality_issues', [])
        has_missing_data = len(missing_data) > 0
        has_data_quality_issues = len(data_quality_issues) > 0

        html += f"""
                <div class="col-md-6 col-lg-4 stock-card-wrapper" data-name="{data['name'].lower()}" data-symbol="{display_symbol.lower()}">
                    <div class="card stock-card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">{data['name']}</h5>
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="ticker-symbol" onclick="window.open('https://www.nseindia.com/get-quotes/equity?symbol={display_symbol}', '_blank')">{display_symbol}</span>
                                    <span class="badge bg-secondary">{exchange}</span>
                                </div>
                                <span class="badge bg-{score_class} badge-buffett">Buffett Score: {score:.1f} ({score_text})</span>
                            </div>
                        </div>
                        <div class="card-body">
                            <h6 class="card-subtitle mb-3 text-muted">{data['sector']}</h6>
        """

        if has_missing_data:
            html += f"""
                            <div class="data-error mb-3">
                                <strong><i class="bi bi-exclamation-triangle"></i> Missing Data:</strong> 
                                <span>{', '.join(missing_data)}</span>
                            </div>
            """

        if has_data_quality_issues:
            html += f"""
                            <div class="debug-info mb-3 collapsible-section" onclick="toggleSection(this)">
                                <strong><i class="bi bi-bug"></i> Data Quality Info (Click to expand)</strong>
                                <div class="collapsible-content">
                                    <ul class="data-quality mt-2 mb-0">
            """
            for issue in data_quality_issues:
                html += f"                                        <li>{issue}</li>\n"
            html += """
                                    </ul>
                                </div>
                            </div>
            """

        html += f"""                    
                            <div class="row mb-1">
                                <div class="col-6">Current Price:</div>
                                <div class="col-6 text-end fw-bold">₹{price:,.2f}</div>
                            </div>

                            <div class="row mb-1">
                                <div class="col-6">Intrinsic Value:</div>
                                <div class="col-6 text-end fw-bold">₹{intrinsic_value:,.2f}</div>
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

                            <h6 class="mt-4 mb-2">Why Buffett Would Like It:</h6>
                            <ul class="reasons">
        """

        for reason in data.get('reasons', []):
            html += f"                                <li>{reason}</li>\n"

        html += """
                            </ul>

                            <div class="qualitative-section">
                                <h6 class="mb-2">Qualitative Assessment:</h6>
        """

        if 'industry_dynamics' in qualitative_factors:
            industry = qualitative_factors['industry_dynamics']
            score_class = "positive-score" if industry['score'] > 0 else "negative-score" if industry[
                                                                                                 'score'] < 0 else "neutral-score"
            html += f"""
                                <div class="qualitative-item">
                                    <strong>Industry Dynamics:</strong>
                                    <span class="qualitative-score {score_class}">{industry['score']}</span>
                                    <div>{industry['reason']}</div>
                                </div>
            """

        if 'regulatory_environment' in qualitative_factors:
            regulatory = qualitative_factors['regulatory_environment']
            score_class = "positive-score" if regulatory['score'] > 0 else "negative-score" if regulatory[
                                                                                                   'score'] < 0 else "neutral-score"
            html += f"""
                                <div class="qualitative-item">
                                    <strong>Regulatory Environment:</strong>
                                    <span class="qualitative-score {score_class}">{regulatory['score']}</span>
                                    <div>{regulatory['reason']}</div>
                                </div>
            """

        if 'macroeconomic_factors' in qualitative_factors:
            macro = qualitative_factors['macroeconomic_factors']
            score_class = "positive-score" if macro['score'] > 0 else "negative-score" if macro[
                                                                                              'score'] < 0 else "neutral-score"
            html += f"""
                                <div class="qualitative-item">
                                    <strong>Macroeconomic Factors:</strong>
                                    <span class="qualitative-score {score_class}">{macro['score']}</span>
                                    <div>{macro['reason']}</div>
                                </div>
            """

        if 'corporate_governance' in qualitative_factors:
            governance = qualitative_factors['corporate_governance']
            score_class = "positive-score" if governance['score'] > 0 else "negative-score" if governance[
                                                                                                   'score'] < 0 else "neutral-score"
            html += f"""
                                <div class="qualitative-item">
                                    <strong>Corporate Governance:</strong>
                                    <span class="qualitative-score {score_class}">{governance['score']}</span>
                                    <div>{governance['reason']}</div>
                                </div>
            """

        if 'india_cultural_fit' in qualitative_factors:
            india_fit = qualitative_factors['india_cultural_fit']
            score_class = "positive-score" if india_fit['score'] > 0 else "negative-score" if india_fit[
                                                                                                  'score'] < 0 else "neutral-score"
            html += f"""
                                <div class="qualitative-item">
                                    <strong>India Cultural Fit:</strong>
                                    <span class="qualitative-score {score_class}">{india_fit['score']}</span>
                                    <div>{india_fit['reason']}</div>
                                </div>
            """

        if 'economic_moat' in qualitative_factors:
            moat = qualitative_factors['economic_moat']
            score_class = "positive-score" if moat['score'] > 0 else "negative-score" if moat[
                                                                                             'score'] < 0 else "neutral-score"
            html += f"""
                                <div class="qualitative-item">
                                    <strong>Economic Moat:</strong>
                                    <span class="qualitative-score {score_class}">{moat['score']}</span>
                                    <div>{moat['reason']}</div>
                                </div>
            """

        if 'owner_oriented_management' in qualitative_factors:
            management = qualitative_factors['owner_oriented_management']
            score_class = "positive-score" if management['score'] > 0 else "negative-score" if management[
                                                                                                   'score'] < 0 else "neutral-score"
            html += f"""
                                <div class="qualitative-item">
                                    <strong>Owner-Oriented Management:</strong>
                                    <span class="qualitative-score {score_class}">{management['score']}</span>
                                    <div>{management['reason']}</div>
                                </div>
            """

        html += """
                            </div>
        """

        if data.get('warnings', []):
            html += """
                            <h6 class="mt-3 mb-2 text-danger">Potential Concerns:</h6>
                            <ul class="warnings">
            """

            for warning in data.get('warnings', []):
                html += f"                                <li>{warning}</li>\n"

        html += """
                            </ul>
                        </div>
                    </div>
                </div>
        """

    html += """
            </div>

            <div class="row mt-5 mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <h4>Warren Buffett's Investment Philosophy</h4>
                            <p>Warren Buffett, often called the "Oracle of Omaha," follows a disciplined value investing approach based on principles he learned from his mentor, Benjamin Graham. Buffett looks for companies with:</p>

                            <div class="row">
                                <div class="col-md-6">
                                    <h5>Quantitative Factors</h5>
                                    <ul>
                                        <li><strong>Simple, Understandable Business Models</strong>: Buffett only invests in businesses he can understand and evaluate.</li>
                                        <li><strong>Consistent Operating History</strong>: Companies with a long track record of profitability and stability.</li>
                                        <li><strong>Financial Strength</strong>: Low debt, high returns on equity, and consistent earnings power.</li>
                                        <li><strong>Margin of Safety</strong>: Buying at a price significantly below intrinsic value to reduce risk.</li>
                                    </ul>
                                </div>

                                <div class="col-md-6">
                                    <h5>Qualitative Factors</h5>
                                    <ul>
                                        <li><strong>Industry Dynamics</strong>: Buffett favors industries with stable demand and high barriers to entry.</li>
                                        <li><strong>Regulatory Environment</strong>: He prefers businesses with minimal regulatory interference.</li>
                                        <li><strong>Macroeconomic Resilience</strong>: Companies that can thrive in various economic conditions.</li>
                                        <li><strong>Corporate Governance</strong>: Honest, capable management that allocates capital effectively.</li>
                                        <li><strong>Local Market Adaptation</strong>: Understanding of cultural and regional market dynamics.</li>
                                        <li><strong>Economic Moat Depth</strong>: Strong barriers to competition and sustainable advantages.</li>
                                        <li><strong>Owner-Oriented Management</strong>: High insider ownership and shareholder-friendly policies.</li>
                                    </ul>
                                </div>
                            </div>

                            <p>Remember Buffett's famous quotes:</p>
                            <div class="buffett-quote">"Be fearful when others are greedy, and greedy when others are fearful."</div>
                            <div class="buffett-quote">"It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price."</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="bg-light py-3 mt-5">
            <div class="container text-center">
                <p class="mb-0 text-muted">This analysis is for educational purposes only. Always do your own research before investing.</p>
                <p class="mb-0 text-muted small">Updated daily after market close.</p>
                <p class="visit-counter">Total visits today: """ + str(visit_count) + """</p>
            </div>
        </footer>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const tickerSymbols = document.querySelectorAll('.ticker-symbol');
                tickerSymbols.forEach(symbol => {
                    symbol.style.cursor = 'pointer';
                    symbol.title = 'Click to view on NSE website';
                });
            });

            function toggleSection(element) {
                const content = element.querySelector('.collapsible-content');
                if (content.style.maxHeight) {
                    content.style.maxHeight = null;
                } else {
                    content.style.maxHeight = content.scrollHeight + "px";
                }
            }

            function searchStocks() {
                const searchInput = document.getElementById('stockSearch');
                const filter = searchInput.value.toLowerCase();
                const stockCards = document.getElementsByClassName('stock-card-wrapper');

                for (let i = 0; i < stockCards.length; i++) {
                    const name = stockCards[i].getAttribute('data-name');
                    const symbol = stockCards[i].getAttribute('data-symbol');

                    if (name.includes(filter) || symbol.includes(filter)) {
                        stockCards[i].classList.remove('hidden');
                    } else {
                        stockCards[i].classList.add('hidden');
                    }
                }

                const visibleCount = document.querySelectorAll('.stock-card-wrapper:not(.hidden)').length;
                const infoAlert = document.querySelector('.alert-info strong');
                if (infoAlert) {
                    infoAlert.textContent = `Found ${visibleCount} companies`;
                }
            }
        </script>
    </body>
    </html>
    """

    os.makedirs('output', exist_ok=True)

    with open('output/index.html', 'w') as f:
        f.write(html)

    print("HTML report generated at output/index.html")


if __name__ == "__main__":
    print("Starting Warren Buffett analysis...")
    stock_data = load_latest_data()
    buffett_picks = buffett_analysis(stock_data)
    generate_html_report(buffett_picks)
    print(f"Analysis complete. Found {len(buffett_picks)} stocks that match Buffett's criteria.")

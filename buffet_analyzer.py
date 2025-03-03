import json
import os
from datetime import datetime

def safe_format(value, format_spec=".2f"):
    """Safely format a value that might be None"""
    if value is None:
        return f"{0:{format_spec}}"
    return f"{value:{format_spec}}"


def load_latest_data():
    """Load the most recently collected stock data"""
    try:
        with open('data/latest.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}


def buffett_analysis(stock_data):
    """
    Apply Warren Buffett's comprehensive investment criteria to filter stocks

    Key Buffett Principles:
    1. Business is simple to understand and operate (Circle of Competence)
    2. Consistent operating history/established business
    3. Favorable long-term prospects (Economic Moat)
    4. Operated by honest and competent people (Management Quality)
    5. Simple business model (Avoid complexity)
    6. High and consistent ROE (15%+ for 10+ years)
    7. Low debt to equity ratio
    8. High profit margins (and preferably improving)
    9. Ability to deploy retained earnings profitably
    10. Margin of safety (Price vs Intrinsic Value)
    11. Be fearful when others are greedy, and greedy when others are fearful
    12. Focus on low P/E companies with strong fundamentals
    """
    buffett_picks = {}
    buffett_preferred_sectors = [
        'Financial Services', 'Consumer Defensive', 'Technology', 'Financial','Pharmaceuticals',
        'Consumer Goods', 'Healthcare', 'Consumer Staples', 'Insurance', 'Banking',
        'Food & Beverage', 'Retail', 'Communication Services', 'Utilities'
    ]

    # Define sectors Buffett typically avoids
    buffett_avoided_sectors = [
        'Biotechnology', 'Cryptocurrency', 'Cannabis',
        'Mining', 'Oil & Gas E&P', 'Airlines'
    ]

    for symbol, data in stock_data.items():
        # Skip stocks with missing or error data
        if 'error' in data:
            continue

        # Initialize score and reasons
        score = 0
        reasons = []
        warnings = []

        # --- UNDERSTANDING THE BUSINESS ---

        # 1. Circle of Competence (business Buffett would understand)
        sector = data.get('sector', 'Unknown')
        if any(preferred in sector for preferred in buffett_preferred_sectors):
            score += 1
            reasons.append(f"Within Buffett's circle of competence: {sector}")
        elif any(avoided in sector for avoided in buffett_avoided_sectors):
            warnings.append(f"Outside Buffett's typical interests: {sector}")

        # --- FINANCIAL STRENGTH ---

        # 2. ROE > 15% (Buffett's gold standard)
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

        # 3. Low debt to equity (Buffett prefers companies with little debt)
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

        # 4. Consistent earnings growth (Buffett loves predictable businesses)
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

        # 5. Positive free cash flow (Cash generation is critical)
        if data.get('fcf'):
            if data['fcf'] > 0:
                # Calculate FCF yield if possible
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

        # --- VALUATION ---

        # 6. Margin of safety (Buffett's core principle - price vs value)
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

        # 7. Reasonable P/E ratio (Buffett avoids excessive valuations)
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

        # 8. Market capitalization (Buffett typically avoids tiny companies)
        if data.get('market_cap'):
            # Convert to billions for easier reading
            market_cap_billions = data['market_cap'] / 1_000_000_000
            if market_cap_billions >= 10:
                score += 1
                reasons.append(f"Large established company (₹{market_cap_billions:.2f}B market cap)")
            elif market_cap_billions >= 1:
                score += 0.5
            elif market_cap_billions < 0.2:  # Less than 200 million
                warnings.append(f"Very small company (₹{market_cap_billions:.2f}B market cap)")

        # Only include stocks that meet Buffett's criteria (higher threshold)
        # Out of possible 20+ points, require at least 8 for high confidence picks
        if score >= 8:
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
                'score': score,
                'reasons': reasons,
                'warnings': warnings
            }

    # Sort by score (descending)
    sorted_picks = dict(sorted(buffett_picks.items(), key=lambda x: x[1]['score'], reverse=True))
    return sorted_picks


def generate_html_report(buffett_picks):
    """Generate an HTML report of Buffett's stock picks"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Warren Buffett Indian Stock Picks</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
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
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row mt-4 mb-2">
                <div class="col-12">
                    <h1 class="display-4">Warren Buffett Indian Stock Picks-Disclaimer not an investment recommendation do your own analysis</h1>
                    <p class="text-muted">Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</p>
                    <div class="buffett-quote">
                        "Price is what you pay. Value is what you get." - Warren Buffett
                    </div>
                </div>
            </div>

            <div class="filters p-3 mb-4">
                <h5>Buffett's Key Investment Principles:</h5>
                <ol>
                    <li>Circle of Competence: Only invest in businesses you understand</li>
                    <li>Margin of Safety: Buy companies at a significant discount to intrinsic value</li>
                    <li>Economic Moat: Companies with sustainable competitive advantages</li>
                    <li>Great Management: Honest, capable, and shareholder-friendly</li>
                    <li>Financial Strength: Low debt, high ROE, consistent earnings</li>
                </ol>
                <p class="small mb-0">Stocks are scored based on how well they align with these principles.</p>
            </div>

            <div class="row">
    """

    # Calculate total market value being tracked
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
        # Format the display symbol
        display_symbol = symbol.replace('.NS', '').replace('.BO', '')
        exchange = "NSE" if ".NS" in symbol else "BSE"

        # Calculate market cap in billions for display and handle None
        market_cap = data.get('market_cap', 0) or 0
        market_cap_billions = market_cap / 1_000_000_000

        # Get price and intrinsic value, protecting against None
        price = data.get('price', 0) or 0
        intrinsic_value = data.get('intrinsic_value', 0) or 0
        margin_of_safety = data.get('margin_of_safety', 0) or 0
        pe_ratio = data.get('pe_ratio', 0) or 0
        roe = data.get('roe', 0) or 0
        debt_to_equity = data.get('debt_to_equity', 0) or 0

        # Determine the score category
        score = data.get('score', 0) or 0
        score_class = "success"
        if score >= 15:
            score_class = "success"
            score_text = "Excellent"
        elif score >= 12:
            score_class = "primary"
            score_text = "Very Good"
        elif score >= 10:
            score_class = "info"
            score_text = "Good"
        else:
            score_class = "secondary"
            score_text = "Fair"

        html += f"""
                <div class="col-md-6 col-lg-4">
                    <div class="card stock-card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">{data['name']}</h5>
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="ticker-symbol">{display_symbol}</span>
                                    <span class="badge bg-secondary">{exchange}</span>
                                </div>
                                <span class="badge bg-{score_class} badge-buffett">Buffett Score: {score:.1f} ({score_text})</span>
                            </div>
                        </div>
                        <div class="card-body">
                            <h6 class="card-subtitle mb-3 text-muted">{data['sector']}</h6>

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

        if data.get('warnings', []):
            html += """
                            </ul>

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
                            <ul>
                                <li><strong>Simple, Understandable Business Models</strong>: Buffett only invests in businesses he can understand and evaluate.</li>
                                <li><strong>Consistent Operating History</strong>: Companies with a long track record of profitability and stability.</li>
                                <li><strong>Favorable Long-Term Prospects</strong>: Businesses with "economic moats" - sustainable competitive advantages.</li>
                                <li><strong>Competent and Honest Management</strong>: Leadership with integrity that allocates capital effectively.</li>
                                <li><strong>Financial Strength</strong>: Low debt, high returns on equity, and consistent earnings power.</li>
                                <li><strong>Margin of Safety</strong>: Buying at a price significantly below intrinsic value to reduce risk.</li>
                            </ul>
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
            </div>
        </footer>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)

    # Save HTML report
    with open('output/index.html', 'w') as f:
        f.write(html)

    print("HTML report generated at output/index.html")


if __name__ == "__main__":
    print("Starting Warren Buffett analysis...")
    stock_data = load_latest_data()
    buffett_picks = buffett_analysis(stock_data)
    generate_html_report(buffett_picks)
    print(f"Analysis complete. Found {len(buffett_picks)} stocks that match Buffett's criteria.")
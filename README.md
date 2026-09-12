# Fixed-Income Portfolio Risk Engine

A Python-based fixed-income risk analytics project that evaluates the interest-rate risk of a current hypothetical Euro bond portfolio using historical ECB yield-curve movements, stress scenarios, and Monte Carlo simulation.

## Project Objective

The core idea is:

> **Take the current portfolio and ask: how would it have behaved if it had been exposed to historical market moves?**

The project does **not** calculate the portfolio's actual historical P&L. Instead, it applies the portfolio's **current DV01 exposures** to historical daily yield changes across the ECB yield curve.

This creates a historical distribution of hypothetical daily P&L for the portfolio, which is then used to estimate risk measures such as **Value at Risk (VaR)** and **Expected Shortfall (ES)**.

## What the Project Does

### 1. Yield Curve Data Preparation
- Loads ECB yield-curve data
- Converts dates into datetime format
- Reorders maturities from 3M to 30Y
- Calculates daily yield changes
- Converts yield changes into basis points
- Calculates daily volatility by maturity
- Calculates correlation across yield-curve maturities

### 2. Bond Analytics
For each bond in the portfolio, the project calculates:
- Bond market value
- Macaulay duration
- Modified duration
- DV01
- Signed DV01 for long and short positions

### 3. Historical Portfolio P&L
Each bond is mapped to the closest available ECB maturity bucket.

For every historical trading day:

```text
Historical Portfolio P&L ≈ -DV01 × Historical Yield Change
```

The current portfolio's DV01 exposures are applied to more than 5,000 historical daily yield scenarios.

This answers:

> **If today's portfolio had existed during each of these historical yield moves, what would its approximate one-day P&L have been?**

The result is a historical P&L distribution for the current portfolio.

### 4. Historical VaR and Expected Shortfall
Using the historical P&L distribution, the project calculates:
- 95% 1-Day Historical VaR
- 99% 1-Day Historical VaR
- 95% Expected Shortfall
- 99% Expected Shortfall
- 10 worst historical portfolio P&L scenarios

### 5. Data-Driven Stress Testing
The project estimates extreme upward and downward yield shocks using historical percentile movements.

For each maturity, it uses:
- 95th and 99th percentile upward yield changes
- 5th and 1st percentile downward yield changes
- Worst observed one-day increases and decreases

The stress scenarios are then applied to the portfolio using signed DV01.

This gives:
- P&L under a severe upward yield shock
- P&L under a severe downward yield shock

### 6. Monte Carlo Simulation
The project also generates 100,000 simulated daily yield-curve scenarios.

The process is:

```text
Historical Yield Changes
        ↓
Covariance Matrix
        ↓
Cholesky Decomposition
        ↓
Independent Random Shocks
        ↓
Correlated Yield Shocks
        ↓
Portfolio DV01 Exposure
        ↓
100,000 Simulated Portfolio P&Ls
```

Cholesky decomposition is used so simulated maturity shocks retain approximately the same covariance structure observed in historical yield movements.

The simulated covariance matrix is also compared with the original historical covariance matrix as a validation check.

### 7. Monte Carlo Risk Measures
From the 100,000 simulated portfolio P&Ls, the project calculates:
- 95% Monte Carlo VaR
- 99% Monte Carlo VaR
- 95% Monte Carlo Expected Shortfall
- 99% Monte Carlo Expected Shortfall

Historical and Monte Carlo risk measures are then compared visually.

## Visual Outputs

The script generates charts for:
- Latest ECB yield curve
- Yield-curve correlation matrix
- Historical portfolio P&L distribution
- Data-driven yield stress scenarios
- Portfolio P&L under stress
- Monte Carlo P&L distribution
- Historical vs Monte Carlo VaR
- Historical vs Monte Carlo Expected Shortfall

Charts are saved automatically in the `outputs/` folder.

## Main Risk Concepts Used

- Yield curve analysis
- Bond pricing
- Macaulay duration
- Modified duration
- DV01
- Long/short interest-rate exposure
- Historical simulation
- Value at Risk
- Expected Shortfall
- Stress testing
- Covariance
- Correlation
- Cholesky decomposition
- Monte Carlo simulation

## Key Assumptions

This is a learning and portfolio-risk analytics project, not a production trading or bank risk engine.

Important assumptions include:
- P&L is approximated using **DV01**, so the model assumes a mostly linear relationship between yield changes and bond price changes.
- Convexity is not included in the historical and Monte Carlo P&L approximation.
- Each portfolio bond is mapped to a selected ECB maturity bucket.
- Monte Carlo yield shocks are generated using a multivariate normal framework based on historical covariance.
- Historical covariance is assumed to be informative for simulated future one-day movements.
- Stress scenarios are data-driven project assumptions rather than regulatory stress scenarios.
- Liquidity risk, credit spread risk, default risk, FX risk, and transaction costs are not included.

## Why This Project Matters

The project demonstrates how a market-risk analyst can move from raw yield-curve data to portfolio-level risk measures.

More importantly, it separates three different questions:

- **Historical simulation:** What would today's portfolio have done under historical yield moves?
- **Stress testing:** What happens under deliberately severe yield shocks?
- **Monte Carlo simulation:** What could happen under a large set of statistically simulated yield scenarios?

This provides a practical framework for understanding portfolio interest-rate exposure rather than looking at DV01, VaR, or duration in isolation.

## Tech Stack

- Python
- pandas
- NumPy
- Matplotlib
- Seaborn
- Excel / CSV data

## Files

```text
positiontests.py
ecb_yield_curve.csv
hypothetical_euro_bond_portfolio.xlsx
cleaned_ecb_yield_curve.csv
outputs/
```

## Run the Project

Install the required libraries:

```bash
pip install pandas numpy matplotlib seaborn openpyxl
```

Then run:

```bash
python positiontests.py
```

Make sure the ECB yield-curve CSV and hypothetical bond portfolio Excel file are in the same working directory as the Python script.

## Future Improvements

Possible next steps:
- Add convexity to large-shock P&L estimates
- Add rolling volatility and regime-based analysis
- Compare different historical lookback windows
- Add parallel shift, steepener, and flattener stress scenarios
- Add key-rate DV01
- Add credit-spread risk
- Add VaR backtesting
- Add portfolio dashboards
- Add scenario reporting by maturity bucket

## Disclaimer

This project is for educational and portfolio demonstration purposes only. It is not investment advice and is not intended to represent a full production-grade market-risk framework.

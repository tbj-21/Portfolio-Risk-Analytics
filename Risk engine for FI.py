import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

os.makedirs("outputs", exist_ok=True)

rates_df = pd.read_csv("ecb_yield_curve.csv")

rates_df.columns = ["Date", "Time", "10Y", "1Y", "20Y", "2Y", "30Y", "3M",
              "3Y", "5Y", "6M", "7Y" ]

rates_df["Date"] = pd.to_datetime(rates_df["Date"])

## Arranging maturities in ascending order
maturity_columns = ["3M", "6M", "1Y", "2Y", "3Y","5Y", "7Y", "10Y", "20Y", "30Y"]
rates_df = rates_df[["Date", "Time"] + maturity_columns]
rates_df.to_csv("cleaned_ecb_yield_curve.csv", index=False) #saving clean dataset
print("Cleaned dataset saved successfully!")

# Plotting the latest yield curve
yields = rates_df.iloc[-1][maturity_columns]

plt.figure(figsize=(10, 6))
plt.plot(maturity_columns, yields, marker="o")
plt.title("Euro Area Government Yield Curve")
plt.xlabel("Maturity")
plt.ylabel("Yield (%)")
plt.grid(True)
plt.savefig("outputs/01_latest_yield_curve.png", dpi=300, bbox_inches="tight")
plt.show()
plt.close()

# Calculating daily changes in yields

yield_columns = ["3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

yield_changes = rates_df[yield_columns].diff().dropna()
#creating new df for storing daily change in yield and removing the first row (NaN)

# converting percentage-point changes into basis points
yield_changes_bp = yield_changes * 100

daily_volatility = yield_changes_bp.std()
print("Daily yield volatility (basis points):", daily_volatility)

# Calculating plotting correlation between yield maturities
correlation_matrix = yield_changes_bp.corr()

print("Correlation matrix:\n", correlation_matrix)

plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap="coolwarm")
plt.title("Yield Curve Correlation Matrix")
plt.tight_layout()
plt.savefig("outputs/02_yield_correlation_matrix.png", dpi=300, bbox_inches="tight")
plt.show()
plt.close()

# BOND ANALYTICS

portfolio = pd.read_excel("hypothetical_euro_bond_portfolio.xlsx", sheet_name="Portfolio")

def bond_price(face_value, coupon_rate, yield_rate, maturity):
    coupon = face_value * coupon_rate
    price = 0

    for t in range(1, maturity + 1):
        price += coupon / (1 + yield_rate) ** t

    price += face_value / (1 + yield_rate) ** maturity
    return price

portfolio["Coupon_Rate"] = portfolio["Coupon_Rate_%"] / 100 
portfolio["Yield_Rate"] = portfolio["Current_Yield_%"] / 100

portfolio["Market_Value"] = portfolio.apply( lambda row:
        bond_price( row["Face_Value_EUR"], row["Coupon_Rate"], row["Yield_Rate"], row["Maturity_Years"]), axis=1)
print(portfolio)


def macaulay_duration(face_value, coupon_rate, yield_rate, maturity):

    coupon = face_value * coupon_rate
    price = bond_price(face_value, coupon_rate, yield_rate, maturity )
    weighted_cash_flows = 0

    for t in range(1, maturity + 1):
        cash_flow = coupon
        if t == maturity:
            cash_flow += face_value

        present_value = cash_flow / (1 + yield_rate) ** t
        weighted_cash_flows += t * present_value
    return weighted_cash_flows / price

portfolio["Macaulay_Duration"] = portfolio.apply(
    lambda row: macaulay_duration(
        row["Face_Value_EUR"],
        row["Coupon_Rate"],
        row["Yield_Rate"],
        row["Maturity_Years"] ), axis=1)

portfolio["Modified_Duration"] = ( portfolio["Macaulay_Duration"] /
    (1 + portfolio["Yield_Rate"]) )

# Calculate DV01 for each bond position
portfolio["DV01"] = (portfolio["Modified_Duration"] * portfolio["Market_Value"]* 0.0001)

# Apply position direction to DV01
portfolio["Signed_DV01"] = portfolio["DV01"]
portfolio.loc[portfolio["Position"] == "Short", "Signed_DV01"] *= -1
portfolio_dv01 = portfolio["Signed_DV01"].sum()  # total portfolio DV01 (net)

## PORTFOLIO DURATION
# Gross market value 
gross_market_value = portfolio["Market_Value"].sum()

# Portfolio modified duration based on gross exposure
# NetDV01 = Modified Duration × Market Value × 0.0001
portfolio_duration = (portfolio_dv01 / gross_market_value * 10000)

print("\nPortfolio Analytics:")
print(f"Gross Market Value: €{gross_market_value:,.2f}")
print(f"Net DV01: €{portfolio_dv01:,.2f}")
print(f"Portfolio Modified Duration: {portfolio_duration:.4f}")

# MAP PORTFOLIO BONDS TO ECB YIELD CHANGES
portfolio["ECB_Maturity"] = portfolio["Maturity_Years"].map(
   {2: "2Y", 5: "5Y", 10: "10Y", 30: "30Y"})

# HISTORICAL PORTFOLIO P&L

# today’s portfolio sensitivity to each historical yield move.
historical_pnl = pd.DataFrame(index=yield_changes_bp.index)

historical_pnl["Date"] = rates_df.loc[yield_changes_bp.index, "Date"].values

historical_pnl["Portfolio_PnL"] = 0.0

for _, row in portfolio.iterrows():

    maturity = row["ECB_Maturity"]
    dv01 = row["Signed_DV01"]
    historical_pnl["Portfolio_PnL"] += (-dv01 * yield_changes_bp[maturity].values)

print("\nP&L Statistics:")
print(historical_pnl["Portfolio_PnL"].describe())

# HISTORICAL P&L DISTRIBUTION
pnl = historical_pnl["Portfolio_PnL"]

plt.figure(figsize=(10, 6))
plt.title("Historical Portfolio P&L Distribution")
plt.xlabel("Daily P&L (in €)")
plt.ylabel("Frequency")
plt.grid(True)
plt.hist(pnl, bins=50, color="tab:blue")
plt.axvline(pnl.min(), color="orange", linestyle="--", label="Worst P&L")
plt.axvline(pnl.max(), color="green", linestyle="--", label="Best P&L")
plt.legend()

plt.savefig("outputs/03_historical_pnl_distribution.png", dpi=300, bbox_inches="tight")
plt.show()
plt.close()

# HISTORICAL VALUE AT RISK
#pnl = historical_pnl["Portfolio_PnL"]
var_95 = -pnl.quantile(0.05)
var_99 = -pnl.quantile(0.01)

# HISTORICAL EXPECTED SHORTFALL

historical_es_95 = -pnl[pnl <= -var_95].mean()
historical_es_99 = -pnl[pnl <= -var_99].mean()
print("\nHistorical VaR:")
print(f"95% 1-Day VaR: €{var_95:,.2f}")
print(f"99% 1-Day VaR: €{var_99:,.2f}")
print("\nHistorical Expected Shortfall:")
print(f"95% 1-Day ES: €{historical_es_95:,.2f}")
print(f"99% 1-Day ES: €{historical_es_99:,.2f}")

# WORST HISTORICAL P&L DAYS
worst_days = historical_pnl.sort_values("Portfolio_PnL").head(10)

print("\n10 Worst Historical P&L Days:")
print(worst_days)

# STRESS TESTING

# HISTORICAL YIELD STRESS LEVELS
stress_levels = pd.DataFrame({
    "95th_percentile": yield_changes_bp.quantile(0.95),
    "99th_percentile": yield_changes_bp.quantile(0.99),
    "Worst_1D_Increase": yield_changes_bp.max(),
    "5th_percentile": yield_changes_bp.quantile(0.05),
    "1st_percentile": yield_changes_bp.quantile(0.01),
    "Worst_1D_Decrease": yield_changes_bp.min()
})


# DATA-DRIVEN STRESS SCENARIOS

yield_stress_up = (
    stress_levels["99th_percentile"]
    + ( stress_levels["99th_percentile"] - stress_levels["95th_percentile"]  ))

yield_stress_down = (
    stress_levels["1st_percentile"]
    - ( stress_levels["5th_percentile"] - stress_levels["1st_percentile"]  ))


# STRESS TEST PORTFOLIO P&L

stress_up_pnl = 0
stress_down_pnl = 0

for _, row in portfolio.iterrows():

    maturity = row["ECB_Maturity"]
    dv01 = row["Signed_DV01"]

    stress_up_pnl += -dv01 * yield_stress_up[maturity]
    stress_down_pnl += -dv01 * yield_stress_down[maturity]


print("\nStress Test Results:")
print(f"Upward Yield Stress P&L:   €{stress_up_pnl:,.2f}")
print(f"Downward Yield Stress P&L: €{stress_down_pnl:,.2f}")


# DATA-DRIVEN STRESS CURVE
#yieldcolumns = ["3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

plt.figure(figsize=(10, 6))

plt.plot( yield_columns, yield_stress_up[yield_columns], marker="o", label="Upward Stress" )

plt.plot( yield_columns, yield_stress_down[yield_columns], marker="o", label="Downward Stress" )

plt.axhline(0, linewidth=1)

plt.title("Data-Driven Yield Curve Stress Scenarios")
plt.xlabel("Maturity")
plt.ylabel("Yield Shock (bp)")
plt.legend()
plt.grid(True)
plt.savefig("outputs/04_stress_yield_curve.png", dpi=300, bbox_inches="tight")
plt.show()
plt.close()

# STRESS P&L COMPARISON

stress_labels = [ "Upward Yield Stress", "Downward Yield Stress"]

stress_pnl_values = [ stress_up_pnl,  stress_down_pnl]
plt.figure(figsize=(8, 6))
plt.bar( stress_labels, stress_pnl_values)

plt.axhline(0, linewidth=1)

plt.title("Portfolio P&L Under Data-Driven Stress")
plt.ylabel("P&L (€)")
plt.grid(axis="y")
plt.savefig("outputs/05_stress_pnl_comparison.png", dpi=300, bbox_inches="tight")
plt.show()
plt.close()

# MONTE CARLO SIMULATION

# Calculating covariance matrix of daily yield changes
covariance_matrix = yield_changes_bp.cov()

# Cholesky decomposition of covariance matrix
cholesky_matrix = np.linalg.cholesky(covariance_matrix)

# Generating independent standard normal random shocks
no_of_sims = 100000
np.random.seed(45)     # For reproducible Monte Carlo results
random_shocks = np.random.normal( size=(no_of_sims, len(yield_columns)) )

# Transforming independent shocks into correlated yield shocks
correlated_shocks = random_shocks @ cholesky_matrix.T

# Check simulated covariance matrix
simulated_covariance = np.cov(correlated_shocks, rowvar=False)
difference = simulated_covariance - covariance_matrix.values

max_difference = np.abs(difference).max() 
if max_difference < 0.5:       # simple validation threshold for project
    print("Covariance match looks reasonable.")
else:
    print("Covariance match is weak.")
# MONTE CARLO PORTFOLIO P&L

# Aggregate signed DV01 by maturity
portfolio_dv01_by_maturity = (
    portfolio.groupby("ECB_Maturity")["Signed_DV01"]
    .sum()
    .reindex(yield_columns)
    .fillna(0) )

# Calculate simulated portfolio P&L
monte_carlo_pnl = -np.dot(correlated_shocks , portfolio_dv01_by_maturity.values)

print("\nMonte Carlo P&L:")
print(f"Simulations: {len(monte_carlo_pnl)}")
print(f"Mean P&L: €{monte_carlo_pnl.mean():,.2f}")
print(f"Std Dev of P&L: €{monte_carlo_pnl.std():,.2f}")

# MONTE CARLO VALUE AT RISK

mc_var_95 = -np.percentile(monte_carlo_pnl, 5)
mc_var_99 = -np.percentile(monte_carlo_pnl, 1)

# MONTE CARLO EXPECTED SHORTFALL

mc_es_95 = -monte_carlo_pnl[ monte_carlo_pnl <= -mc_var_95 ].mean()
mc_es_99 = -monte_carlo_pnl[monte_carlo_pnl <= -mc_var_99 ].mean()

print("\nMonte Carlo Expected Shortfall:")
print(f"95% 1-Day ES: €{mc_es_95:,.2f}")
print(f"99% 1-Day ES: €{mc_es_99:,.2f}")

# MONTE CARLO P&L DISTRIBUTION

plt.figure(figsize=(10, 6))
plt.hist(monte_carlo_pnl, bins=100, color="tab:blue")

plt.axvline(-mc_var_95, color="orange", linestyle="--", linewidth=2, label="95% VaR")
plt.axvline(-mc_var_99, color="red", linestyle="--", linewidth=2, label="99% VaR")

plt.title("Monte Carlo Simulated Portfolio P&L")
plt.xlabel("1-Day P&L (€)")
plt.ylabel("Frequency")
plt.legend()
plt.grid(True)
plt.savefig("outputs/06_monte_carlo_pnl_distribution.png", dpi=300, bbox_inches="tight")
plt.show()
plt.close()

# HISTORICAL VS MONTE CARLO COMPARISON
risk_comparison = pd.DataFrame({
    "Historical": [ var_95, var_99, historical_es_95, historical_es_99],
    "Monte Carlo": [ mc_var_95, mc_var_99, mc_es_95, mc_es_99]},
    index=[ "95% VaR", "99% VaR", "95% ES", "99% ES" ])

print("\nHistorical vs Monte Carlo Risk Comparison:")
print(risk_comparison.round(2))

# VAR COMPARISON

var_labels = ["95% VaR", "99% VaR"]
historical_var_values = [ var_95, var_99]
monte_carlo_var_values = [ mc_var_95, mc_var_99]
x = np.arange(len(var_labels))
width = 0.35

plt.figure(figsize=(8, 6))

plt.bar( x - width / 2, historical_var_values, width, label="Historical")
plt.bar( x + width / 2, monte_carlo_var_values, width, label="Monte Carlo")

plt.xticks(x, var_labels)
plt.ylabel("VaR (€)")
plt.title("Historical vs Monte Carlo VaR")
plt.legend()
plt.grid(axis="y")
plt.tight_layout()
plt.savefig("outputs/07_historical_vs_monte_carlo_var.png", dpi=300, bbox_inches="tight")
plt.show()
plt.close()

# EXPECTED SHORTFALL COMPARISON
es_labels = ["95% ES", "99% ES"]

historical_es_values = [ historical_es_95, historical_es_99]
monte_carlo_es_values = [ mc_es_95, mc_es_99]
x = np.arange(len(es_labels))

plt.figure(figsize=(8, 6))
plt.bar( x - width / 2, historical_es_values, width, label="Historical" )
plt.bar( x + width / 2, monte_carlo_es_values, width, label="Monte Carlo")

plt.xticks(x, es_labels)
plt.ylabel("Expected Shortfall (€)")
plt.title("Historical vs Monte Carlo Expected Shortfall")
plt.legend()
plt.grid(axis="y")
plt.tight_layout()
plt.savefig("outputs/08_historical_vs_monte_carlo_es.png", dpi=300, bbox_inches="tight")
plt.show()
plt.close()
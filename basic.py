import gurobipy as gp
from gurobipy import GRB
m = gp.Model("basic")

# ----- Read Stock Data -----
def process_stock_data(file_path):
    stock_set = set()
    # Open and read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 5:
            index = int(parts[0])  # Index of asset
            asset = parts[1]       # Asset name
            avg_price = float(parts[2])  # Average price
            cagr = float(parts[3])/100       # CAGR
            volatility = float(parts[4])/100 # Volatility
            
            stock_set.add((index, asset, avg_price, cagr, volatility))
    return stock_set

# File path to the .txt file
file_path = 'data.txt'
stocks = process_stock_data(file_path)

# ----- Adding Variables -----
vars = []
for i in range(1, 21):
    vars.append(m.addVar(vtype=GRB.CONTINUOUS, name=f"x{i}"))

# Initial Starting Balance
budget = 10000

# ----- Objective Function -----
# Initialize the objective expression
objective = gp.LinExpr()

# Add terms to the objective function
for stock, var in zip(sorted(stocks), vars):  # Align stocks with variables
    index, asset, avg_price, cagr, volatility = stock
    delta_i = volatility
    a_i = cagr
    p_i = avg_price
    x_i = var
    
    # Add the term: ((a_i - delta_i) * p_i * x_i - p_i * x_i)
    objective += ((1+(a_i - delta_i)) * p_i * x_i - (p_i * x_i))

m.setObjective(objective, GRB.MAXIMIZE)

# ----- Constraints -----
# Budget constraint: Sum of (p_i * x_i) <= b
budget_constraint = gp.LinExpr()
for stock, var in zip(sorted(stocks), vars):  # Align stocks with variables
    _, _, avg_price, _, _ = stock  # Extract price (p_i) from stock data
    p_i = avg_price
    x_i = var
    
    # Add term p_i * x_i to the budget constraint
    budget_constraint += p_i * x_i

m.addConstr(budget_constraint <= budget)

# Individual allocation constraint: p_i * x_i <= 0.15 * total portfolio value
portfolio_total = budget_constraint  # Total portfolio value
for stock, var in zip(sorted(stocks), vars):
    _, _, avg_price, _, _ = stock  # Extract price (p_i) from stock data
    p_i = avg_price
    x_i = var
    m.addConstr(p_i * x_i <= 0.15 * portfolio_total)

m.optimize()

# ----- Print Optimal Solution -----
var_to_asset = {f"x{stock[0]}": stock[1] for stock in sorted(stocks)}

if m.status == GRB.OPTIMAL:
    print("\n----- Print Optimal Solution -----")
    print(f"Objective value (Net Return): ${m.objVal:.2f}")
    print("\nOptimal allocation of shares:")
    for var in m.getVars():
        if var.x > 0:  # Only print variables with positive values
            asset_name = var_to_asset[var.varName]  # Retrieve the asset name
            print( f"   {var.varName:<3} ({asset_name:<4}):  Shares: {var.x:.2f}")
else:
    print("No Optimal Sol Family.")

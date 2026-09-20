def calculate_pv_of_annuity(payment, rate, periods):
    """
    Calculates the Present Value (PV) of an ordinary annuity.
    Formula: PV = P * [1 - (1 + r)^-n] / r
    """
    if rate == 0:
        return payment * periods
    return payment * (1 - (1 + rate)**-periods) / rate

def evaluate_bess_scenario(scenario_name, params, capex, opex, tax_rate, interest_rate, debt_tenor):
    """
    Calculates CFADS, Debt Capacity, and Gearing Ratio for a given scenario.
    """
    ebitda = params["annual_revenue"] - opex
    tax_estimate = ebitda * tax_rate
    cfads = ebitda - tax_estimate
    
    max_annual_debt_service = cfads / params["target_dscr"]
    
    debt_size = calculate_pv_of_annuity(
        payment=max_annual_debt_service, 
        rate=interest_rate, 
        periods=debt_tenor
    )
    
    debt_size = min(debt_size, capex)
    gearing = debt_size / capex
    equity_size = capex - debt_size
    
    return {
        "Strategy": scenario_name,
        "Target DSCR": params["target_dscr"],
        "Annual Revenue (€)": params["annual_revenue"],
        "CFADS (€)": cfads,
        "Max Debt Service (€)": max_annual_debt_service,
        "Debt Capacity (€)": debt_size,
        "Equity Required (€)": equity_size,
        "Gearing Ratio (%)": gearing * 100
    }

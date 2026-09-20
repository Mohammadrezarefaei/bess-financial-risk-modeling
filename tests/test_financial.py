import pytest
from src.financial_logic import calculate_pv_of_annuity

def test_pv_of_annuity_zero_rate():
    # Test with zero interest rate
    assert calculate_pv_of_annuity(100, 0, 5) == 500
    
def test_pv_of_annuity_standard():
    # Test standard annuity PV calculation
    pv = calculate_pv_of_annuity(1000, 0.05, 10)
    assert round(pv, 2) == 7721.73

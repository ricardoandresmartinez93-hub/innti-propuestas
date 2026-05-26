"""
Pruebas para la generación del código de propuesta.
"""
import pytest
from datetime import datetime
from app.utils.proposal_code import generate_date_code, build_proposal_code


def test_generate_date_code_current_month():
    """Genera código de fecha actual con formato correcto (4 dígitos)."""
    code = generate_date_code()
    assert len(code) == 4
    assert code.isdigit()


def test_generate_date_code_specific_date():
    """Para enero 2026 debe retornar '0126'."""
    specific_date = datetime(2026, 1, 15)
    assert generate_date_code(specific_date) == "0126"


def test_generate_date_code_december():
    """Para diciembre 2025 retorna '1225'."""
    specific_date = datetime(2025, 12, 1)
    assert generate_date_code(specific_date) == "1225"


def test_build_proposal_code():
    """'3018' + mayo 2026 = '3018-0526'."""
    date = datetime(2026, 5, 10)
    assert build_proposal_code("3018", date) == "3018-0526"


def test_build_proposal_code_empty_consecutive():
    """Debe lanzar ValueError si consecutive está vacío."""
    with pytest.raises(ValueError, match="El consecutivo interno no puede estar vacío"):
        build_proposal_code("")
    
    with pytest.raises(ValueError, match="El consecutivo interno no puede estar vacío"):
        build_proposal_code("   ")

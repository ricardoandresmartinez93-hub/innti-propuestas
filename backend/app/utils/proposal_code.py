"""
Utilidades para la generación del código de propuesta.
Formato: {consecutivo_interno}-{MMAA}
"""
from datetime import datetime
from typing import Optional


def generate_date_code(date: Optional[datetime] = None) -> str:
    """
    Retorna el código de fecha en formato "MMAA" (ej: "0526").
    Si no se pasa fecha, usa la fecha actual.
    """
    if date is None:
        date = datetime.now()
    return date.strftime("%m%y")


def build_proposal_code(consecutive: str, date: Optional[datetime] = None) -> str:
    """
    Construye el código completo de la propuesta: "3018-0526".
    Valida que el consecutivo no esté vacío.
    """
    if not consecutive or not consecutive.strip():
        raise ValueError("El consecutivo interno no puede estar vacío.")
    
    date_code = generate_date_code(date)
    return f"{consecutive.strip()}-{date_code}"


def suggest_date_code() -> str:
    """
    Alias de generate_date_code() para ser usado por la API.
    Informa al frontend el código de fecha que debe acompañar al consecutivo manual.
    """
    return generate_date_code()

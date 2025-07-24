



def decimal_to_float(value):
    """Convertește Decimal la float pentru operații în template."""
    from decimal import Decimal
    if isinstance(value, Decimal):
        return float(value)
    return value
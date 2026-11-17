"""Disposable hosted-review fixture. Not imported by the plugin; do not merge."""


def quote_total(unit_price_cents: int, quantity: int) -> int:
    """Return total cents for a nonnegative price and positive quantity."""
    if unit_price_cents < 0 or quantity <= 0:
        raise ValueError("invalid price or quantity")
    return unit_price_cents // quantity

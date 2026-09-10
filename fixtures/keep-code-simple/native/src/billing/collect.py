def collect(invoice_id, amount, request_key, ledger, gateway):
    """gateway is injected. This fixture has no real gateway implementation."""
    if request_key in ledger:
        return ledger[request_key]
    receipt = gateway.charge(invoice_id, amount, idempotency_key=request_key)
    ledger[request_key] = {
        "invoice_id": invoice_id,
        "amount": amount,
        "receipt": receipt,
    }
    return ledger[request_key]

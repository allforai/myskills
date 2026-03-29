# Fintech Domain Knowledge

## Core Business Flows
- Account Opening -> KYC Verification -> Fund Account -> Transact -> Settle
- Lending: Apply -> Credit Check -> Approve -> Disburse -> Repay
- Investment: Browse -> Research -> Order -> Execute -> Portfolio View

## Typical Roles
- Customer (consumer, experience_priority: consumer)
- Compliance Officer (professional, experience_priority: admin)
- Risk Manager (professional, experience_priority: admin)
- Support Agent (professional, experience_priority: admin)

## Critical Business Rules
- Double-entry bookkeeping (every debit has matching credit)
- Transaction atomicity (ACID compliance)
- Regulatory compliance (KYC/AML/PCI-DSS)
- Audit trail (immutable transaction log)
- Rate limiting (fraud prevention)

## Common Entities
- Account, Transaction, Ledger, User, KYCRecord, Instrument, Portfolio, Order

## Domain-Specific Checks
- Transaction reversibility rules
- Settlement timing (T+0, T+1, T+2)
- Interest calculation accuracy
- Regulatory reporting completeness

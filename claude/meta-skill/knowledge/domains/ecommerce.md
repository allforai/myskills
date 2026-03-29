# E-Commerce Domain Knowledge

## Core Business Flows
- Browse -> Search -> Product Detail -> Add to Cart -> Checkout -> Payment -> Order Confirmation
- Order Management: Track -> Cancel -> Return -> Refund
- Seller: List Product -> Manage Inventory -> Process Orders -> Handle Returns

## Typical Roles
- Buyer (consumer, experience_priority: consumer)
- Seller/Merchant (professional, experience_priority: admin)
- Platform Admin (professional, experience_priority: admin)
- Customer Service (professional, experience_priority: admin)

## Critical Business Rules
- Inventory consistency (concurrent purchase race condition)
- Payment idempotency (double-charge prevention)
- Order state machine (pending -> paid -> shipped -> delivered -> completed)
- Price calculation (discounts, coupons, taxes, shipping)

## Common Entities
- User/Account, Product/SKU, Cart, Order, OrderItem, Payment, Address, Review, Category

## Domain-Specific Checks
- CRUD completeness per entity (especially Order lifecycle)
- Payment callback handling (async notification from payment provider)
- Stock deduction timing (optimistic vs pessimistic locking)
- Multi-currency support (if international)

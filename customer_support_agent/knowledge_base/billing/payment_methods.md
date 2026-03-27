# Payment Methods

## Supported Payment Methods

CloudSync Pro supports multiple payment options depending on your plan:

| Payment Method | Free | Pro ($29/mo) | Enterprise (Custom) |
|---|---|---|---|
| Visa / Mastercard | N/A | Yes | Yes |
| American Express | N/A | Yes | Yes |
| Discover | N/A | Yes | Yes |
| PayPal | N/A | Monthly only | No |
| ACH Bank Transfer | N/A | Yes (US only) | Yes (US only) |
| Wire Transfer | N/A | No | Yes ($5K+ annual) |
| Purchase Order | N/A | No | Yes |

## How to Update Your Payment Method

1. Go to **Settings > Billing > Payment Methods**
2. Click **Add Payment Method** or **Edit** next to your current method
3. Enter your new card details or bank information
4. Click **Save**. The new method becomes the default for future charges.

Your old payment method remains on file for 30 days in case of pending transactions. You can remove it manually after confirming no outstanding charges.

## Handling Failed Payments

When a payment fails, CloudSync Pro follows this retry schedule:

- **Day 0**: Initial charge attempt fails. You receive an email notification with error code (e.g., `PAY_ERR_DECLINED`, `PAY_ERR_INSUFFICIENT`, `PAY_ERR_EXPIRED`).
- **Day 1**: First automatic retry.
- **Day 3**: Second automatic retry. A banner appears in your dashboard warning of billing issues.
- **Day 7**: Final automatic retry. You receive an urgent email.
- **Day 10**: Account downgraded to Free plan. All Pro/Enterprise features are suspended but data is preserved for 90 days.

## Common Payment Error Codes

- `PAY_ERR_DECLINED` -- Your card was declined by the issuing bank. Contact your bank.
- `PAY_ERR_INSUFFICIENT` -- Insufficient funds in the account.
- `PAY_ERR_EXPIRED` -- The card on file has expired. Update your payment method.
- `PAY_ERR_CVV` -- CVV verification failed. Re-enter your card details.
- `PAY_ERR_LIMIT` -- Transaction exceeds your card's daily limit.

## Currency and Regional Pricing

All prices are listed in USD. International customers are charged in USD, and currency conversion fees are determined by your bank or payment provider. CloudSync Pro does not charge additional fees for international transactions.

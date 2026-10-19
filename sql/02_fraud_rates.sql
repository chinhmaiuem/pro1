-- Unknown labels are deliberately excluded, not converted to zero.
SELECT merchant_category,
       COUNT(*) AS labeled_transactions,
       SUM(is_fraud) AS fraud_cases,
       1.0 * SUM(is_fraud) / COUNT(*) AS fraud_rate
FROM transactions
WHERE is_fraud IS NOT NULL
GROUP BY merchant_category
HAVING COUNT(*) >= 30
ORDER BY fraud_rate DESC, labeled_transactions DESC;

-- Raw RFM metrics for the 365 days before the day after the last observed date.
-- LEFT JOIN retains registry customers with no eligible purchases.
WITH cutoff AS (
    SELECT datetime(date(MAX(date)), '+1 day') AS reference_date FROM transactions
),
purchase_metrics AS (
    SELECT client_id, MAX(date) AS last_purchase, COUNT(*) AS frequency,
           SUM(amount) AS monetary
    FROM transactions CROSS JOIN cutoff
    WHERE is_purchase = 1
      AND julianday(date) >= julianday(reference_date, '-365 days')
      AND julianday(date) < julianday(reference_date)
    GROUP BY client_id
)
SELECT u.id AS client_id,
       CAST(julianday(c.reference_date) - julianday(p.last_purchase) AS INTEGER) AS recency,
       COALESCE(p.frequency, 0) AS frequency,
       COALESCE(p.monetary, 0) AS monetary
FROM users u CROSS JOIN cutoff c
LEFT JOIN purchase_metrics p ON p.client_id = u.id
ORDER BY u.id;

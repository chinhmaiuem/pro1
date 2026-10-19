-- Discovery cohort: top-quartile purchase value, with no Credit card on registry.
-- PERCENT_RANK is a SQL ranking illustration; boundary ties can differ from pandas quantile.
WITH cutoff AS (
    SELECT datetime(date(MAX(date)), '+1 day') AS reference_date FROM transactions
),
spend AS (
    SELECT client_id, SUM(amount) AS purchase_value, COUNT(*) AS purchases
    FROM transactions CROSS JOIN cutoff
    WHERE is_purchase = 1
      AND julianday(date) >= julianday(reference_date, '-365 days')
      AND julianday(date) < julianday(reference_date)
    GROUP BY client_id
),
ranked AS (
    SELECT *, PERCENT_RANK() OVER (ORDER BY purchase_value) AS spend_percentile
    FROM spend
)
SELECT r.* FROM ranked r JOIN users u ON u.id = r.client_id
WHERE spend_percentile >= 0.75
  AND NOT EXISTS (
      SELECT 1 FROM cards c WHERE c.client_id = r.client_id AND lower(c.card_type) = 'credit'
  )
ORDER BY purchase_value DESC;

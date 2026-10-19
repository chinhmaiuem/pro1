-- Error-free net value, purchase value and refunds; running net value uses a window.
WITH monthly AS (
    SELECT substr(date, 1, 7) AS month,
           COUNT(*) AS transactions,
           SUM(amount) AS net_value,
           SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS purchase_value,
           -SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) AS refund_value
    FROM transactions WHERE has_error = 0
    GROUP BY substr(date, 1, 7)
)
SELECT *, SUM(net_value) OVER (ORDER BY month ROWS UNBOUNDED PRECEDING) AS cumulative_net_value
FROM monthly ORDER BY month;

-- Spend stays at week/channel grain. Outcomes are held separately to avoid fan-out.
SELECT channel,
       COUNT(*) AS weeks,
       ROUND(SUM(spend_gbp), 2) AS total_spend_gbp,
       ROUND(AVG(spend_gbp), 2) AS mean_weekly_spend_gbp
FROM spend
GROUP BY channel
ORDER BY total_spend_gbp DESC;

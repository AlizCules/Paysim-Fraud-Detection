-- These queries run against a DuckDB view named transactions.

-- query: total_transactions
SELECT
    COUNT(*) AS transactions,
    SUM(isFraud) AS fraud_transactions,
    COUNT(*) - SUM(isFraud) AS non_fraud_transactions,
    AVG(isFraud) AS fraud_rate
FROM transactions;

-- query: fraud_by_type
SELECT
    type,
    COUNT(*) AS transactions,
    SUM(isFraud) AS fraud_transactions,
    AVG(isFraud) AS fraud_rate,
    SUM(CASE WHEN isFraud = 1 THEN amount ELSE 0 END) AS fraud_amount
FROM transactions
GROUP BY type
ORDER BY fraud_rate DESC;

-- query: fraud_amount_by_type
SELECT
    type,
    SUM(CASE WHEN isFraud = 1 THEN amount ELSE 0 END) AS fraud_amount,
    AVG(CASE WHEN isFraud = 1 THEN amount END) AS average_fraud_amount,
    MAX(CASE WHEN isFraud = 1 THEN amount END) AS maximum_fraud_amount
FROM transactions
GROUP BY type
ORDER BY fraud_amount DESC;

-- query: fraud_by_hour
SELECT
    MOD(step, 24) AS hour,
    COUNT(*) AS transactions,
    SUM(isFraud) AS fraud_transactions,
    AVG(isFraud) AS fraud_rate
FROM transactions
GROUP BY hour
ORDER BY hour;

-- query: fraud_by_day
SELECT
    CAST(step / 24 AS INTEGER) AS day,
    COUNT(*) AS transactions,
    SUM(isFraud) AS fraud_transactions,
    AVG(isFraud) AS fraud_rate
FROM transactions
GROUP BY day
ORDER BY day;

-- query: fraud_by_amount_band
SELECT
    CASE
        WHEN amount < 1000 THEN '<1k'
        WHEN amount < 10000 THEN '1k-10k'
        WHEN amount < 100000 THEN '10k-100k'
        WHEN amount < 1000000 THEN '100k-1m'
        ELSE '>=1m'
    END AS amount_band,
    COUNT(*) AS transactions,
    SUM(isFraud) AS fraud_transactions,
    AVG(isFraud) AS fraud_rate
FROM transactions
GROUP BY amount_band
ORDER BY MIN(amount);

-- query: high_risk_segments
SELECT
    type,
    MOD(step, 24) AS hour,
    COUNT(*) AS transactions,
    SUM(isFraud) AS fraud_transactions,
    AVG(isFraud) AS fraud_rate
FROM transactions
GROUP BY type, hour
HAVING COUNT(*) >= 1000
ORDER BY fraud_rate DESC
LIMIT 20;

-- query: alert_volume
SELECT
    COUNT(*) AS scored_transactions,
    SUM(fraud_flag) AS alerts,
    AVG(CAST(fraud_flag AS INTEGER)) AS alert_rate,
    AVG(fraud_score) AS mean_fraud_score
FROM predictions;

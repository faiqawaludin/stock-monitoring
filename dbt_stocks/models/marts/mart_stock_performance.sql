WITH base AS (
    SELECT
        *,
        LAG(close_price) OVER (
            PARTITION BY symbol
            ORDER BY trade_date
        ) AS prev_close_price
    FROM {{ ref('stg_stock') }}
)

SELECT
    symbol,
    trade_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    ROUND(high_price - low_price, 2) AS intraday_spread,
    ROUND(
        SAFE_DIVIDE(close_price - prev_close_price, prev_close_price) * 100,
        2
    ) AS daily_return_pct,
    ROUND(
        AVG(close_price) OVER (
            PARTITION BY symbol
            ORDER BY trade_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS moving_avg_7d
FROM base
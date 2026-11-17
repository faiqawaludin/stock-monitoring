WITH ranked AS (
    SELECT
        symbol,
        exchange,
        DATE(TIMESTAMP(date)) AS trade_date,
        CAST(open AS FLOAT64) AS open_price,
        CAST(high AS FLOAT64) AS high_price,
        CAST(low AS FLOAT64) AS low_price,
        CAST(close AS FLOAT64) AS close_price,
        CAST(volume AS FLOAT64) AS volume,
        ingested_at,
        ROW_NUMBER() OVER (
            PARTITION BY symbol, DATE(TIMESTAMP(date))
            ORDER BY ingested_at DESC
        ) AS rn
    FROM {{ source('raw_stock', 'eod_prices') }}
)

SELECT
    symbol,
    exchange,
    trade_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume
FROM ranked
WHERE rn = 1
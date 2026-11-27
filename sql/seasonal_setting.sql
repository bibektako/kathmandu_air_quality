SELECT 
    station_name,
    CASE 
        WHEN EXTRACT(MONTH FROM date::date) IN (12, 1, 2) THEN 'Winter'
        WHEN EXTRACT(MONTH FROM date::date) IN (3, 4, 5) THEN 'Pre-monsoon'
        WHEN EXTRACT(MONTH FROM date::date) IN (6, 7, 8, 9) THEN 'Monsoon'
        WHEN EXTRACT(MONTH FROM date::date) IN (10, 11) THEN 'Post-monsoon'
    END AS season,
    ROUND(AVG(aqi), 1) AS avg_aqi,
    ROUND(MAX(aqi), 1) AS max_aqi
FROM fact_air_quality
WHERE date IS NOT NULL
GROUP BY station_name, 
    CASE 
        WHEN EXTRACT(MONTH FROM date::date) IN (12, 1, 2) THEN 'Winter'
        WHEN EXTRACT(MONTH FROM date::date) IN (3, 4, 5) THEN 'Pre-monsoon'
        WHEN EXTRACT(MONTH FROM date::date) IN (6, 7, 8, 9) THEN 'Monsoon'
        WHEN EXTRACT(MONTH FROM date::date) IN (10, 11) THEN 'Post-monsoon'
    END
ORDER BY station_name, season
limit 10;
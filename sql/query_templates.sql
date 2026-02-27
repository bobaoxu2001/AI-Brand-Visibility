-- =========================================================
-- AI Brand Visibility Tracker - SQL Query Templates
-- =========================================================

-- 1) Pipeline health checks
SELECT COUNT(*) AS prompt_count FROM prompts;

SELECT model_name, COUNT(*) AS successful_raw_responses
FROM raw_responses
WHERE status = 'success'
GROUP BY model_name
ORDER BY model_name;

SELECT COUNT(*) AS parsed_metrics_count
FROM parsed_metrics;

-- 2) Brand recommendation totals
SELECT
  top_brand,
  COUNT(*) AS recommendations
FROM parsed_metrics
GROUP BY top_brand
ORDER BY recommendations DESC;

-- 3) Share-of-model view (win-rate by model)
SELECT
  model_name,
  brand,
  win_count,
  win_rate_pct
FROM view_share_of_model
ORDER BY model_name, win_rate_pct DESC;

-- 4) Sentiment view (avg sentiment by model + brand)
SELECT
  model_name,
  brand,
  avg_sentiment,
  sample_size
FROM view_brand_sentiment
ORDER BY model_name, avg_sentiment DESC;

-- 5) Compare Tesla recommendation share across models
SELECT
  model_name,
  win_rate_pct
FROM view_share_of_model
WHERE brand = 'Tesla'
ORDER BY win_rate_pct DESC;

-- 6) "Other" bucket share (signals off-taxonomy recommendations)
SELECT
  model_name,
  win_rate_pct
FROM view_share_of_model
WHERE brand = 'Other'
ORDER BY win_rate_pct DESC;

-- 7) Prompt-category-level winner analysis
SELECT
  p.category,
  pm.top_brand,
  COUNT(*) AS wins
FROM parsed_metrics pm
JOIN raw_responses rr ON rr.id = pm.response_id
JOIN prompts p ON p.id = rr.prompt_id
WHERE rr.status = 'success'
GROUP BY p.category, pm.top_brand
ORDER BY p.category, wins DESC;

-- 8) Pull sample responses for qualitative review
SELECT
  rr.model_name,
  p.category,
  p.prompt_text,
  pm.top_brand,
  pm.sentiment,
  pm.key_features
FROM parsed_metrics pm
JOIN raw_responses rr ON rr.id = pm.response_id
JOIN prompts p ON p.id = rr.prompt_id
WHERE rr.status = 'success'
ORDER BY rr.model_name, p.category
LIMIT 25;

-- 1. Count elements in network
SELECT
  (SELECT COUNT(*) FROM bus)  AS num_buses,
  (SELECT COUNT(*) FROM line) AS num_lines,
  (SELECT COUNT(*) FROM load) AS num_loads;

-- 2. Total load in MW
SELECT SUM(p_mw) AS total_load_mw FROM load;

-- 3. Show load at each bus
SELECT
  b.bus_id,
  b.voltage_kv,
  COALESCE(l.p_mw, 0) AS p_mw,
  COALESCE(l.q_mvar, 0) AS q_mvar
FROM bus b
LEFT JOIN load l ON b.bus_id = l.bus_id
ORDER BY b.bus_id;

-- 4) Duplicate bus IDs
SELECT bus_id, COUNT(*) AS cnt
FROM bus
GROUP BY bus_id
HAVING COUNT(*) > 1;

-- 5) Duplicate line IDs
SELECT line_id, COUNT(*) AS cnt
FROM line
GROUP BY line_id
HAVING COUNT(*) > 1;

-- 6) Lines with missing/invalid parameters
SELECT *
FROM line
WHERE r_ohm   IS NULL OR x_ohm   IS NULL OR rate_mva IS NULL
   OR r_ohm  <= 0     OR x_ohm  <= 0     OR rate_mva <= 0;


-- 7) Check invalid lines
SELECT *
FROM line
WHERE from_bus NOT IN (SELECT bus_id FROM bus)
   OR to_bus NOT IN (SELECT bus_id FROM bus);

-- 8) Check high load buses
SELECT *
FROM load
WHERE p_mw > 0.10
ORDER BY p_mw DESC;
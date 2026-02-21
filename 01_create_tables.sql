DROP TABLE IF EXISTS bus;
DROP TABLE IF EXISTS line;
DROP TABLE IF EXISTS load;
DROP TABLE IF EXISTS load_profile;

CREATE TABLE bus (
  bus_id INTEGER PRIMARY KEY,
  voltage_kv REAL
);

CREATE TABLE line (
  line_id INTEGER PRIMARY KEY,
  from_bus INTEGER,
  to_bus INTEGER,
  r_ohm REAL,
  x_ohm REAL,
  rate_mva REAL
);

CREATE TABLE load (
  bus_id INTEGER,
  p_mw REAL,
  q_mvar REAL
);

CREATE TABLE load_profile (
  hour INTEGER PRIMARY KEY,
  multiplier REAL
);
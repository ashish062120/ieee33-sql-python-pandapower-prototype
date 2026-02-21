# IEEE 33-Bus Network Modelling using Python, SQL and Pandapower

This repository demonstrates a data-driven approach to electric network modelling using the IEEE 33-bus distribution system. The project integrates Python, SQL (SQLite3), and pandapower to perform network analysis, data validation, and time-series load flow simulations.

---

## Overview

To reflect a modern data-driven approach in network modelling, this workflow simulates a realistic utility-style data pipeline:

1. Network data (bus, line, load) stored in CSV files  
2. Data loaded into a structured SQL database  
3. SQL queries used for validation and analytics  
4. Python integrates with the database to build a pandapower model  
5. Time-series load flow simulation performed  
6. Results visualised using plots and violation checks

---

## Salient Features

- IEEE 33-bus distribution network modelling  
- SQL-based data management and validation  
- Python-based automation for power system analysis  
- Pandapower load flow simulation  
- Time-series load modelling (hourly profiles)  
- Voltage profile, line loading analysis and violation check  
- Network topology visualisation through coordinates and connectivity 
- Data quality checks (missing buses, invalid lines, etc.)

---

## Key Analysis

### Load Flow Analysis
- AC load flow using Newton-Raphson method  
- Voltage profile across all buses  
- Line loading and network losses  

### Time-Series Simulation
- Hourly load profile simulation  
- Voltage envelope analysis (min/max voltage over time)  
- Network stress evaluation  

### Data Validation (SQL)
- Missing or invalid network elements  
- Connectivity checks  
- Duplicate entries  
- Load aggregation  

---

## Example Outputs

- Network topology graph  
- Load distribution across buses  
- Voltage profile plots  
- Time-series voltage envelope  
- Line loading analysis  

---

## Project Structure

ieee33-sql-python-demo/
├── data/      (Input CSV files: bus, line, load, profiles)
├── sql/       (SQL scripts: create tables, analysis queries)
├── src/       (Python scripts)
├── outputs/   (Generated results: DB, plots, CSV exports)
└── README.md

## Install dependencies:

- Python  
- Pandas 
- Numpy 
- SQLite3 (SQL)  
- Pandapower  
- NetworkX  
- Matplotlib  

---

## How to Run

2. Run the main script: python src/run_demo.py 

3. Outputs will be saved in the `outputs/` folder.

---

## Future Improvements

- Integration with real network datasets (e.g. NEM)  
- DER/PV modelling and voltage rise analysis  
- Dynamic Operating Envelope (DOE) calculation  
- Dashboard visualisation using React / FastAPI  

---

## Author

Dr. Ashish Kumar Karmaker  
Electrical & Power Systems Engineer  

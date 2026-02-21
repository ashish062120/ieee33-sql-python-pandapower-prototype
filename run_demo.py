import sqlite3
import pandas as pd
from pathlib import Path
import networkx as nx
import numpy as np
import pandapower as pp
import matplotlib.pyplot as plt
import pandapower.plotting as plot

# Folder path
BASE_DIR = Path(__file__).resolve().parent.parent

# File paths
bus_file = BASE_DIR / "data" / "ieee33_bus.csv"
line_file = BASE_DIR / "data" / "ieee33_line.csv"
load_file = BASE_DIR / "data" / "ieee33_load.csv"

create_sql_file = BASE_DIR / "sql" / "01_create_tables.sql"
query_sql_file = BASE_DIR / "sql" / "02_analysis_queries.sql"

# Database path
db_path = BASE_DIR / "outputs" / "network.db"

# Connecting to database
conn = sqlite3.connect(db_path)

# Creating tables
with open(create_sql_file, "r") as f:
    conn.executescript(f.read())

# Loading CSV data into tables
bus_df = pd.read_csv(bus_file)
line_df = pd.read_csv(line_file)
load_df = pd.read_csv(load_file)

bus_df.to_sql("bus", conn, if_exists="append", index=False)
line_df.to_sql("line", conn, if_exists="append", index=False)
load_df.to_sql("load", conn, if_exists="append", index=False)

# Running SQL queries
with open(query_sql_file, "r") as f:
    queries = f.read().split(";")

print("\n++++ SQL RESULTS +++++\n")

for q in queries:
    q = q.strip()
    if q:
        try:
            result = pd.read_sql_query(q, conn)
            print(result)
        except Exception as e:
            print("Error:", e)

# -------------------------------
# Plotting Section
# -------------------------------

print("\nCreating plots...")

# Reading data from database
bus_load_df = pd.read_sql_query("""
SELECT b.bus_id, COALESCE(l.p_mw, 0) AS p_mw
FROM bus b
LEFT JOIN load l ON b.bus_id = l.bus_id
ORDER BY b.bus_id
""", conn)

# Plot 1: Network topology using graph/connection
line_df = pd.read_sql_query("SELECT from_bus, to_bus FROM line", conn)

G = nx.Graph()

for _, row in line_df.iterrows():
    G.add_edge(row["from_bus"], row["to_bus"])

plt.figure()
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_size=300)
plt.title("IEEE 33 Bus Network Topology")
plt.savefig("outputs/network_topology.png")
plt.close()

# Plot 2: Load per bus
plt.figure()
plt.bar(bus_load_df["bus_id"], bus_load_df["p_mw"])
plt.xlabel("Bus ID")
plt.ylabel("Load (MW)")
plt.title("Load Distribution Across IEEE 33 Bus Network")
plt.savefig("outputs/load_per_bus.png")
plt.close()

# Plot 3: Load distribution histogram
plt.figure()
plt.hist(bus_load_df["p_mw"], bins=10)
plt.xlabel("Load (MW)")
plt.ylabel("Number of Buses")
plt.title("Load Distribution Across Network")
plt.savefig("outputs/load_histogram.png")
plt.close()

# Plot 4: Network topology by manually setting coordinates
pos = {
    # main feeder 1-18
    1:(0,0), 2:(1,0), 3:(2,0), 4:(3,0), 5:(4,0), 6:(5,0), 7:(6,0),
    8:(7,0), 9:(8,0), 10:(9,0), 11:(10,0), 12:(11,0), 13:(12,0),
    14:(13,0), 15:(14,0), 16:(15,0), 17:(16,0), 18:(17,0),

    # branch from bus 2: 19-22 (up)
    19:(1,1), 20:(1,2), 21:(1,3), 22:(1,4),

    # branch from bus 3: 23-25 (up)
    23:(2,1), 24:(2,2), 25:(2,3),

    # branch from bus 6: 26-33 (down)
    26:(5,-1), 27:(6,-1), 28:(7,-1), 29:(8,-1),
    30:(9,-1), 31:(10,-1), 32:(11,-1), 33:(12,-1),
}
plt.figure(figsize=(12, 5))
nx.draw(G, pos, with_labels=True, node_size=350, font_size=8)
plt.title("IEEE 33-bus Topology (Fixed coordinates)")
plt.savefig("outputs/network_topology_fixed.png", dpi=200)
plt.close()


print("\n++++ Building pandapower network from SQL tables ++++")

# Reading tables from SQLite
bus_df  = pd.read_sql_query("SELECT bus_id, voltage_kv FROM bus ORDER BY bus_id", conn)
line_df = pd.read_sql_query("SELECT line_id, from_bus, to_bus, r_ohm, x_ohm, rate_mva FROM line ORDER BY line_id", conn)
load_df = pd.read_sql_query("SELECT bus_id, p_mw, q_mvar FROM load ORDER BY bus_id", conn)

# Creating pandapower network
net = pp.create_empty_network(sn_mva=10.0)

# Creating buses
bus_map = {}
for _, r in bus_df.iterrows():
    b_id = int(r["bus_id"])
    vn_kv = float(r["voltage_kv"])
    bus_map[b_id] = pp.create_bus(net, vn_kv=vn_kv, name=f"Bus {b_id}")

# slack/ext_grid
pp.create_ext_grid(net, bus=bus_map[1], vm_pu=1.02, name="Slack")

# Creating lines from parameters(assumed length_km=1)
for _, r in line_df.iterrows():
    fb = int(r["from_bus"])
    tb = int(r["to_bus"])
    r_ohm = float(r["r_ohm"])
    x_ohm = float(r["x_ohm"])
    rate_mva = float(r["rate_mva"])
    vn_kv = float(bus_df.loc[bus_df["bus_id"] == fb, "voltage_kv"].iloc[0])
    max_i_ka = rate_mva / (np.sqrt(3) * vn_kv)

    pp.create_line_from_parameters(
        net,
        from_bus=bus_map[fb],
        to_bus=bus_map[tb],
        length_km=1.0,
        r_ohm_per_km=r_ohm,
        x_ohm_per_km=x_ohm,
        c_nf_per_km=0.0,
        max_i_ka=max_i_ka,
        name=f"Line {int(r['line_id'])}"
    )

# Creating loads
for _, r in load_df.iterrows():
    b_id = int(r["bus_id"])
    pp.create_load(net, bus=bus_map[b_id], p_mw=float(r["p_mw"]), q_mvar=float(r["q_mvar"]), name=f"Load {b_id}")

# Running power flow
pp.runpp(net, algorithm="nr", max_iteration=30, tolerance_mva=1e-6, init="flat")

print("Power flow converged:", net.converged)

# Saving results as csv file
net.res_bus.to_csv("outputs/pandapower_res_bus.csv", index=True)
net.res_line.to_csv("outputs/pandapower_res_line.csv", index=True)

# Plotting bus Voltage profiles plot
vm_df = pd.DataFrame({
    "bus_id": list(bus_map.keys()),
    "pp_bus": list(bus_map.values())
})
vm_df["vm_pu"] = vm_df["pp_bus"].apply(lambda idx: net.res_bus.loc[idx, "vm_pu"])
vm_df = vm_df.sort_values("bus_id")

plt.figure(figsize=(10, 4))
plt.plot(vm_df["bus_id"], vm_df["vm_pu"], marker="o")
plt.xlabel("Bus ID")
plt.ylabel("Voltage (p.u.)")
plt.title("Voltage Profiles")
plt.ylim(0.9, 1.05)
plt.grid(True, alpha=0.3)
plt.savefig("outputs/voltage_profile_from_sql.png", dpi=200)
plt.close()

# Plotting Line loading
plt.figure(figsize=(10, 4))
plt.plot(net.res_line["loading_percent"].values, marker="o")
plt.xlabel("Line index")
plt.ylabel("Loading (%)")
plt.title("Line Loading")
plt.grid(True, alpha=0.3)
plt.savefig("outputs/line_loading_from_sql.png", dpi=200)
plt.close()

#Loading load profiles
profile_file = BASE_DIR / "data" / "load_profile_hourly.csv"

profile_df = pd.read_csv(profile_file)
profile_df.to_sql("load_profile", conn, if_exists="append", index=False)

# Reading hourly profile from SQLite
profile_df = pd.read_sql_query("SELECT hour, multiplier FROM load_profile ORDER BY hour", conn)

# Storing base loads
base_p = net.load["p_mw"].values.copy()
base_q = net.load["q_mvar"].values.copy()

hours = profile_df["hour"].values
mults = profile_df["multiplier"].values

vm_time = []       
loading_time = []  

for hour, mult in zip(hours, mults):
    net.load.loc[:, "p_mw"] = base_p * mult
    net.load.loc[:, "q_mvar"] = base_q * mult

    pp.runpp(net, algorithm="nr", max_iteration=30, tolerance_mva=1e-6)

    vm_time.append(net.res_bus["vm_pu"].values.copy())
    loading_time.append(net.res_line["loading_percent"].values.copy())

# Plotting time-seires voltage profile

vm_time = np.array(vm_time)
loading_time = np.array(loading_time)

vmin_ts = vm_time.min(axis=1)
vmax_ts = vm_time.max(axis=1)
lmax_ts = loading_time.max(axis=1)

plt.figure(figsize=(10,4))
plt.plot(hours, vmin_ts, marker="o", label="Min V (network)")
plt.xlabel("Hour")
plt.ylabel("Voltage (p.u.)")
plt.title("Network Voltage Over Time")
plt.grid(True, alpha=0.3)
plt.legend()
plt.savefig("outputs/voltage_timeseries.png", dpi=200)
plt.close()

plt.figure(figsize=(10,4))
plt.plot(hours, lmax_ts, marker="o")
plt.xlabel("Hour")
plt.ylabel("Max Line Loading (%)")
plt.title("Max Line Loading Over Time")
plt.grid(True, alpha=0.3)
plt.savefig("outputs/max_line_loading_timeseries.png", dpi=200)
plt.close()


# Plotting time-series Voltage profiles for selected buses
vm_time = np.array(vm_time)

# Selecting bus IDs
source_bus_id = 1
middle1_bus_id = 26
middle2_bus_id = 33
far_end_bus_id = 18

# Converting bus IDs to pandapower bus indices
source_pp = bus_map[source_bus_id]
middle1_pp = bus_map[middle1_bus_id]
middle2_pp = bus_map[middle2_bus_id]
far_pp = bus_map[far_end_bus_id]

plt.figure(figsize=(10, 4))
plt.plot(hours, vm_time[:, source_pp], marker="o", label=f"Source Bus {source_bus_id}")
plt.plot(hours, vm_time[:, middle1_pp], marker="o", label=f"Middle1 Bus {middle1_bus_id}")
plt.plot(hours, vm_time[:, middle2_pp], marker="o", label=f"Middle2 Bus {middle2_bus_id}")
plt.plot(hours, vm_time[:, far_pp], marker="o", label=f"Far-end Bus {far_end_bus_id}")

plt.xlabel("Hour")
plt.ylabel("Voltage (p.u.)")
plt.title("Time-series Voltage Profile")
plt.ylim(0.9, 1.05)
plt.grid(True, alpha=0.3)
plt.legend()
plt.savefig("outputs/voltage_timeseries_selected_buses.png", dpi=200)
plt.close()


print("\n ++++ Violation check ++++")

# Voltage limits 
V_MIN = 0.95
V_MAX = 1.05

# Thermal limit
LOADING_LIMIT = 100  # %

# Voltage check
vmin = net.res_bus["vm_pu"].min()
vmax = net.res_bus["vm_pu"].max()

print(f"Min voltage: {vmin:.3f} pu")
print(f"Max voltage: {vmax:.3f} pu")

if vmin < V_MIN or vmax > V_MAX:
    print("Voltage violation detected")
else:
    print(" Voltage within limits")

# -------------------------------
# Line loading check
# -------------------------------
lmax = net.res_line["loading_percent"].max()

print(f"Max line loading: {lmax:.2f} %")

if lmax > LOADING_LIMIT:
    print("Thermal loading violation detected")
else:
    print("No thermal violations")

conn.close()

print("\nDONE")


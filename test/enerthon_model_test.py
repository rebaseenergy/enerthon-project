import pandas as pd
import numpy as np
from enerthon.enerthon_model import model, model_input, model_results, solve_model


# Import data
df = pd.read_csv('./data/data.zip', header = 0, index_col=0, parse_dates = True)


# Assign value to every unique month-year
df['TM'] = df.index.month
df['TY'] = df.index.year
df['month_order'] = df['TM'] + (df['TY'] - df['TY'][0])*12 - df['TM'][0]+1
df = df.drop(columns=['TM', 'TY'])


# Set prices for buying/selling electricity, eg. Nordpool prices
df['price_buy_euros_kWh'] = 0.800 # SEK/kWh  --> Here fixed but it can be Nordpool prices
df['price_sell_euros_kWh'] = 0.0 # SEK/kWh --> Here fixed but it can be Nordpool prices



#%% Tarrif structures

# Example 1 - Fixed energy tariff
# Prices for Affärsverken Elnät AB (Fuse 16A, appartment)
fixed_charge = 145 # SEK/Month

df['grid_energy_import_fee'] = 45*0.01 # SEK/kWh
df['grid_energy_export_fee'] = 0 # SEK/kWh
df['grid_power_import_fee'] = 0 # SEK/kW-month
df['grid_power_export_fee'] = 0 # SEK/kW-month




# Example 2 - Power based tariff
# Prices for Bjäre Kraft ek för (Fuse 16, house)
fixed_charge = 141 # SEK/Month

df['grid_energy_import_fee'] = 0 # SEK/kWh
df['grid_energy_export_fee'] = 0 # SEK/kWh
df['grid_power_import_fee'] = 0 # SEK/kW-month
df['grid_power_export_fee'] = 0 # SEK/kW-month

# Set grid energy fee for different months, days and hours
for i in [1,2,3,11,12]:
    df.loc[(df.index.month == i),'grid_power_import_fee'] = 126

for i in [4,5,6,7,8,9,10]:
    for j in list(range(0,5)):
        for k in list(range(9,19)):
            df.loc[(df.index.month == i) & (df.index.weekday == j) & (df.index.hour == k),'grid_power_import_fee'] = 75




# Example 3 - Time based tariff
# Prices for Ellevio AB Dalarna Södra (Fuse 16A, house)
fixed_charge = 255 # SEK/Month

df['grid_energy_import_fee'] = 9*0.01 # SEK/kWh
df['grid_energy_export_fee'] = 0 # SEK/kWh
df['grid_power_import_fee'] = 0 # SEK/kW-month
df['grid_power_export_fee'] = 0 # SEK/kW-month

# Set grid energy fee for different months, days and hours
for i in [1,2,3,11,12]:
    for j in list(range(0,5)):
        for k in list(range(8,22)):
            df.loc[(df.index.month == i) & (df.index.weekday == j) & (df.index.hour == k),'grid_energy_import_fee'] = 58*0.01


for i in [4,5,6,7,8,9,10]:
    df.loc[(df.index.month == i),'grid_energy_import_fee'] = 9*0.01




#%% Base case (Load + Heat demand covered by gas boiler)
data = {'generation': (0*df['PV']).to_list(),
        'demand': df['Load'].to_list(),
        'heat_demand': df['Heat'].to_list(),
        
        'battery_min_level': 0.0,
        'battery_capacity': 0.0,
        'battery_charge_max': 0.5,
        'battery_discharge_max': 0.5,
        'battery_efficiency_charge': 0.9,
        'battery_efficiency_discharge': 0.9,
        'bel_ini_level': 0.0,
        'bel_fin_level': 0.0,
        'battery_grid_charging': True,
        
        'tes_min_level': 0.0,
        'tes_capacity': 0.0,
        'tes_charge_max': 1.0,
        'tes_discharge_max': 1.0,
        'tes_losses': 0.01,
        'tes_ini_level': 0.0,
        'tes_fin_level': 0.0,   
        
        'energy_price_buy': df['price_buy_euros_kWh'].to_list(),
        'energy_price_sell': df['price_sell_euros_kWh'].to_list(),
        'grid_fixed_fee': fixed_charge,
        'grid_energy_import_fee': df['grid_energy_import_fee'].to_list(),
        'grid_energy_export_fee': df['grid_energy_export_fee'].to_list(),
        'grid_power_import_fee': df['grid_power_import_fee'].to_list(),
        'grid_power_export_fee': df['grid_power_export_fee'].to_list(),
        
        'fuel_price': 0.7,
        
        'boiler_capacity': 300,
        'boiler_efficiency': 0.95,
        
        'month_order': df['month_order'].to_list(),
        'dt': 1,
}
    

# Create model data structure
model_data = model_input(data) 

# Create model instance with data
model_instance = model(model_data)

# Solve
solver = {'name':"glpk",'path': "C:/glpk-4.65/w64/glpsol"}
solution = solve_model(model_instance, solver) 

# Get results
base_results = model_results(solution)


#%% Scenario (PV  + Load + Heat demand covered by heat pumps + heat storage + batteries)
data = {'generation': df['PV'].to_list(),
        'demand': df['Load'].to_list(),
        'heat_demand': df['Heat'].to_list(),
        
        'battery_min_level': 0.0,
        'battery_capacity': 5.0,
        'battery_charge_max': 0.5,
        'battery_discharge_max': 0.5,
        'battery_efficiency_charge': 0.9,
        'battery_efficiency_discharge': 0.9,
        'bel_ini_level': 0.0,
        'bel_fin_level': 0.0,
        'battery_grid_charging': True,
        
        'tes_min_level': 0.0,
        'tes_capacity': 100.0,
        'tes_charge_max': 1.0,
        'tes_discharge_max': 1.0,
        'tes_losses': 0.01,
        'tes_ini_level': 0.0,
        'tes_fin_level': 0.0,   
        
        'energy_price_buy': df['price_buy_euros_kWh'].to_list(),
        'energy_price_sell': df['price_sell_euros_kWh'].to_list(),
        'grid_fixed_fee': fixed_charge,
        'grid_energy_import_fee': df['grid_energy_import_fee'].to_list(),
        'grid_energy_export_fee': df['grid_energy_export_fee'].to_list(),
        'grid_power_import_fee': df['grid_power_import_fee'].to_list(),
        'grid_power_export_fee': df['grid_power_export_fee'].to_list(),
        
        'fuel_price': 0.7,
        
        'heat_pump_capacity': 300,
        'heat_pump_cop': 3,
        
        'month_order': df['month_order'].to_list(),
        'dt': 1,
}
    

# Create model data structure
model_data = model_input(data) 

# Create model instance with data
model_instance = model(model_data)

# Solve
solver = {'name':"glpk",'path': "C:/glpk-4.65/w64/glpsol"}
solution = solve_model(model_instance, solver) 

# Get results
results = model_results(solution)


# Savings
savings = base_results['cost_total'] - results['cost_total']
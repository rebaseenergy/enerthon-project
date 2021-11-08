from pyomo.environ import ConcreteModel, AbstractModel
from pyomo.environ import Set,Param,Var,Objective,Constraint
from pyomo.environ import PositiveIntegers, NonNegativeReals, Reals
from pyomo.environ import SolverFactory, minimize
from pyomo.environ import value
from pyomo.core.base.param import SimpleParam
import numpy as np


def solve_model(model_instance, solver):
    if 'path' in solver:
        optimizer = SolverFactory(solver['name'], executable=solver['path'])
    else:
        optimizer = SolverFactory(solver['name'])

    optimizer.solve(model_instance, tee=True, keepfiles=False)

    return model_instance


def model(model_data):


    model = ConcreteModel()

    ## SETS
    model.T = Set(dimen=1, ordered=True, initialize=model_data[None]['T']) # Periods
    model.M = Set(dimen=1, ordered=True, initialize=np.array(list(set(model_data[None]['month_order'].values())))) # Months



    ## PARAMETERS
    model.demand                        = Param(model.T, within=Reals, initialize=model_data[None]['demand'])
    model.generation                    = Param(model.T, initialize=model_data[None]['generation'])
    model.heat_demand                   = Param(model.T, within=Reals, initialize=model_data[None]['heat_demand'])

    model.battery_min_level             = Param(initialize=model_data[None]['battery_min_level'])
    model.battery_capacity              = Param(initialize=model_data[None]['battery_capacity'])
    model.battery_charge_max            = Param(initialize=model_data[None]['battery_charge_max'])
    model.battery_discharge_max         = Param(initialize=model_data[None]['battery_discharge_max'])
    model.battery_efficiency_charge     = Param(initialize=model_data[None]['battery_efficiency_charge'])
    model.battery_efficiency_discharge  = Param(initialize=model_data[None]['battery_efficiency_discharge'])
    model.bel_ini_level                 = Param(initialize=model_data[None]['bel_ini_level'])
    model.bel_fin_level                 = Param(initialize=model_data[None]['bel_fin_level'])
    model.battery_grid_charging         = Param(initialize=model_data[None]['battery_grid_charging'])
    
    model.energy_price_buy              = Param(model.T, initialize=model_data[None]['energy_price_buy'])
    model.energy_price_sell             = Param(model.T, initialize=model_data[None]['energy_price_sell'])
    
    model.grid_fixed_fee                = Param(initialize=model_data[None]['grid_fixed_fee'])
    model.grid_energy_import_fee        = Param(model.T, within=Reals, initialize=model_data[None]['grid_energy_import_fee'])
    model.grid_energy_export_fee        = Param(model.T, within=Reals, initialize=model_data[None]['grid_energy_export_fee'])
    
    model.grid_power_import_fee         = Param(model.T, within=Reals, initialize=model_data[None]['grid_power_import_fee'])
    model.grid_power_export_fee         = Param(model.T, within=Reals, initialize=model_data[None]['grid_power_export_fee'])
    
    model.fuel_price                    = Param(initialize=model_data[None]['fuel_price'])
    
    model.boiler_capacity               = Param(initialize=model_data[None]['boiler_capacity'])
    model.boiler_efficiency             = Param(initialize=model_data[None]['boiler_efficiency'])
    model.heat_pump_capacity            = Param(initialize=model_data[None]['heat_pump_capacity'])
    model.heat_pump_cop                 = Param(initialize=model_data[None]['heat_pump_cop'])
    
    model.tes_min_level                 = Param(initialize=model_data[None]['tes_min_level'])
    model.tes_capacity                  = Param(initialize=model_data[None]['tes_capacity'])
    model.tes_charge_max                = Param(initialize=model_data[None]['tes_charge_max'])
    model.tes_discharge_max             = Param(initialize=model_data[None]['tes_discharge_max'])
    model.tes_losses                    = Param(initialize=model_data[None]['tes_losses'])
    model.tes_ini_level                 = Param(initialize=model_data[None]['tes_ini_level'])
    model.tes_fin_level                 = Param(initialize=model_data[None]['tes_fin_level'])

    model.dt                            = Param(initialize=model_data[None]['dt'])



    ## VARIABLE LIMITS
    def soc_limits(model, t):
        return (model.battery_min_level*model.battery_capacity, model.battery_capacity)
    def charge_limits(model, t):
        return (0.0, model.battery_charge_max*model.battery_capacity)
    def discharge_limits(model, t):
        return (0.0, model.battery_discharge_max*model.battery_capacity)

    def tes_limits(model, t):
        return (model.tes_min_level*model.tes_capacity, model.tes_capacity)
    def tes_charge_limits(model, t):
        return (0.0, model.tes_charge_max*model.tes_capacity)
    def tes_discharge_limits(model, t):
        return (0.0, model.tes_discharge_max*model.tes_capacity)

    def heat_pump_limits(model, t):
        return (0.0, model.heat_pump_capacity)
    def boiler_limits(model, t):
        return (0.0, model.boiler_capacity)


    ## VARIABLES
    model.COST_ENERGY                   = Var(model.T, within=Reals)
    model.COST_GRID_ENERGY_IMPORT       = Var(model.T, within=Reals)
    model.COST_GRID_ENERGY_EXPORT       = Var(model.T, within=Reals)
    model.COST_GRID_POWER_IMPORT        = Var(model.T, within=NonNegativeReals)
    model.COST_GRID_POWER_EXPORT        = Var(model.T, within=NonNegativeReals)
    model.COST_GRID_POWER_IMPORT_MAX    = Var(model.M, within=Reals)
    model.COST_GRID_POWER_EXPORT_MAX    = Var(model.M, within=Reals)
    model.COST_GRID_FIXED               = Var(within=Reals)
    model.COST_FUEL                     = Var(model.T, within=Reals)
    
    model.P_BUY                         = Var(model.T, within=NonNegativeReals)
    model.P_SELL                        = Var(model.T, within=NonNegativeReals)
    
    model.BEL                           = Var(model.T, within=NonNegativeReals, bounds=soc_limits)
    model.B_IN                          = Var(model.T, within=NonNegativeReals, bounds=charge_limits)
    model.B_OUT                         = Var(model.T, within=NonNegativeReals, bounds=discharge_limits)

    model.TES                           = Var(model.T, within=NonNegativeReals, bounds=tes_limits)
    model.TES_IN                        = Var(model.T, within=NonNegativeReals, bounds=tes_charge_limits)
    model.TES_OUT                       = Var(model.T, within=NonNegativeReals, bounds=tes_discharge_limits)

    model.Q_HP                          = Var(model.T, within=NonNegativeReals, bounds=heat_pump_limits)
    model.P_HP                          = Var(model.T, within=NonNegativeReals)

    model.Q_BO                          = Var(model.T, within=NonNegativeReals, bounds=boiler_limits)
    model.F_BO                          = Var(model.T, within=NonNegativeReals)


    ## OBJECTIVE
    # Minimize cost
    def total_cost(model):
        return sum(model.COST_ENERGY[t] + model.COST_GRID_ENERGY_IMPORT[t] + model.COST_GRID_ENERGY_EXPORT[t] for t in model.T) \
        + sum(model.COST_GRID_POWER_IMPORT_MAX[m] + model.COST_GRID_POWER_EXPORT_MAX[m] for m in model.M) + model.COST_GRID_FIXED \
        + sum(model.COST_FUEL[t] for t in model.T)
    model.total_cost = Objective(rule=total_cost, sense=minimize)




    ## CONSTRAINTS
    # Energy cost
    def energy_cost(model, t):
        return model.COST_ENERGY[t] == model.energy_price_buy[t]*model.P_BUY[t]*model.dt - model.energy_price_sell[t]*model.P_SELL[t]*model.dt
    model.energy_cost = Constraint(model.T, rule=energy_cost)



    # Grid fixed cost
    def grid_fixed_cost(model):
        return model.COST_GRID_FIXED == model.grid_fixed_fee*len(model.M)
    model.grid_fixed_cost = Constraint(rule=grid_fixed_cost)
    


    # Grid energy import cost
    def grid_energy_import_cost(model, t):
        return model.COST_GRID_ENERGY_IMPORT[t] == model.grid_energy_import_fee[t]*model.P_BUY[t]*model.dt
    model.grid_energy_import_cost = Constraint(model.T, rule=grid_energy_import_cost)
    
    # Grid energy export cost
    def grid_energy_export_cost(model, t):
        return model.COST_GRID_ENERGY_EXPORT[t] == model.grid_energy_export_fee[t]*model.P_SELL[t]*model.dt
    model.grid_energy_export_cost = Constraint(model.T, rule=grid_energy_export_cost)



    # Grid power import cost
    def grid_power_import_cost(model, t):
        return model.COST_GRID_POWER_IMPORT[t] >= model.grid_power_import_fee[t]*(model.P_BUY[t]-model.P_SELL[t])
    model.grid_power_import_cost = Constraint(model.T, rule=grid_power_import_cost)
    
    # Grid power export cost
    def grid_power_export_cost(model, t):
        return model.COST_GRID_POWER_EXPORT[t] >= model.grid_power_export_fee[t]*(model.P_SELL[t]-model.P_BUY[t])
    model.grid_power_export_cost = Constraint(model.T, rule=grid_power_export_cost)

    # Max grid import cost
    def max_grid_power_import_cost(model, t):
        return model.COST_GRID_POWER_IMPORT_MAX[model_data[None]['month_order'][t]] >= model.COST_GRID_POWER_IMPORT[t]
    model.max_grid_power_import_cost = Constraint(model.T, rule=max_grid_power_import_cost)

    # Max grid export cost
    def max_grid_power_export_cost(model, t):
        return model.COST_GRID_POWER_EXPORT_MAX[model_data[None]['month_order'][t]] >= model.COST_GRID_POWER_EXPORT[t]
    model.max_grid_power_export_cost = Constraint(model.T, rule=max_grid_power_export_cost)


    # Fuel cost
    def fuel_cost(model, t):
        return model.COST_FUEL[t] == model.fuel_price*model.F_BO[t]*model.dt
    model.fuel_cost = Constraint(model.T, rule=fuel_cost)


    # Power balance
    def power_balance(model, t):
        return model.P_SELL[t] - model.P_BUY[t] ==  model.generation[t] + model.B_OUT[t] - model.B_IN[t] - model.demand[t] - model.P_HP[t]
    model.power_balance = Constraint(model.T, rule=power_balance)


    # Heat balance
    def heat_balance(model, t):
        return model.Q_BO[t] + model.Q_HP[t] ==  model.heat_demand[t] - model.TES_OUT[t] + model.TES_IN[t]
    model.heat_balance = Constraint(model.T, rule=heat_balance)


    # Battery energy balance
    def battery_soc(model, t):
        if t==model.T.first():
            return model.BEL[t] - model.bel_ini_level*model.battery_capacity == model.battery_efficiency_charge*model.B_IN[t]*model.dt  - (1/model.battery_efficiency_discharge)*model.B_OUT[t]*model.dt
        else:
            return model.BEL[t] - model.BEL[model.T.prev(t)] == model.battery_efficiency_charge*model.B_IN[t]*model.dt  - (1/model.battery_efficiency_discharge)*model.B_OUT[t]*model.dt
    model.battery_soc = Constraint(model.T, rule=battery_soc)


    # Heat storage energy balance
    def heat_storage_soc(model, t):
        if t==model.T.first():
            return model.TES[t] - (1-model.tes_losses)*model.tes_ini_level*model.tes_capacity == model.TES_IN[t]*model.dt - model.TES_OUT[t]*model.dt
        else:
            return model.TES[t] - (1-model.tes_losses)*model.TES[model.T.prev(t)] == model.TES_IN[t]*model.dt - model.TES_OUT[t]*model.dt
    model.heat_storage_soc = Constraint(model.T, rule=heat_storage_soc)


    # Battery charging from grid
    def no_grid_charging(model, t):
        if value(model.battery_grid_charging) == False:
            return model.P_BUY[t] <= model.demand[t] + model.P_HP[t] 
        else:
            return Constraint.Skip
    model.no_grid_charging = Constraint(model.T, rule=no_grid_charging)


    # Fuel boiler
    def fuel_boiler_gen(model, t):
        return model.F_BO[t] == (1/model.boiler_efficiency)*model.Q_BO[t]
    model.fuel_boiler_gen = Constraint(model.T, rule=fuel_boiler_gen)


    # Heat pump
    def heat_pump_gen(model, t):
        return model.Q_HP[t] == model.heat_pump_cop*model.P_HP[t]
    model.heat_pump_gen = Constraint(model.T, rule=heat_pump_gen)
    
    
    

    # Fix battery soc in the last period
    if value(model.bel_fin_level) > 0:
        model.BEL[model.T.last()].fix(model.bel_fin_level*model.battery_capacity)

    
    # Fix tes soc in the last period
    if value(model.tes_fin_level) > 0:
        model.TES[model.T.last()].fix(model.tes_fin_level*model.tes_capacity)
    

    return model


def model_input(data):


    periods = np.arange(1, len(data['generation'])+1)
    generation = dict(zip(periods,  data['generation']))


    if "demand" in data:
        demand = dict(zip(periods,  data['demand']))
    else:
        demand = [0] * len(data['generation'])
        demand = dict(zip(periods,  demand))
        
    if "heat_demand" in data:
        heat_demand = dict(zip(periods,  data['heat_demand']))
    else:
        heat_demand = [0] * len(data['generation'])
        heat_demand = dict(zip(periods,  heat_demand))        



    if "battery_capacity" in data:
        battery_capacity = data['battery_capacity']
    else:
        battery_capacity = 0

    if "battery_min_level" in data:
        battery_min_level = data['battery_min_level']
    else:
        battery_min_level = 0

    if "battery_charge_max" in data:
        battery_charge_max = data['battery_charge_max']
    else:
        battery_charge_max = 1

    if "battery_discharge_max" in data:
        battery_discharge_max = data['battery_discharge_max']
    else:
        battery_discharge_max = 1

    if "battery_efficiency_charge" in data:
        battery_efficiency_charge = data['battery_efficiency_charge']
    else:
        battery_efficiency_charge = 0.95

    if "battery_efficiency_discharge" in data:
        battery_efficiency_discharge = data['battery_efficiency_discharge']
    else:
        battery_efficiency_discharge = 0.95

    if "bel_ini_level" in data:
        bel_ini_level = data['bel_ini_level']
    else:
        bel_ini_level = 0

    if "bel_fin_level" in data:
        bel_fin_level = data['bel_fin_level']
    else:
        bel_fin_level = 0
        
    if "battery_grid_charging" in data:
        battery_grid_charging = data['battery_grid_charging']
    else:
        battery_grid_charging = True        
        

    if "tes_capacity" in data:
        tes_capacity = data['tes_capacity']
    else:
        tes_capacity = 0

    if "tes_min_level" in data:
        tes_min_level = data['tes_min_level']
    else:
        tes_min_level = 0

    if "tes_charge_max" in data:
        tes_charge_max = data['tes_charge_max']
    else:
        tes_charge_max = 1

    if "tes_discharge_max" in data:
        tes_discharge_max = data['tes_discharge_max']
    else:
        tes_discharge_max = 1

    if "tes_losses" in data:
        tes_losses = data['tes_losses']
    else:
        tes_losses = 0.02

    if "tes_ini_level" in data:
        tes_ini_level = data['tes_ini_level']
    else:
        tes_ini_level = 0

    if "tes_fin_level" in data:
        tes_fin_level = data['tes_fin_level']
    else:
        tes_fin_level = 0


    energy_price_buy = dict(zip(periods,  data['energy_price_buy']))
    energy_price_sell = dict(zip(periods,  data['energy_price_sell']))
    
    grid_fixed_fee = data['grid_fixed_fee']
    grid_energy_import_fee = dict(zip(periods,  data['grid_energy_import_fee']))
    grid_energy_export_fee = dict(zip(periods,  data['grid_energy_export_fee']))
    grid_power_import_fee = dict(zip(periods,  data['grid_power_import_fee']))
    grid_power_export_fee = dict(zip(periods,  data['grid_power_export_fee']))


    if "fuel_price" in data:
        fuel_price = data['fuel_price']
    else:
        fuel_price = 0

    if "heat_pump_capacity" in data:
        heat_pump_capacity = data['heat_pump_capacity']
    else:
        heat_pump_capacity = 0

    if "heat_pump_cop" in data:
        heat_pump_cop = data['heat_pump_cop']
    else:
        heat_pump_cop = 1
        
    if "boiler_capacity" in data:
        boiler_capacity = data['boiler_capacity']
    else:
        boiler_capacity = 0
        
    if "boiler_efficiency" in data:
        boiler_efficiency = data['boiler_efficiency']
    else:
        boiler_efficiency = 0.95        
    

    if "dt" in data:
        dt = data['dt']
    else:
        dt = 1

    month_order = dict(zip(periods,  data['month_order']))

    # Create model data input dictionary
    model_data = {None: {
        'T': periods,

        'generation': generation,
        'demand': demand,
        'heat_demand': heat_demand,

        'battery_min_level': battery_min_level,
        'battery_capacity': battery_capacity,
        'battery_charge_max': battery_charge_max,
        'battery_discharge_max': battery_discharge_max,
        'battery_efficiency_charge': battery_efficiency_charge,
        'battery_efficiency_discharge': battery_efficiency_discharge,
        'battery_grid_charging': battery_grid_charging,
        'bel_ini_level': bel_ini_level,
        'bel_fin_level': bel_fin_level,
        
        'tes_min_level': tes_min_level,
        'tes_capacity': tes_capacity,
        'tes_charge_max': tes_charge_max,
        'tes_discharge_max': tes_discharge_max,
        'tes_losses': tes_losses,
        'tes_ini_level': tes_ini_level,
        'tes_fin_level': tes_fin_level,        

        'energy_price_buy': energy_price_buy,
        'energy_price_sell': energy_price_sell,
        
        'grid_fixed_fee': grid_fixed_fee,
        'grid_energy_import_fee': grid_energy_import_fee,
        'grid_energy_export_fee': grid_energy_export_fee,
        'grid_power_import_fee': grid_power_import_fee,
        'grid_power_export_fee': grid_power_export_fee,
        
        'fuel_price': fuel_price,
        
        'heat_pump_capacity': heat_pump_capacity,
        'heat_pump_cop': heat_pump_cop,
        'boiler_capacity': boiler_capacity,
        'boiler_efficiency': boiler_efficiency,

        'month_order': month_order,
        'dt': dt,
    }}

    return model_data


def model_results(solution):
    
    s = dict()
    
    s['cost_total'] = solution.total_cost()
    s['cost_energy'] = value(solution.COST_ENERGY[:])
    s['cost_grid_energy_import'] = value(solution.COST_GRID_ENERGY_IMPORT[:])
    s['cost_grid_energy_export'] = value(solution.COST_GRID_ENERGY_EXPORT[:])
    s['cost_grid_power_import'] = value(solution.COST_GRID_POWER_IMPORT_MAX[:])
    s['cost_grid_power_export'] = value(solution.COST_GRID_POWER_EXPORT_MAX[:])
    s['cost_grid_power_fixed'] = value(solution.COST_GRID_FIXED)
    
    s['cost_fuel'] = value(solution.COST_FUEL[:])
        
    s['power_buy'] = value(solution.P_BUY[:])
    s['power_sell'] = value(solution.P_SELL[:])
    
    s['battery_soc'] = value(solution.BEL[:])
    s['battery_charge'] = value(solution.B_IN[:])
    s['battery_discharge'] = value(solution.B_OUT[:])

    s['tes_soc'] = value(solution.TES[:])
    s['tes_charge'] = value(solution.TES_IN[:])
    s['tes_discharge'] = value(solution.TES_OUT[:])
    
    s['heat_pump_heat_generation'] = value(solution.Q_HP[:])
    s['heat_pump_power_consumption'] = value(solution.P_HP[:])
    
    s['boiler_heat_generation'] = value(solution.Q_BO[:])
    s['boiler_fuel_consumption'] = value(solution.F_BO[:])

    return s
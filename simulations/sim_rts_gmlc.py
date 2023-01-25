from prescient.simulator import Prescient

# set some options
prescient_options = {
        "data_path":"../downloads/rts_gmlc/RTS-GMLC/RTS_Data/SourceData/",
        "input_format":"rts-gmlc",
        "simulate_out_of_sample":True,
        "run_sced_with_persistent_forecast_errors":True,
        "output_directory":"rts_gmlc_output",
        "start_date":"07-10-2020",
        "num_days":7,
        "sced_horizon":1,
        "ruc_mipgap":0.01,
        "reserve_factor":0.1,
        "deterministic_ruc_solver":"gurobi",
        "deterministic_ruc_solver_options":{"feas":"off", "DivingF":"on",},
        "sced_solver":"gurobi",
        "sced_frequency_minutes":60,
        "ruc_horizon":36,
        "compute_market_settlements":True,
        "monitor_all_contingencies":False,
        "output_solver_logs":False,
        "price_threshold":1000,
        "contingency_price_threshold":100,
        "reserve_price_threshold":5,
        }
# run the simulator
Prescient().simulate(**prescient_options)

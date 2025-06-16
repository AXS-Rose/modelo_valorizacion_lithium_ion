import numpy as np
import pandas as pd

# Funciones auxiliares
def synthetic_profile(dt=1, dis_curr=-0.5, charg_curr=0.5, lower_capacity=-2.5, upper_capacity=2.5, N=1000):
    # create a capacity profile to simulate a synthetic degradation profile
    capacity_profile = []  # List to store the synthetic capacity profile

    dis_cap = dis_curr * dt / 3600 # capacity step in Ah
    discharge_repetitions = int(lower_capacity / dis_cap)  # Number of repetitions for discharge steps

    charg_cap = charg_curr * dt / 3600 # capacity step in Ah
    charge_repetitions = int(upper_capacity / charg_cap)  # Number of repetitions for discharge steps
     
    for _ in range(N):
        # Fill the capacity profile with discharge and charge steps
        capacity_profile.extend([dis_cap] * discharge_repetitions)  # Fill with zeros for discharge steps    
        capacity_profile.extend([charg_cap] * charge_repetitions)  # Fill with zeros for discharge steps

    return capacity_profile

def profile_repeat(cap_profile, N=1000):
    """
    Repeat a given capacity profile N times to create a longer profile.
    
    Parameters:
    - cap_profile: List or array of capacity values.
    - N: Number of times to repeat the profile.
    
    Returns:
    - Repeated capacity profile as a list.
    """
    repeated_profile = cap_profile * N  # Repeat the capacity profile N times
    return repeated_profile

def log_a(a,x):
    y = np.log(x)/np.log(a)
    return y

def valorización(SOH_actual_prop, cap_0_prop, min_cap_app, valor_ideal, prop_cycles, ideal_cycles):
    """
    Calculate the current value of a battery based on its SOH and ideal value.
    
    Parameters:
    - SOH_actual: Current State of Health of the battery (as a percentage).
    - valor_ideal: Ideal value of the battery when it is new.
    
    Returns:
    - Current value of the battery.
    """

    min_SOH = min_cap_app/cap_0_prop # calculate minimum SOH for the proposed battery
    deg_factor = (1 - SOH_actual_prop) / (1 - max([0.6,min_SOH]))  # Calculate the degradation factor
    
    cycle_factor = np.clip(prop_cycles/ideal_cycles,0,1)
    
    valor_prop = valor_ideal * deg_factor * cycle_factor # compute the economic value of the proposed battery

    return valor_prop

def total_cycle(battery_model,initial_SOH,terminal_SOH,
                cap_profile,profile_amb_temp,initial_SOC,
                MC_runs=10):
    """
    Calculate the total amount of equivalent cycles a battery can perform of a certain usage profile

    Parameters:
    - SOH_actual: Current State of Health of the battery (as a percentage).
    - valor_ideal: Ideal value of the battery when it is new.

    Returns:
    - Current value of the battery.
    """

    total_soh_values = pd.DataFrame()  # DataFrame to store SOH (State of Health) values for each run
    total_eqcycle_values = np.array([])  # Numpy array to store equivalent cycle counts for each run
    soh_columns = [] # keep each run here first
    max_len = 0 # longest Q_values we have seen so far

    for i in range(MC_runs):

        eq_cycle_count = 0  # Counter for equivalent cycles simulated

        current_Q = battery_model.parameters["Qmax"] * initial_SOH  # Initial maximum capacity of the battery
        Q_values = [current_Q]  # List to store capacity values over time

        # Variables for the equivalent cycle calculation method
        dsoc = 0  # Change in SoC (State of Charge)
        soc_acc = 0  # Accumulated SoC change
        soc_inst_eqcycle = 1 * initial_SOC  # Initial SoC in percentage
        soc_counting_eqcycle = [soc_inst_eqcycle]  # List to track SoC changes

        # Iterate through all delta capacity values (dC_w10_standford_values2)
        for dc in cap_profile:
            dsoc = dc * 100 / current_Q  # Calculate change in SoC based on delta capacity
            soc_inst_eqcycle += dsoc  # Update the instantaneous SoC

            # Ensure SoC stays within valid bounds (0% to 100%)
            if soc_inst_eqcycle >= 100:
                soc_inst_eqcycle = 100
            elif soc_inst_eqcycle < 0:
                soc_inst_eqcycle = 0

            # Implementation of the equivalent cycle method
            if dsoc < 0:  # Only consider discharging events
                soc_acc += dsoc  # Accumulate SoC changes
                soc_counting_eqcycle.append(soc_inst_eqcycle)  # Track SoC changes

            # Check if an equivalent cycle is completed
            if -100 >= soc_acc:
                ssr = max(soc_counting_eqcycle) - min(soc_counting_eqcycle)
                assr = np.mean(soc_counting_eqcycle)
                eta_k_eqcycle = battery_model.get_factor(soc_counting_eqcycle, profile_amb_temp)  # Get degradation factor
                current_Q *= eta_k_eqcycle[0]  # Update the current capacity based on degradation
                current_soh = current_Q / battery_model.parameters["Qmax"]
                soc_acc = 0  # Reset accumulated SoC
                soc_counting_eqcycle = []  # Reset SoC tracking
                Q_values.append(current_Q)  # Append the updated capacity
                eq_cycle_count += 1  # Increment the equivalent cycle count

                print(f'Run: {i + 1} Cycle: {eq_cycle_count} Current SOH: {current_soh:.4f}', end='\r',flush=True)

                # Break the loop if the terminal SOH is reached
                if current_soh < terminal_SOH:
                    Q_values = np.array(Q_values)
                    # total_soh_values[i] = Q_values  # Store SOH values for the current run
                    total_eqcycle_values = np.append(total_eqcycle_values, eq_cycle_count)  # Store equivalent cycle count for the current run

                    max_len = max(max_len, len(Q_values))   # remember the tallest column
                    soh_columns.append(Q_values)            # keep raw list for now
                    print(f"Run {i + 1} completed with SOH: {current_soh:.4f} and equivalent cycles: {eq_cycle_count}")
                    break

    # pad every run up to max_len
    soh_columns_padded = [
        np.pad(q, (0, max_len - len(q)), constant_values=np.nan)
        for q in soh_columns
    ]

    total_soh_values = pd.DataFrame({
        run_idx + 1: col / battery_model.parameters["Qmax"]
        for run_idx, col in enumerate(soh_columns_padded)
    })

    # Get the mean and standard deviation of the SOH values
    SOH_df = total_soh_values.iloc[:, :MC_runs].copy()  # Select only the columns from 1 to N (number of simulations)
    SOH_df['mean'] = SOH_df.mean(axis=1)
    SOH_df['std'] = SOH_df.std(axis=1)


    total_cycles = np.mean(total_eqcycle_values)

    return total_cycles, SOH_df['mean'], SOH_df['std']
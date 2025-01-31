import simpy
import math
import random
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


# Configurar la semilla para reproducibilidad
SEED = 3
random_generators = {
    'cleaning_and_inspection': random.Random(SEED),
    'component_cleaning': random.Random(SEED + 1),
    'component_inspection': random.Random(SEED + 2),
    'component_repair': random.Random(SEED + 3),
    'finished_product_inspection': random.Random(SEED + 4),
    'demand_arrival': random.Random(SEED + 5),
    'cores_arrival': random.Random(SEED + 6),
}

# Simulation parameters
simulation_time = 80640  # Total simulation time: 8 weeks in minutes
warmup_period = 2520   # Warmup period
monitoring_interval = 1
include_stacked_chart_diagram_for_good_quality_components = 'yes'
replenish_buffers = 'yes'
include_arrival_variability = 'no'
include_demand_variability  = 'no'
discard_at_cleaning_and_inspection = 'yes'


# Parameters to be modified by students
process_parameters = {
    'demand': {
        'interval': 5760,  # Average time between demand arrivals (subject to variability)
        'variability': 0.1,  # Variability factor for demand interval (0 = no variability)
        'quantity_min': 18,  # Minimum demand quantity
        'quantity_max': 20   # Maximum demand quantity
    },
    'cores_arrival': {
        'interval': 1440,  # Interval at which cores arrive
        'variability': 0,
        'batch_size_min': 6,  
        'batch_size_max': 6 # Number of cores arriving each time
    },
    
    'cleaning_and_inspection': {
        'batch_size': 1,  # Number of parts cleaned and inspected in a batch
        'capacity': 1,  # Number of cleaning and inspection machines available
        'quality_thresholds': { 
            'Low': 40,  
            'Medium': 60  
        },
        'process_times': {
            'Low': 30,
            'Medium': 24,
            'High': 20
        }
    },
     'bill_of_materials': {  # Components needed per product
        "Component_A": 2,
        "Component_B": 3,
        "Component_C": 1
    },
    
    'disassembly': {
        'batch_size': 1,  # Number of parts disassembled in a batch
        'process_time': {'Low':450, 'Medium':375, 'High':300},  # Time to disassemble one core
        'capacity': 1,  # Number of disassembly machines available
    },
    
    'component_cleaning': {
        'batch_size': 1,  # Number of components cleaned in a batch
        'capacity': 2,  # Number of cleaning machines available
        'quality_thresholds': { 
            'Low': 23,  # Up to 50% for High
            'Medium': 47  # Up to 80% for Medium, above is Low
        },
        'process_times': {  # Cleaning times by component and quality
            'Component_A': {'Low': 33, 'Medium': 30, 'High': 27},
            'Component_B': {'Low': 35, 'Medium': 25, 'High': 15},
            'Component_C': {'Low': 57, 'Medium': 45, 'High': 33}
        }
    },

    'component_inspection': {
        'batch_size': {'Component_A':1, 'Component_B':1,'Component_C':1},  # Number of components repaired in a batch
        'capacity': 1,  # Number of inspection machines available
        'quality_thresholds': { 
            'Component_A': {
                'Low': {'Low': 80, 'Medium': 90},
                'Medium': {'Low': 40, 'Medium':60},
                'High': {'Low': 10,'Medium': 30}
            },
            'Component_B': { 
                'Low': {'Low': 80, 'Medium': 95},
                'Medium': {'Low': 35,'Medium': 65},
                'High': {'Low': 5, 'Medium': 25}
            },
            'Component_C': { 
                'Low': {'Low': 90, 'Medium': 95},
                'Medium': {'Low': 40, 'Medium': 55},
                'High': {'Low': 20, 'Medium': 30}
            }
        },
        'process_times': {  # Inspection times by quality
            'Component_A': {'Low': 23, 'Medium': 20, 'High': 17},
            'Component_B': {'Low': 21, 'Medium': 20, 'High': 19},
            'Component_C': {'Low': 10, 'Medium': 8, 'High': 7}
        }
    },

    'component_repair': {
        'capacity': 1,  # Number of repair stations available
        'quality_thresholds': { 
            'Component_A': {
                'Low': {'Low': 80, 'Medium': 90},
                'Medium': {'Low': 40, 'Medium':60},
                'High': {'Low': 10,'Medium': 30}
            },
            'Component_B': { 
                'Low': {'Low': 80, 'Medium': 90},
                'Medium': {'Low': 40, 'Medium':60},
                'High': {'Low': 10,'Medium': 30}
            },
            'Component_C': { 
                'Low': {'Low': 80, 'Medium': 90},
                'Medium': {'Low': 40, 'Medium':60},
                'High': {'Low': 10,'Medium': 30}
            }
        },
        'easiness_to_repair_thresholds': {
            'Component_A': {
                'Low': 20,  # Up to 50% for High
                'Medium': 80  # Up to 80% for Medium, above is Low
            },
            'Component_B': { 
                'Low': 15,  # Up to 60% for High
                'Medium': 75  # Up to 85% for Medium, above is Low
            },
            'Component_C': { 
                'Low': 30,  # Up to 40% for High
                'Medium': 70  # Up to 70% for Medium, above is Low
            }
        },
        'process_times': {  # Repair times by component type and easiness to repair, high means easy to repair.
            'Component_A': {'Low': 1200, 'Medium': 1000, 'High': 760},
            'Component_B': {'Low': 1300, 'Medium': 1050, 'High': 900},
            'Component_C': { 'Low': 1600, 'Medium': 1200, 'High': 960}
        },
        'max_repair_attempts': 1 # Maximum number of repair attempts
    },
    
    'assembly': {
        'batch_size': 1,
        'process_time': 210,  # Time to assemble one product
        'capacity': 1
    },

    'finished_product_inspection': {
        'capacity': 1,  # Number of inspection stations
        'quality_thresholds': {
            'Low': 0.5,  # Up to 50% for High
            'Medium': 1.5  # Up to 80% for Medium, above is Low
        },
        'process_time': 30  # Fixed time for inspection
    },
    
    'replenishment': {
        'component_types': ['Component_A', 'Component_B', 'Component_C'],
        'thresholds': {  # Umbrales para cada componente
            'Component_A': 2,
            'Component_B': 3,
            'Component_C': 1
        },
        'replenishment_batch': {  # Tamaño del lote de reposición para cada componente
            'Component_A': 1,
            'Component_B': 3,
            'Component_C': 1
        },
        'interval': 0  # Intervalo de revisión en unidades de tiempo
    }
}

# Costs
component_adquisition = 4
core_adquisition = 30
cost_per_delay = 100
operational_cost_per_hour = 50
prize = 6000

# KPIs
total_requests = 0
fulfilled_requests = 0
delayed_requests = 0
cumulative_delay_time = 0
cumulative_work_hours = 0
core_adquisition_cost = 0
income = 0
last_request_time=0
buyed_components_cost = 0
cont=0

# Buffers and queues
arrival_buffer_capacity = 500
cleaned_buffer_capacity = 500
discarded_cores_buffer_capacity = 500
components_buffer_capacity = 500
cleaned_components_buffer_capacity = 500
good_quality_components_buffer_capacity = 500
to_be_repaired_components_buffer_capacity = 500
discarded_components_buffer_capacity = 500
finished_products_buffer_capacity = 500
inspected_finished_products_buffer_capacity = 500
discarded_products_buffer_capacity = 500


delayed_request_times = []  # Track timestamps of delayed requests


# Monitoring data

buffer_log = []


# Utility functions
def log_debug(message):
    if DEBUG:
        print(message)

# Initialize the dictionary at the start of the script
quality_random_by_process = {
    'demand_arrival':[],
    'cores_arrival':[],
    'cleaning_and_inspection': [],
    'component_cleaning': [],
    'component_inspection': [],
    'component_repair': [],
    'finished_product_inspection': []
}




def assign_quality(quality_thresholds, process_name):

    global quality_random_by_process
    
    quality_random = random_generators[process_name].uniform(0, 100)
    #quality_random_by_process[process_name].append(quality_random)
    
    if quality_random <= quality_thresholds['Low']:
        return "Low"
    elif quality_random <= quality_thresholds['Medium']:
        return "Medium"
    else:
        return "High"
    #log_debug(f"[DEBUG] Assigned quality: {quality}")
    return quality_random



# Processes
def demand_arrival(env, inspected_finished_products_buffer):
    global total_requests, fulfilled_requests, delayed_requests, cumulative_delay_time, income, cont
    params = process_parameters['demand']
    if env.now < warmup_period:
        yield env.timeout(warmup_period - env.now)
    
    while True:
        if include_demand_variability =='yes':
            interval = random_generators['demand_arrival'].uniform(
                params['interval'] * (1 - params['variability']),
                params['interval'] * (1 + params['variability'])
            )
            demand_quantity = random_generators['demand_arrival'].randint(
                params['quantity_min'],
                params['quantity_max']
            )
        else:
            interval = params['interval']
            demand_quantity = params['quantity_min']
        yield env.timeout(interval)
        
        total_requests += demand_quantity
        #print(cont, demand_quantity, total_requests)
        #log_debug(f"[DEBUG] Time {env.now}: Demand arrival of {demand_quantity} units. Inspected_finished_products_buffer buffer level: {len(inspected_finished_products_buffer.items)}")

        if len(inspected_finished_products_buffer.items) >= demand_quantity:
            for _ in range(demand_quantity):
                yield inspected_finished_products_buffer.get()  # Retrieve one item at a time
            fulfilled_requests += demand_quantity
            income =  fulfilled_requests * prize
            #log_debug(f"[DEBUG] Time {env.now}: {demand_quantity} units shipped. Remaining cleaned buffer level: {len(cleaned_buffer.items)}")
        else:
            delayed_requests += demand_quantity
            delayed_request_times.extend([env.now] * demand_quantity)
            #log_debug(f"[DEBUG] Time {env.now}: Insufficient stock. {demand_quantity} units delayed. inspected_finished_products_buffer: {len(inspected_finished_products_buffer.items)}")
            
            while len(inspected_finished_products_buffer.items) < demand_quantity:
                yield env.timeout(1)
            
            for _ in range(demand_quantity):
                yield inspected_finished_products_buffer.get()  # Retrieve one item at a time
            fulfillment_time = env.now
            for _ in range(demand_quantity):
                delay_time = fulfillment_time - delayed_request_times.pop(0)
                cumulative_delay_time += delay_time
            #log_debug(f"[DEBUG] Time {env.now}: LATE SHIPPING: {demand_quantity} units shipped. Remaining inspected_finished_products_buffer: {len(inspected_finished_products_buffer.items)}")



def update_monitoring_data(env, monitoring_data, 
                           arrival_buffer, cleaned_buffer, discarded_cores_buffer, 
                           components_buffer, cleaned_components_buffer, 
                           good_quality_components_buffer, to_be_repaired_components_buffer, 
                           discarded_components_buffer, finished_products_buffer, 
                           inspected_finished_products_buffer, discarded_products_buffer):
    #print(f"update_monitoring_data called at time {env.now}")
    monitoring_data['time'].append(env.now)
    monitoring_data['arrival_buffer_level'].append(len(arrival_buffer.items))
    monitoring_data['cleaned_buffer_level'].append(len(cleaned_buffer.items))
    monitoring_data['discarded_cores_buffer_level'].append(len(discarded_cores_buffer.items))
    monitoring_data['components_buffer_level'].append(len(components_buffer.items))  # Use len() for Store
    monitoring_data['cleaned_components_buffer_level'].append(len(cleaned_components_buffer.items))  # Use len() for Store
    monitoring_data['good_quality_components_buffer_level'].append(len(good_quality_components_buffer.items))  # Use len() for Store
    monitoring_data['to_be_repaired_components_buffer_level'].append(len(to_be_repaired_components_buffer.items))  # Use len() for Store
    monitoring_data['discarded_components_buffer_level'].append(len(discarded_components_buffer.items))  # Use len() for Store
    monitoring_data['finished_products_buffer_level'].append(len(finished_products_buffer.items))  # Use len() for Store
    monitoring_data['inspected_finished_products_buffer_level'].append(len(inspected_finished_products_buffer.items))  # Use len() for Store
    monitoring_data['discarded_products_buffer_level'].append(len(discarded_products_buffer.items))  # Use len() for Store
    monitoring_data['fulfilled_requests'].append(fulfilled_requests)
    monitoring_data['delayed_requests'].append(delayed_requests)

    # Log buffer states
    log_buffer_state(simulation_time, 'arrival_buffer', arrival_buffer.items)
    log_buffer_state(simulation_time, 'cleaned_buffer', cleaned_buffer.items)
    log_buffer_state(simulation_time, 'discarded_cores_buffer', discarded_cores_buffer.items)
    log_buffer_state(simulation_time, 'components_buffer', components_buffer.items)
    log_buffer_state(simulation_time, 'cleaned_components_buffer', cleaned_components_buffer.items)
    log_buffer_state(simulation_time, 'good_quality_components_buffer', good_quality_components_buffer.items)
    log_buffer_state(simulation_time, 'to_be_repaired_components_buffer', to_be_repaired_components_buffer.items)
    log_buffer_state(simulation_time, 'discarded_components_buffer', discarded_components_buffer.items)
    log_buffer_state(simulation_time, 'finished_products_buffer', finished_products_buffer.items)
    log_buffer_state(simulation_time, 'inspected_finished_products_buffer', inspected_finished_products_buffer.items)
    log_buffer_state(simulation_time, 'discarded_products_buffer', discarded_products_buffer.items)

    

    if include_stacked_chart_diagram_for_good_quality_components == 'yes':
         # Stacked levels for good quality components
        component_types = ["Component_A", "Component_B", "Component_C"]
        good_quality_stacked = {component: 0 for component in component_types}
        discarded_stacked = {component: 0 for component in component_types}
    
        # Update stacked levels for good quality components
        for item in good_quality_components_buffer.items:
            component_type = item['type']
            if component_type in good_quality_stacked:
                good_quality_stacked[component_type] += 1
    
        for component in component_types:
            key = f'good_quality_{component.lower()}_buffer_level'
            if key not in monitoring_data:
                monitoring_data[key] = []
            monitoring_data[key].append(good_quality_stacked[component])
    
        # Update stacked levels for discarded components
        for item in discarded_components_buffer.items:
            component_type = item['type']
            if component_type in discarded_stacked:
                discarded_stacked[component_type] += 1
    
        for component in component_types:
            key = f'discarded_{component.lower()}_buffer_level'
            if key not in monitoring_data:
                monitoring_data[key] = []
            monitoring_data[key].append(discarded_stacked[component])



def log_buffer_state(time, buffer_name, buffer_content):
    buffer_types = {}
    total_count = 0
    has_type = any('type' in item for item in buffer_content)  # Check if items have 'type'

    if has_type:
        # Process items with a 'type'
        for item in buffer_content:
            item_type = item.get('type', 'Unknown')  # Use 'Unknown' if 'type' is missing
            buffer_types[item_type] = buffer_types.get(item_type, 0) + 1
            total_count += 1

        # Log counts by type
        for item_type, count in buffer_types.items():
            log_entry = {'time': time, 'buffer': buffer_name, 'type': item_type, 'count': count}
            buffer_log.append(log_entry)
            #print("Logged entry with type:", log_entry)  # Debugging output

    else:
        # Handle buffers without types
        total_count = len(buffer_content)  # Just count items in the buffer

    # Log aggregate count for the buffer
    aggregate_log_entry = {'time': time, 'buffer': buffer_name, 'type': 'All', 'count': total_count}
    buffer_log.append(aggregate_log_entry)
    #print("Logged aggregate entry:", aggregate_log_entry)


def periodic_monitoring(env, 
                        arrival_buffer, 
                        cleaned_buffer, 
                        discarded_cores_buffer, 
                        components_buffer, 
                        cleaned_components_buffer, 
                        good_quality_components_buffer, 
                        to_be_repaired_components_buffer, 
                        discarded_components_buffer, 
                        finished_products_buffer, 
                        inspected_finished_products_buffer, 
                        discarded_products_buffer, 
                        monitoring_data):
    while True:
        # Monitor the state of each buffer
        #print(f"periodic_monitoring running at time {env.now}")
        update_monitoring_data(env, monitoring_data, 
                               arrival_buffer, cleaned_buffer, discarded_cores_buffer, 
                               components_buffer, cleaned_components_buffer, 
                               good_quality_components_buffer, to_be_repaired_components_buffer, 
                               discarded_components_buffer, finished_products_buffer, 
                               inspected_finished_products_buffer, discarded_products_buffer)
        
        # Pause for the monitoring interval
        yield env.timeout(1)  # Adjust this to your desired interval


def cores_arrival(env, arrival_buffer):
    global core_adquisition_cost
    
    params = process_parameters['cores_arrival']
    while True:
        if include_arrival_variability == 'yes':                   
            arrival_interval = random_generators['cores_arrival'].uniform(
                params['interval'] * (1 - params['variability']),
                params['interval'] * (1 + params['variability'])
            )
            batch_size = random_generators['cores_arrival'].randint(
                params['batch_size_min'],
                params['batch_size_max']
            )
        else:
            arrival_interval = params['interval']
            batch_size=math.floor((params['batch_size_min']+params['batch_size_max'])/2)
        yield env.timeout(arrival_interval)
        # Add cores as individual items to the buffer
        batch = [{'core_id': i} for i in range(batch_size)]  # Create batch as a list of items
        for core in batch:
            arrival_buffer.put(core)  # Add each core individually
            core_adquisition_cost += core_adquisition
        #log_debug(f"[DEBUG] Time {env.now}: Added {params['batch_size']} cores to arrival buffer. Current cores level: {len(arrival_buffer.items)}")

def cleaning_and_inspection(env, arrival_buffer, cleaned_buffer, discarded_cores_buffer, resource):
    params = process_parameters['cleaning_and_inspection']
    global cumulative_work_hours
    while True:
        with resource.request() as request:
            yield request
            if len(arrival_buffer.items) >= params['batch_size']:
                #Log the state of the arrival buffer
                #log_debug(f"[DEBUG] Time {env.now}: Arrival buffer level before taking batch: {len(arrival_buffer.items)}.")
                
                # Collect a batch of items from the arrival buffer
                batch = []
                for _ in range(params['batch_size']):
                    item = yield arrival_buffer.get()
                    # Ensure item is a dictionary; if not, create one
                    if not isinstance(item, dict):
                        item = {'cores_general_condition': None}
                    batch.append(item)

                #Log the state after taking the batch
                #log_debug(f"[DEBUG] Time {env.now}: Arrival buffer level after taking batch: {len(arrival_buffer.items)}.")

                # Assign quality and determine process time for each item
                for item in batch:
                    item['cores_general_condition'] = assign_quality(params['quality_thresholds'], 'cleaning_and_inspection')
                
                process_times = [params['process_times'][item['cores_general_condition']] for item in batch]
                max_process_time = max(process_times)

                #log_debug(f"[DEBUG] Time {env.now}: Batch taken for cleaning with qualities {[item['cores_general_condition'] for item in batch]} and max process time {max_process_time}.")
                
                yield env.timeout(max_process_time)
                cumulative_work_hours += (max_process_time/60)

                # Add cleaned items to the cleaned buffer
                for item in batch:
                    if item['cores_general_condition']=='Low' and discard_at_cleaning_and_inspection == 'yes':
                        discarded_cores_buffer.put(item)
                        #print(f"Condición general del core: {item['cores_general_condition']}, Descarte en la fase limpieza e inspección: {discard_at_cleaning_and_inspection}, Buffer de componentes limpios: {len(cleaned_buffer.items)}, Buffer de componentes desechados: {len(discarded_cores_buffer.items)}")
                    else:
                        cleaned_buffer.put(item)
                        #print(f"Condición general del core: {item['cores_general_condition']}, Descarte en la fase limpieza e inspección: {discard_at_cleaning_and_inspection}, Buffer de componentes limpios: {len(cleaned_buffer.items)}, Buffer de componentes desechados: {len(discarded_cores_buffer.items)}")

                #log_debug(f"[DEBUG] Time {env.now}: Batch added to cleaned buffer. Cleaned buffer level: {len(cleaned_buffer.items)}.")
            else:
                #log_debug(f"[DEBUG] Time {env.now}: Not enough parts in arrival buffer for a batch. Arrival buffer level: {len(arrival_buffer.items)}. Waiting...")
                yield env.timeout(1)



def disassembly(env, cleaned_buffer, components_buffer, resource):
    params = process_parameters['disassembly']  # Retrieve process parameters
    bom = process_parameters['bill_of_materials']
    global cumulative_work_hours
    while True:
        with resource.request() as request:
            yield request
            if len(cleaned_buffer.items) >= params['batch_size']:
                # Collect the batch using a loop
                batch = []
                for _ in range(params['batch_size']):
                    core_data = yield cleaned_buffer.get()
                    batch.append(core_data)

                # Extract qualities and determine the maximum process time
                cores_general_conditions = [core_data['cores_general_condition'] for core_data in batch]  # Extract qualities
                process_times = [params['process_time'][cores_general_condition] for cores_general_condition in cores_general_conditions]  # Get process times
                max_process_time = max(process_times)  # Take the longest process time

                #log_debug(f"[DEBUG] Time {env.now}: Disassembling a batch with qualities {qualities}. Max process time: {max_process_time}.")
                yield env.timeout(max_process_time)
                cumulative_work_hours += (max_process_time/60)

                # Add components to the components buffer based on the bill of materials
                for core_data in batch:
                    for component, quantity in bom.items():
                        for _ in range(quantity):
                            components_buffer.put({'type': component, 'quantity': 1})
                            #log_debug(f"[DEBUG] Time {env.now}: Added 1 of {component} to components buffer. Buffer updated.")
            else:
                yield env.timeout(1)



def component_cleaning(env, components_buffer, cleaned_components_buffer, resource):
    params = process_parameters['component_cleaning']
    quality_thresholds = params['quality_thresholds']
    global cumulative_work_hours
    while True:
        with resource.request() as request:
            yield request
            if len(components_buffer.items) >= params['batch_size']:
                # Collect the batch
                batch = []
                for _ in range(params['batch_size']):
                    component_data = yield components_buffer.get()
                    #log_debug(f"[DEBUG] Time {env.now}: Number of parts in the components buffer: {len(components_buffer.items)}.")
                    batch.append(component_data)
                
                # Extract process times for all components in the batch
                process_times = []
                for component_data in batch:
                    component = component_data['type']
                    component_general_condition = assign_quality(quality_thresholds, 'component_cleaning')
                    component_data['component_general_condition'] = component_general_condition
                    process_time = params['process_times'][component][component_general_condition]
                    process_times.append(process_time)
                    #log_debug(f"[DEBUG] Time {env.now}: Cleaning {component} with quality '{quality}' (process time {process_time}).")
                
                # Determine the longest process time
                max_process_time = max(process_times)
                #log_debug(f"[DEBUG] Time {env.now}: Batch cleaning will take {max_process_time}.")
                yield env.timeout(max_process_time)
                cumulative_work_hours += (max_process_time/60)

                # Add cleaned items to the cleaned_components_buffer
                for component_data in batch:
                    cleaned_components_buffer.put(component_data)
                    #log_debug(f"[DEBUG] Time {env.now}: Cleaned {component_data['type']}. Cleaned components buffer updated.")
                    #log_debug(f"[DEBUG] Time {env.now}: Number of parts in the cleaned components buffer: {len(cleaned_components_buffer.items)}.")
            else:
                #log_debug(f"[DEBUG] Time {env.now}: Not enough parts in the components buffer for a batch. Waiting...")
                yield env.timeout(1)


def component_inspection(env, cleaned_components_buffer, good_quality_components_buffer, to_be_repaired_components_buffer, discarded_components_buffer, resource):
    params = process_parameters['component_inspection']
    global cumulative_work_hours

    while True:
        with resource.request() as request:
            yield request

            # Check if there are enough components for a batch
            batch_ready = False
            while not batch_ready:
                component_counts = {}
                for component_data in cleaned_components_buffer.items:
                    component_type = component_data['type']
                    component_general_condition = component_data['component_general_condition']
                    component_counts[component_type] = component_counts.get(component_type, 0) + 1

                # Check if any component type meets the batch size requirement
                for component_type, count in component_counts.items():
                    if count >= params['batch_size'][component_type]:
                        batch_ready = True
                        selected_type = component_type
                        break

                if not batch_ready:
                    #log_debug(f"[DEBUG] Time {env.now}: Not enough components for a batch. Cleaned components buffer level: {len(cleaned_components_buffer.items)}. Waiting...")
                    yield env.timeout(1)

            # Collect the batch
            batch = []
            #log_debug(f"[DEBUG] Time {env.now}: Collecting batch of type '{selected_type}'. Initial cleaned components buffer level: {len(cleaned_components_buffer.items)}.")
            while len(batch) < params['batch_size'][selected_type]:
                for idx, component_data in enumerate(cleaned_components_buffer.items):
                    if component_data['type'] == selected_type:
                        component = yield cleaned_components_buffer.get()
                        batch.append(component)
                        #log_debug(f"[DEBUG] Time {env.now}: Taken 1 component of type '{selected_type}' from cleaned components buffer. Current level: {len(cleaned_components_buffer.items)}.")
                        if len(batch) == params['batch_size'][selected_type]:
                            break

            #log_debug(f"[DEBUG] Time {env.now}: Batch of {len(batch)} components of type '{selected_type}' collected for inspection. Cleaned components buffer level after batch collection: {len(cleaned_components_buffer.items)}.")

            # Process the batch
            component_general_conditions = [component_general_condition for core_data in batch]
            #qualities = [assign_quality(params['quality_thresholds'][component_type]) for _ in batch]
            process_times = [params['process_times'][selected_type][component_general_condition] for component_general_condition in component_general_conditions]
            max_process_time = max(process_times)
            #log_debug(f"[DEBUG] Time {env.now}: Batch inspection will take {max_process_time} units of time.")
            yield env.timeout(max_process_time)
            cumulative_work_hours += (max_process_time)/60
            component_qualities = [assign_quality(params['quality_thresholds'][component_type][component_general_condition],'component_inspection') for _ in batch]


            # Assign components to their final buffers
            for idx, component_data in enumerate(batch):
                component_quality = component_qualities[idx]
                if component_quality == "High":
                    buffer = good_quality_components_buffer
                elif component_quality == "Medium":
                    buffer = to_be_repaired_components_buffer
                else:
                    buffer = discarded_components_buffer

                buffer.put({'type': selected_type, 'quantity': 1})
                #log_debug(f"[DEBUG] Time {env.now}: Moved 1 component of type '{selected_type}' with quality '{quality}' to the appropriate buffer.")
                #log_debug(f"[DEBUG] Time {env.now}: Buffer levels -> High: {len(good_quality_components_buffer.items)}, Medium: {len(to_be_repaired_components_buffer.items)}, Low: {len(discarded_components_buffer.items)}.")

            #log_debug(f"[DEBUG] Time {env.now}: Cleaned components buffer level after processing: {len(cleaned_components_buffer.items)}.")




def component_repair(env, to_be_repaired_components_buffer, good_quality_components_buffer, discarded_components_buffer, resource, resource_id):
    params = process_parameters['component_repair']  # Acceder a los parámetros actualizados
    max_attempts = params['max_repair_attempts']  # Máximo número de intentos
    global cumulative_work_hours

    while True:
        with resource.request() as request:
            yield request  # Solicitar el recurso específico

            # Depuración: Niveles de buffers antes del proceso
            #log_debug(f"[DEBUG] Time {env.now}: Starting repair process on resource {resource_id}.")
            #log_debug(f"[DEBUG] Time {env.now}: Pre-process buffer levels -> To Be Repaired: {len(to_be_repaired_components_buffer.items)}, Good Quality: {len(good_quality_components_buffer.items)}, Discarded: {len(discarded_components_buffer.items)}.")

            # Revisar si hay componentes en el buffer
            if len(to_be_repaired_components_buffer.items) > 0:
                # Obtener un componente del buffer
                component_data = yield to_be_repaired_components_buffer.get()
                component_type = component_data['type']
                repair_attempts = component_data.get('repair_attempts', 0) + 1

                #log_debug(f"[DEBUG] Time {env.now}: Resource {resource_id} repairing '{component_type}' (Attempt {repair_attempts}/{max_attempts}).")

                # Calcular tiempo de reparación
                easiness_to_repair = assign_quality(params['easiness_to_repair_thresholds'][component_type], 'component_repair')

                process_time = params['process_times'][component_type][easiness_to_repair]
                #process_time = params['process_times'].get(component_type, {}).get(easiness_to_repair, 0)
                #st.write(f"Tiempo de proceso para {component_type} con {easiness_to_repair}: {process_time}")

                yield env.timeout(process_time)
                cumulative_work_hours += process_time / 60

                # Determinar calidad final
                #st.write("Contenido de params['quality_thresholds']:", params['quality_thresholds'])
                #st.write("Contenido de component_type:", component_type)
                #st.write("Contenido de easiness_to_repair:", easiness_to_repair)
                #if component_type in params['quality_thresholds']:
                #    if easiness_to_repair in params['quality_thresholds'][component_type]:
                #        value = params['quality_thresholds'][component_type][easiness_to_repair]
                #        st.write(f"Valor obtenido para calidad: {value}")
                #    else:
                #        st.write(f"Error: '{easiness_to_repair}' no encontrado en '{component_type}'.")
                #else:
                #    st.write(f"Error: '{component_type}' no encontrado en quality_thresholds.")

                quality = assign_quality(params['quality_thresholds'][component_type][easiness_to_repair], 'component_repair')
                #log_debug(f"[DEBUG] Time {env.now}: Repair completed on resource {resource_id} for '{component_type}'. Final quality: '{quality}'.")

                # Determinar el buffer final
                if quality == "High":
                    buffer = good_quality_components_buffer
                elif repair_attempts >= max_attempts or quality == "Low":
                    buffer = discarded_components_buffer
                else:
                    buffer = to_be_repaired_components_buffer

                # Guardar el componente en el buffer final
                buffer.put({'type': component_type, 'quantity': 1, 'repair_attempts': repair_attempts})

                # Depuración: Niveles de buffers después del proceso
                #log_debug(f"[DEBUG] Time {env.now}: Post-process buffer levels -> To Be Repaired: {len(to_be_repaired_components_buffer.items)}, Good Quality: {len(good_quality_components_buffer.items)}, Discarded: {len(discarded_components_buffer.items)}.")
            else:
                yield env.timeout(1)



def assembly(env, good_quality_components_buffer, finished_products_buffer, assembly_resource):
    params = process_parameters['assembly']
    bom = process_parameters['bill_of_materials']  # Referencia al BOM
    replenishment_params = process_parameters['replenishment']  # Umbrales de reposición
    global cumulative_work_hours, last_request_time

    while True:
        with assembly_resource.request() as request:
            yield request

            # Depuración: Nivel inicial de buffers
            #log_debug(f"[DEBUG] Time {env.now}: Starting assembly process.")
            component_counts = {component: len([item for item in good_quality_components_buffer.items if item['type'] == component]) for component in process_parameters['bill_of_materials']}
            #log_debug(f"[DEBUG] Time {env.now}: Pre-process buffer levels -> Good Quality Components: {component_counts}, Finished Products: {len(finished_products_buffer.items)}.")

            # Verificar si hay suficientes componentes en el buffer
            if all(len([item for item in good_quality_components_buffer.items if item['type'] == component]) >= quantity
                   for component, quantity in bom.items()):

                # Depuración: Verificar si hay suficientes componentes
                #log_debug(f"[DEBUG] Time {env.now}: Enough components available for assembly.")
                #log_debug(f"[DEBUG] Time {env.now}: Components required: {bom}.")

                # Tomar componentes necesarios para ensamblar un producto
                for component, quantity in bom.items():
                    for _ in range(quantity):
                        component_data = next(item for item in good_quality_components_buffer.items if item['type'] == component)
                        good_quality_components_buffer.items.remove(component_data)
                        #log_debug(f"[DEBUG] Time {env.now}: Took one '{component}' from good_quality_components_buffer. Remaining: {len([item for item in good_quality_components_buffer.items if item['type'] == component])}.")

                # Verificar y activar reposición si es necesario
                time_since_last_request = env.now - last_request_time
                for component, threshold in replenishment_params['thresholds'].items():
                    current_level = sum(1 for item in good_quality_components_buffer.items if item['type'] == component)
                    #print(f" Current level{current_level}")
                    #print(f" Threshold{threshold}")
                    #print(f"Condition 1_ {current_level < threshold}")
                    #print(f"Time since last request {time_since_last_request}")
                    #print(f"Condition 2_ {env.now > warmup_period}")
                    #print(f"Condition 3_ {time_since_last_request > 1440}")
                    if (current_level < threshold and 
                        env.now > warmup_period and 
                        time_since_last_request > replenishment_params['interval']):  # Supongamos que X = 50 unidades de tiempo
                        #log_debug(f"[DEBUG] Time {env.now}: Replenishing '{component}' as its level {current_level} is below threshold {threshold}.")
                        env.process(replenish_good_quality_components(env, good_quality_components_buffer))
                        last_request_time = env.now
                        break  # Salir del bucle tras activar el proceso de reposición

                # Procesar el ensamblaje
                #log_debug(f"[DEBUG] Time {env.now}: Assembling product. Assembly time: {params['process_time']} units.")
                yield env.timeout(params['process_time'])
                cumulative_work_hours += (params['process_time'] / 60)

                # Añadir el producto ensamblado al buffer de productos terminados
                finished_products_buffer.put({'product': 'assembled_product'})
                #log_debug(f"[DEBUG] Time {env.now}: Product assembled and moved to finished_products_buffer.")
                #log_debug(f"[DEBUG] Time {env.now}: Product in the finished products buffer: {len(finished_products_buffer.items)}")

                # Depuración: Nivel de buffers después del ensamblaje
                #log_debug(f"[DEBUG] Time {env.now}: Post-process buffer levels -> Good Quality Components: {len(good_quality_components_buffer.items)}, Finished Products: {len(finished_products_buffer.items)}.")
            else:
                # Depuración: No hay suficientes componentes
                #log_debug(f"[DEBUG] Time {env.now}: Not enough components available for assembly. Waiting...")
                yield env.timeout(10)



def finished_product_inspection(env, finished_products_buffer, inspected_finished_products_buffer, discarded_products_buffer, resource):
    params = process_parameters['finished_product_inspection']
    global cumulative_work_hours


    while True:
        with resource.request() as request:
            yield request

            # Log the pre-process buffer levels
            #log_debug(f"[DEBUG] Time {env.now}: Finished products buffer level before inspection: {len(finished_products_buffer.items)}.")
            #log_debug(f"[DEBUG] Time {env.now}: Discarded products buffer level: {len(discarded_products_buffer.items)}.")

            # Check if there are parts in the finished products buffer
            if len(finished_products_buffer.items) > 0:
                product_data = yield finished_products_buffer.get()
                quality = assign_quality(params['quality_thresholds'], 'finished_product_inspection')
                process_time = params['process_time']

                #log_debug(f"[DEBUG] Time {env.now}: Inspecting finished product with quality '{quality}' (fixed process time: {process_time}).")

                # Perform the inspection
                yield env.timeout(process_time)
                cumulative_work_hours += (process_time/60)


                # Route the product based on quality
                if quality == "High":
                    inspected_finished_products_buffer.put(product_data)
                    #log_debug(f"[DEBUG] Time {env.now}: Moved finished product to inspected_finished_products_buffer. Level: {len(inspected_finished_products_buffer.items)}.")
                elif quality == "Medium":
                    discarded_products_buffer.put(product_data)
                    #log_debug(f"[DEBUG] Time {env.now}: Moved finished product to discarded_products_buffer. Level: {len(discarded_products_buffer.items)}.")
                else:  # quality == "Low"
                    discarded_products_buffer.put(product_data)
                    #log_debug(f"[DEBUG] Time {env.now}: Moved finished product to discarded_products_buffer. Level: {len(discarded_products_buffer.items)}.")
            else:
                #log_debug(f"[DEBUG] Time {env.now}: No finished products to inspect. Waiting...")
                yield env.timeout(1)

def replenish_good_quality_components(env, good_quality_components_buffer):
    global buyed_components_cost
    params = process_parameters['replenishment']
    component_types = params['component_types']
    thresholds = params['thresholds']
    replenishment_batch = params['replenishment_batch']
    #print(f"Time:{env.now}, empieza el replenishement")

    for component in thresholds:  # Iterate through all components in the thresholds
        current_count = len([x for x in good_quality_components_buffer.items if x['type'] == component])
        if current_count < thresholds[component]:
            # Execute logic when the specific component type is below the threshold
            #print(f"Replenishing {component} as it is below the threshold.")
            # Si el nivel está por debajo del umbral, reponer
            batch = [{'type': component, 'component_quality': 'High'} for _ in range(replenishment_batch[component])]
            yield env.timeout(params['interval'])
            for item in batch:
                #yield env.timeout(params['interval'])
                #log_debug(f"[DEBUG] Time {env.now}: Replenished {replenishment_batch[component]} units of '{component}' to good_quality_components_buffer. Current level: {replenishment_batch[component]}.")
                buyed_components_cost += component_adquisition
                good_quality_components_buffer.put(item)

                # Log del proceso de reposición
            #log_debug(f"[DEBUG] Time {env.now}: Replenished {replenishment_batch[component]} units of '{component}' to good_quality_components_buffer. Current level: {current_count}.")
       # yield env.timeout(params['interval']*10)  # Revisar los niveles a intervalos definidos


def plot_results(monitoring_data):
    times = monitoring_data['time']
    
    #Cores Buffers
    arrival_levels = monitoring_data['arrival_buffer_level']
    cleaned_levels = monitoring_data['cleaned_buffer_level']
    discarded_cores_levels = monitoring_data['discarded_cores_buffer_level']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    plt.plot(times, arrival_levels, label='Arrival Cores Buffer Level')
    plt.plot(times, cleaned_levels, label='Cleaned Cores Buffer Level')
    plt.plot(times, discarded_cores_levels, label='Discarded Cores Buffer Level')
    plt.xlabel('Time')
    plt.ylabel('Buffer Level')
    plt.title('Cores Buffer Levels Over Time')
    plt.legend()
    plt.grid(True)
    st.pyplot(fig)
    
    #Component Buffers
    components_levels = monitoring_data['components_buffer_level']
    cleaned_components_levels = monitoring_data['cleaned_components_buffer_level']
    good_quality_components_buffer_levels = monitoring_data['good_quality_components_buffer_level']
    to_be_repaired_components_buffer_levels = monitoring_data['to_be_repaired_components_buffer_level']
    discarded_components_buffer_levels = monitoring_data['discarded_components_buffer_level']

    fig, ax = plt.subplots(figsize=(10, 6))
    plt.plot(times, components_levels, label='Components Buffer Level')
    plt.plot(times, cleaned_components_levels, label='Cleaned Components Buffer Level')
    plt.plot(times, good_quality_components_buffer_levels, label='Good quality components Buffer Level')
    plt.plot(times, to_be_repaired_components_buffer_levels, label='To be repaired components Buffer Level')
    plt.plot(times, discarded_components_buffer_levels, label='Discarded components Buffer Level')
    plt.xlabel('Time')
    plt.ylabel('Buffer Level')
    plt.title('Buffer Levels Over Time')
    plt.legend()
    plt.grid(True)
    st.pyplot(fig)

    #Final product Buffer
    finished_products_levels = monitoring_data['finished_products_buffer_level']
    inspected_finished_products_levels = monitoring_data['inspected_finished_products_buffer_level']
    fig, ax = plt.subplots(figsize=(10, 6))
    plt.plot(times, finished_products_levels, label='Finished products Level')
    plt.plot(times, inspected_finished_products_levels, label='Inspected finished products Level')
    plt.xlabel('Time')
    plt.ylabel('Buffer Level')
    plt.title('Buffer Levels Over Time')
    plt.legend()
    plt.grid(True)
    st.pyplot(fig)

    #Service level plots
    fulfilled = monitoring_data['fulfilled_requests']
    delayed = monitoring_data['delayed_requests']

    fig, ax = plt.subplots(figsize=(10, 6))
    plt.plot(times, fulfilled, label='Fulfilled Requests', color='green')
    plt.plot(times, delayed, label='Delayed Requests', color='red')
    plt.xlabel('Time')
    plt.ylabel('Requests')
    plt.title('Fulfilled vs Delayed Requests Over Time')
    plt.legend()
    plt.grid(True)
    st.pyplot(fig)


def plot_stacked_chart(monitoring_data):
    times = monitoring_data['time']
    component_a_levels = monitoring_data.get('good_quality_component_a_buffer_level', [])
    component_b_levels = monitoring_data.get('good_quality_component_b_buffer_level', [])
    component_c_levels = monitoring_data.get('good_quality_component_c_buffer_level', [])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    plt.stackplot(times, component_a_levels, component_b_levels, component_c_levels, labels=["Component A", "Component B", "Component C"])
    plt.xlabel('Time')
    plt.ylabel('Buffer Level')
    plt.title('Good Quality Components Buffer Levels (Stacked)')
    plt.legend(loc='upper left')
    plt.grid(True)
    st.pyplot(fig)

def plot_discarded_components_stacked_chart(monitoring_data):
    times = monitoring_data['time']
    component_a_levels = monitoring_data.get('discarded_component_a_buffer_level', [])
    component_b_levels = monitoring_data.get('discarded_component_b_buffer_level', [])
    component_c_levels = monitoring_data.get('discarded_component_c_buffer_level', [])

    fig, ax = plt.subplots(figsize=(10, 6))
    plt.stackplot(times, component_a_levels, component_b_levels, component_c_levels, labels=["Component A", "Component B", "Component C"])
    plt.xlabel('Time')
    plt.ylabel('Buffer Level')
    plt.title('Discarded Components Buffer Levels (Stacked)')
    plt.legend(loc='upper left')
    plt.grid(True)
    st.pyplot(fig)


def run_simulation(simulation_time, process_parameters, generate_plots = False):
    #print("Contenido de process_parameters:", process_parameters.keys())
    # Validar que process_parameters contiene todas las claves necesarias
    required_keys = ['cleaning_and_inspection', 'disassembly', 'component_cleaning', 
                     'component_inspection', 'component_repair', 'assembly', 
                     'finished_product_inspection']
    missing_keys = [key for key in required_keys if key not in process_parameters]
    if missing_keys:
        raise KeyError(f"Faltan las siguientes claves en process_parameters: {missing_keys}")


    # Depuración: imprime los parámetros recibidos
   # print("Parametros recibidos en run_simulation:", process_parameters)

    
    # Crear el entorno de SimPy
    env = simpy.Environment()
    
    # Crear los buffers
    arrival_buffer = simpy.Store(env, capacity=process_parameters.get('arrival_buffer_capacity', 500))
    cleaned_buffer = simpy.Store(env, capacity=process_parameters.get('cleaned_buffer_capacity', 500))
    discarded_cores_buffer = simpy.Store(env, capacity=process_parameters.get('discarded_cores_buffer_capacity', 500))
    components_buffer = simpy.Store(env, capacity=process_parameters.get('components_buffer_capacity', 500))
    cleaned_components_buffer = simpy.Store(env, capacity=process_parameters.get('cleaned_components_buffer_capacity', 500))
    good_quality_components_buffer = simpy.Store(env, capacity=process_parameters.get('good_quality_components_buffer_capacity', 500))
    to_be_repaired_components_buffer = simpy.Store(env, capacity=process_parameters.get('to_be_repaired_components_buffer_capacity', 500))
    discarded_components_buffer = simpy.Store(env, capacity=process_parameters.get('discarded_components_buffer_capacity', 500))
    finished_products_buffer = simpy.Store(env, capacity=process_parameters.get('finished_products_buffer_capacity', 500))
    inspected_finished_products_buffer = simpy.Store(env, capacity=process_parameters.get('inspected_finished_products_buffer_capacity', 500))
    discarded_products_buffer = simpy.Store(env, capacity=process_parameters.get('discarded_products_buffer_capacity', 500))
   
    # Initialize monitoring data
    monitoring_data = {
        'time': [],
        'arrival_buffer_level': [],
        'cleaned_buffer_level': [],
        'discarded_cores_buffer_level': [],
        'components_buffer_level': [],
        'cleaned_components_buffer_level': [],
        'good_quality_components_buffer_level': [],
        'to_be_repaired_components_buffer_level': [],
        'discarded_components_buffer_level': [],
        'finished_products_buffer_level':[],
        'inspected_finished_products_buffer_level':[],
        'discarded_products_buffer_level': [],    
        'fulfilled_requests': [],
        'delayed_requests': []
    }

    # Crear los recursos
    cleaning_inspection_resource = simpy.Resource(env, capacity=process_parameters['cleaning_and_inspection']['capacity'])
    disassembly_resource = simpy.Resource(env, capacity=process_parameters['disassembly']['capacity'])
    component_cleaning_resource = simpy.Resource(env, capacity=process_parameters['component_cleaning']['capacity'])
    component_inspection_resource = simpy.Resource(env, capacity=process_parameters['component_inspection']['capacity'])
    component_repair_resources = [
        simpy.Resource(env, capacity=1) for _ in range(process_parameters['component_repair']['capacity'])
    ]
    assembly_resource = simpy.Resource(env, capacity=process_parameters['assembly']['capacity'])
    finished_product_inspection_resource = simpy.Resource(env, capacity=process_parameters['finished_product_inspection']['capacity'])

    # Iniciar procesos
    env.process(demand_arrival(env, inspected_finished_products_buffer))
    env.process(cores_arrival(env, arrival_buffer))
    env.process(cleaning_and_inspection(env, arrival_buffer, cleaned_buffer, discarded_cores_buffer, cleaning_inspection_resource))
    env.process(disassembly(env, cleaned_buffer, components_buffer, disassembly_resource))
    env.process(component_cleaning(env, components_buffer, cleaned_components_buffer, component_cleaning_resource))
    env.process(component_inspection(env, cleaned_components_buffer,
                                     good_quality_components_buffer,
                                     to_be_repaired_components_buffer,
                                     discarded_components_buffer,
                                     component_inspection_resource))

    # Proceso de reparación con múltiples recursos
    for resource_id, repair_resource in enumerate(component_repair_resources):
        env.process(component_repair(env, to_be_repaired_components_buffer,
                                     good_quality_components_buffer,
                                     discarded_components_buffer,
                                     repair_resource,
                                     resource_id))

    env.process(assembly(env, good_quality_components_buffer, finished_products_buffer, assembly_resource))
    env.process(finished_product_inspection(env, finished_products_buffer, inspected_finished_products_buffer,
                                            discarded_products_buffer, finished_product_inspection_resource))
    env.process(periodic_monitoring(
        env, arrival_buffer, cleaned_buffer, discarded_cores_buffer, 
        components_buffer, cleaned_components_buffer, 
        good_quality_components_buffer, to_be_repaired_components_buffer, 
        discarded_components_buffer, finished_products_buffer, 
        inspected_finished_products_buffer, discarded_products_buffer, 
        monitoring_data
    ))

    # Ejecutar la simulación
    env.run(until=simulation_time)

    # Calcular resultados
    mean_delay_time = cumulative_delay_time / delayed_requests if delayed_requests > 0 else 0
    mean_lead_time = simulation_time / total_requests if total_requests > 0 else 0
    total_cost = (
        delayed_requests * cost_per_delay +
        cumulative_work_hours * operational_cost_per_hour +
        core_adquisition_cost
    )

    # Generar gráficos y resúmenes si es necesario
    #if generate_plots:
    #    plot_results(monitoring_data)
    #    if include_stacked_chart_diagram_for_good_quality_components == 'yes':
    #        plot_stacked_chart(monitoring_data)
    #        plot_discarded_components_stacked_chart(monitoring_data)

    # Preparar resúmenes de buffers
    #print("Contents of buffer_log before creating buffer_df:", buffer_log[:5])  # Debugging

    #if not buffer_log:
        #print("buffer_log is empty. Skipping DataFrame creation.")
    #else:
       # buffer_df = pd.DataFrame(buffer_log)
        #print(buffer_df.head())  # Print the head of the DataFrame if it exists


    buffer_df = pd.DataFrame(buffer_log)
    buffer_summary_by_type = buffer_df.groupby(['buffer', 'type']).agg(
        mean_count=('count', 'mean'),
        min_count=('count', 'min'),
        max_count=('count', 'max')
    ).reset_index()
    buffer_summary_total = buffer_df[buffer_df['type'] == 'All'].groupby(['buffer']).agg(
        mean_count=('count', 'mean'),
        min_count=('count', 'min'),
        max_count=('count', 'max')
    ).reset_index()

    results = {
        "Total Requests": total_requests,
        "Fulfilled Requests": fulfilled_requests,
        "Delayed Requests": delayed_requests,
        "Mean Delay Time": mean_delay_time,
        "Mean Lead Time": mean_lead_time,
        "Total Cost": total_cost,
        "Total Income": income
    }

    return {
        "results": results,  # Aquí se deben almacenar los resultados principales
        "include_stacked_chart": include_stacked_chart_diagram_for_good_quality_components,
        "monitoring_data": monitoring_data,
        #"Total Requests": total_requests,
        #"Fulfilled Requests": fulfilled_requests,
        #"Delayed Requests": delayed_requests,
        #"Mean Delay Time": mean_delay_time,
        #"Mean Lead Time": mean_lead_time,
        #"Total Cost": total_cost,
        #"Total Income": income,
        "Buffer Summary By Type": buffer_summary_by_type,
        "Buffer Summary Total": buffer_summary_total
    }

#if __name__ == "__main__":
#    print("Validando run_simulation...")

    # Usa el process_parameters original definido antes
#    results = run_simulation(simulation_time=simulation_time, process_parameters=process_parameters, generate_plots=True)

#    print("Resultados de la simulación:", results)


# Simulation setup
#env = simpy.Environment()
#arrival_buffer = simpy.Store(env, capacity=arrival_buffer_capacity)
#cleaned_buffer = simpy.Store(env, capacity=cleaned_buffer_capacity)
#discarded_cores_buffer = simpy.Store(env, capacity=discarded_cores_buffer_capacity)
#components_buffer = simpy.Store(env, capacity=components_buffer_capacity)
#cleaned_components_buffer = simpy.Store(env, capacity=cleaned_components_buffer_capacity)
#good_quality_components_buffer = simpy.Store(env, capacity=good_quality_components_buffer_capacity)
#to_be_repaired_components_buffer = simpy.Store(env, capacity=to_be_repaired_components_buffer_capacity)
#discarded_components_buffer = simpy.Store(env, capacity=discarded_components_buffer_capacity)
#finished_products_buffer = simpy.Store(env, capacity=finished_products_buffer_capacity)
#inspected_finished_products_buffer = simpy.Store(env, capacity=inspected_finished_products_buffer_capacity)
#discarded_products_buffer = simpy.Store(env, capacity=discarded_products_buffer_capacity)



# Crear recursos independientes para cada proceso según su capacidad
#cleaning_inspection_resource = simpy.Resource(env, capacity=process_parameters['cleaning_and_inspection']['capacity'])
#disassembly_resource = simpy.Resource(env, capacity=process_parameters['disassembly']['capacity'])
#component_cleaning_resource = simpy.Resource(env, capacity=process_parameters['component_cleaning']['capacity'])
#component_inspection_resource = simpy.Resource(env, capacity=process_parameters['component_inspection']['capacity'])

# Crear múltiples recursos para el proceso de reparación según su capacidad
#component_repair_resources = [
#    simpy.Resource(env, capacity=1) for _ in range(process_parameters['component_repair']['capacity'])
#]

#assembly_resource = simpy.Resource(env, capacity=process_parameters['assembly']['capacity'])
#finished_product_inspection_resource = simpy.Resource(env, capacity=process_parameters['finished_product_inspection']['capacity'])


#nv.process(demand_arrival(env, inspected_finished_products_buffer))
#env.process(cores_arrival(env, arrival_buffer))
#env.process(cleaning_and_inspection(env, arrival_buffer, cleaned_buffer, discarded_cores_buffer, cleaning_inspection_resource))
#env.process(disassembly(env, cleaned_buffer, components_buffer, disassembly_resource))
#env.process(component_cleaning(env, components_buffer, cleaned_components_buffer, component_cleaning_resource))
#env.process(component_inspection(env, cleaned_components_buffer,
#                                  good_quality_components_buffer,
#                                  to_be_repaired_components_buffer,
#                                  discarded_components_buffer,
#                                  component_inspection_resource))

# Configuración del proceso de reparación con múltiples recursos
#for resource_id, repair_resource in enumerate(component_repair_resources):
#    env.process(component_repair(env, to_be_repaired_components_buffer,
#                                 good_quality_components_buffer,
#                                 discarded_components_buffer,
#                                 repair_resource,
#                                 resource_id))

#env.process(assembly(env, good_quality_components_buffer, finished_products_buffer, assembly_resource))
#env.process(finished_product_inspection(env, finished_products_buffer, inspected_finished_products_buffer, discarded_products_buffer, finished_product_inspection_resource))
#env.process(periodic_monitoring(env))



#env.run(until=simulation_time)

#mean_delay_time = cumulative_delay_time / delayed_requests if delayed_requests > 0 else 0
#mean_lead_time = simulation_time / total_requests if total_requests > 0 else 0
#total_cost = (delayed_requests * cost_per_delay) + (cumulative_work_hours*operational_cost_per_hour) + core_adquisition_cost + buyed_components_cost


#print("--- Simulation Results ---")
#print(f"Total Requests: {total_requests}")
#print(f"Fulfilled Requests: {fulfilled_requests}")
#print(f"Delayed Requests: {delayed_requests}")
#print(f"Mean Delay Time: {mean_delay_time:,.2f}")
#print(f"Mean Lead Time: {mean_lead_time:,.2f}")
#print(f"Total Cost: {total_cost:,.2f}")
#print(f"Total Income: {income:,.2f}")
#print(cont)

#plot_results()
#if include_stacked_chart_diagram_for_good_quality_components == 'yes':
#    plot_stacked_chart()
#    plot_discarded_components_stacked_chart()


#buffer_df = pd.DataFrame(buffer_log)

#buffer_summary_by_type = buffer_df.groupby(['buffer', 'type']).agg(
#    mean_count=('count', 'mean'),
#    min_count=('count', 'min'),
#    max_count=('count', 'max')
#).reset_index()
#print("Disaggregated Summary:")
#print(buffer_summary_by_type)


#buffer_summary_total = buffer_df[buffer_df['type'] == 'All'].groupby(['buffer']).agg(
#    mean_count=('count', 'mean'),
#    min_count=('count', 'min'),
#    max_count=('count', 'max')
#).reset_index()
#print("Total Summary:")
#print(buffer_summary_total)








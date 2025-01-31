import streamlit as st
import json
import pandas as pd
from modelo import run_simulation, process_parameters, include_stacked_chart_diagram_for_good_quality_components, plot_results, plot_stacked_chart, plot_discarded_components_stacked_chart

# Título
st.title("Remanufacturing Process Simulation")
st.markdown(
    """
    <p style="font-size:18px;">
    This application simulates a remanufacturing process seen in the figure below to evaluate key parameters such as cycle time and inventory levels. 
    It is part of the course <em>'Using Discrete Event Simulation for Decision-Making in Remanufacturing Systems'</em> 
    within the TFKnowNet framework. The simulation model is designed to allow participants to perform the exercises outlined 
    in the course.
    </p>
    """,
    unsafe_allow_html=True
)

st.image("Remanufacturing_Process.png", caption="Remanufacturing Process", use_column_width=True)


# Parámetros de configuración
st.sidebar.header("Simulation Configuration")

simulation_time_weeks = st.sidebar.number_input(
    "Total Simulation Time (Weeks)", 
    value=8,  # Valor predeterminado en semanas
    step=1,   # Incremento en semanas
    min_value=1
)
simulation_time = simulation_time_weeks * 7 * 24 * 60  # Convertir semanas a minutos

warmup_period_hours = st.sidebar.number_input(
    "Warm-up period (hours)", 
    value=42,  # Valor predeterminado en horas
    step=1,    # Incremento en horas
    min_value=0
)
warmup_period = warmup_period_hours * 60  # Convertir horas a minutos

monitoring_interval = st.sidebar.number_input("Monitoring Interval (min)", value=1, step=1)

include_stacked_chart_diagram_for_good_quality_components = st.sidebar.radio(
    "Show Buffer Graphs by Component",
    options=['yes', 'no'],
    index=0
)

replenish_buffers = st.sidebar.radio(
    "Replenish components buffers with new components",
    options=['yes', 'no'],
    index=0
)

include_arrival_variability = st.sidebar.radio(
    "Introducing randomness in core arrival intervals",
    options=['yes', 'no'],
    index=1,
    key="include_arrival_variability"
)

if include_arrival_variability == 'yes':
    st.sidebar.subheader("Core Arrival Parameters")
    cores_arrival_interval = st.sidebar.number_input(
        "Interval between core arrivals (min)",
        value=1440,
        step=60,
        min_value=0,
        key="cores_arrival_interval"
    )
    cores_arrival_variability = st.sidebar.slider(
        "Variability in core arrivals (%)",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.01,
        key="cores_arrival_variability"
    )
    cores_batch_size_min = st.sidebar.number_input(
        "Minimum core batch size",
        value=6,
        step=1,
        min_value=1,
        key="cores_batch_size_min"
    )
    cores_batch_size_max = st.sidebar.number_input(
        "Maximum core batch size",
        value=6,
        step=1,
        min_value=1,
        key="cores_batch_size_max"
    )
else:
    cores_arrival_interval = 1440  # Intervalo predeterminado
    cores_arrival_variability = 0.0  # Variabilidad predeterminada
    cores_batch_size_min = 6  # Tamaño mínimo de lote predeterminado
    cores_batch_size_max = 6  # Tamaño máximo de lote predeterminado



include_demand_variability = st.sidebar.radio(
    "Introducing randomness in demand intervals",
    options=['yes', 'no'],
    index=1
)

if include_demand_variability == 'yes':
    st.sidebar.header("Demand Parameters")
    demand_interval = st.sidebar.number_input(
        "Interval between demand arrivals (min)",
        min_value=0,
        value=5760,
        step=1
    )
    demand_variability = st.sidebar.slider(
        "Demand variability (%)",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.01
    )
    demand_quantity_min = st.sidebar.number_input(
        "Minimum demand quantity",
        min_value=1,
        value=18,
        step=1
    )
    demand_quantity_max = st.sidebar.number_input(
        "Maximum demand quantity",
        min_value=1,
        value=20,
        step=1
    )

else:
    demand_interval = 5760  # Intervalo predeterminado
    demand_variability = 0.0  # Variabilidad predeterminada
    demand_quantity_min = 18  # Tamaño mínimo de lote predeterminado
    demand_quantity_max = 20  # Tamaño máximo de lote predeterminado

discard_at_cleaning_and_inspection = st.sidebar.radio(
    "Allow removal of low-quality cores during the cleaning and inspection phase",
    options=['yes', 'no'],
    index=0
)

# Configuración de parámetros de demanda
#st.sidebar.subheader("Parámetros de Demanda")
#demand_interval = st.sidebar.number_input("Intervalo entre llegadas de demanda (min)", value=5760, step=60, min_value=0)
#demand_variability = st.sidebar.slider("Variabilidad de la demanda (%)", min_value=0.0, #max_value=1.0, value=0.1, step=0.01)
#demand_quantity_min = st.sidebar.number_input("Cantidad mínima de demanda", value=18, step=1, min_value=0)
#demand_quantity_max = st.sidebar.number_input("Cantidad máxima de demanda", value=20, step=1, min_value=0)

# Configuración de parámetros de llegada de núcleos
#st.sidebar.subheader("Parámetros de Llegada de Núcleos")
#cores_arrival_interval = st.sidebar.number_input("Intervalo de llegada de núcleos (min)", value=1440, step=60, min_value=0)
#cores_arrival_variability = st.sidebar.slider("Variabilidad en llegada de núcleos (%)", min_value=0.0, max_value=1.0, value=0.0, step=0.01)
#cores_batch_size_min = st.sidebar.number_input("Tamaño mínimo del lote de núcleos", value=6, step=1, min_value=1)
#cores_batch_size_max = st.sidebar.number_input("Tamaño máximo del lote de núcleos", value=6, step=1, min_value=1)

# Configuración de Quality Thresholds para Cleaning and Inspection

st.sidebar.header("Cores Quality after Cleaning and Inspection")

# Define columns for inputs
col1, col2, col3 = st.sidebar.columns(3)

with col1:
    core_cleaning_and_inspection_quality_low = st.number_input(
        "%Low", min_value=0, max_value=100, value=40, step=1, key="cores_low_quality"
    )

with col2:
    core_cleaning_and_inspection_quality_medium = st.number_input(
        "%Medium", min_value=0, max_value=100, value=20, step=1, key="cores_medium_quality"
    )

with col3:
    core_cleaning_and_inspection_quality_high = st.number_input(
        "%High", min_value=0, max_value=100, value=40, step=1, key="cores_high_quality"
    )

# Validation logic
cleaning_and_inspection_quality = (
    core_cleaning_and_inspection_quality_low +
    core_cleaning_and_inspection_quality_medium +
    core_cleaning_and_inspection_quality_high
)

if cleaning_and_inspection_quality != 100:
    st.sidebar.error(
        f"The total percentage must equal 100%. Currently, it is {cleaning_and_inspection_quality}%."
    )
    cleaning_quality_thresholds = None
else:
    cleaning_quality_thresholds = {
        "Low": core_cleaning_and_inspection_quality_low,
        "Medium": core_cleaning_and_inspection_quality_low + core_cleaning_and_inspection_quality_medium,  # Cumulative sum of Low + Medium
        "High": 100  # Always 100 cumulative
    }



#st.sidebar.header("Cores Quality after Cleaning and Inspection")

# Inputs del usuario
#core_cleaning_and_inspection_quality_low = st.sidebar.number_input("% Cores with Low quality", min_value=0, max_value=100, value=40, step=1)
#core_cleaning_and_inspection_quality_medium = st.sidebar.number_input("% Cores with Medium quality", min_value=0, max_value=100, value=20, step=1)
#core_cleaning_and_inspection_quality_high = st.sidebar.number_input("% Cores with High quality", min_value=0, max_value=100, value=40, step=1)

#cleaning_and_inspection_quality = core_cleaning_and_inspection_quality_low + core_cleaning_and_inspection_quality_medium + core_cleaning_and_inspection_quality_high

# Validar que no exceda el 100%
#if cleaning_and_inspection_quality != 100:
#    st.error(f"El total de los umbrales debe ser igual a 100%. Actualmente es {cleaning_and_inspection_quality}%.")
#    cleaning_quality_thresholds = None
#else:
#    cleaning_quality_thresholds = {
#        "Low": core_cleaning_and_inspection_quality_low,
#        "Medium": core_cleaning_and_inspection_quality_low + core_cleaning_and_inspection_quality_medium,  # Suma acumulativa de Low + Medium
#        "High": 100  # Siempre será 100 acumulativo
#    }

# Configuración de la capacidad de reparación
st.sidebar.header("Repair Capacity and Max Repair Attemps")
repair_capacity = st.sidebar.number_input(
    "Capaciy", 
    value=1,  # Valor predeterminado
    step=1, 
    min_value=1
)


# Maximo númerop de intentos de reparación
#st.sidebar.subheader("Intentos de Reparación")
max_repair_attempts = st.sidebar.number_input(
    "Repair Attemps", 
    value=1,  # Valor predeterminado
    step=1, 
    min_value=1
)

###################################################################################
#EASINESS TO REPAIR
###################################################################################

# Configuración de Facilidad de Reparación
#st.sidebar.header("Facilidad de Reparación")

#repair_easiness_thresholds = {}

#for component in components:
#    st.sidebar.subheader(component)
#    
#    repair_low = st.sidebar.number_input(
#        f"Facilidad Baja (Low) - {component}", min_value=0, max_value=100, value=30, step=1
#    )
#    repair_medium = st.sidebar.number_input(
#        f"Facilidad Media (Medium) - {component}", min_value=0, max_value=100, value=50, step=1
#    )
#    repair_high = st.sidebar.number_input(
#        f"Facilidad Alta (High) - {component}", min_value=0, max_value=100, value=20, step=1
#    )

    # Validación del total
#    total_easiness = repair_low + repair_medium + repair_high
#    if total_easiness != 100:
#        st.error(f"El total de las facilidades de reparación para {component} debe ser igual a 100%. Actualmente es {total_easiness}%.")
#        repair_easiness_thresholds[component] = None
#    else:
#        repair_easiness_thresholds[component] = {
#            "Low": repair_low,
#            "Medium": repair_low + repair_medium,
#            "High": 100  # Siempre acumulativo
#        }

# Configuración de Facilidad de Reparación
# Title for Easiness to Repair Section
st.sidebar.header("Easiness to Repair")

# Default values
default_easiness_to_repair_thresholds = {
    'Component_A': {'Low': 20, 'Medium': 60, 'High': 20},
    'Component_B': {'Low': 15, 'Medium': 60, 'High': 25},
    'Component_C': {'Low': 30, 'Medium': 40, 'High': 30}
}

# Initialize storage for user-defined values
repair_easiness_thresholds = {}

# Iterate over components
for component in default_easiness_to_repair_thresholds.keys():
    st.sidebar.markdown(
        f"<h3 style='margin-bottom: 2px; font-size: 16px;'>{component}</h3>",
        unsafe_allow_html=True
    )

    # Create input fields in columns
    cols = st.sidebar.columns(3)

    with cols[0]:
        repair_low = st.number_input(
            "% Low",
            min_value=0,
            max_value=100,
            value=default_easiness_to_repair_thresholds[component]['Low'],
            step=1,
            key=f"{component}_repair_low"
        )

    with cols[1]:
        repair_medium = st.number_input(
            "% Medium",
            min_value=0,
            max_value=100,
            value=default_easiness_to_repair_thresholds[component]['Medium'],
            step=1,
            key=f"{component}_repair_medium"
        )

    with cols[2]:
        repair_high = st.number_input(
            "% High",
            min_value=0,
            max_value=100,
            value=default_easiness_to_repair_thresholds[component]['High'],
            step=1,
            key=f"{component}_repair_high"
        )

    # Validate that the total is exactly 100%
    total_easiness = repair_low + repair_medium + repair_high
    if total_easiness != 100:
        st.sidebar.error(
            f"The total easiness percentages for {component} must be 100%. Currently, it is {total_easiness}%."
        )
        repair_easiness_thresholds[component] = None
    else:
        # ✅ Corrected cumulative summing logic
        repair_easiness_thresholds[component] = {
            "Low": repair_low,
            "Medium": repair_low + repair_medium,  # Cumulative sum
            "High": 100  # Always 100
        }


##########################################################################################
#PROCESS TIMES
##########################################################################################

# Configuración de Tiempos de Procesado para Reparación
#st.sidebar.header("Tiempos de Procesado para Reparación")

#components = ["Component_A", "Component_B", "Component_C"]
#process_times_repair = {}

#for component in components:
#    st.sidebar.subheader(component)
    
#    low_time = st.sidebar.number_input(
#        f"Tiempo (Low) - {component} (en minutos)", min_value=0, value=1200, step=10
#    )
#    medium_time = st.sidebar.number_input(
#        f"Tiempo (Medium) - {component} (en minutos)", min_value=0, value=1000, step=10
#    )
#    high_time = st.sidebar.number_input(
#        f"Tiempo (High) - {component} (en minutos)", min_value=0, value=760, step=10
#    )

#    process_times_repair[component] = {
#        "Low": low_time,
#        "Medium": medium_time,
#        "High": high_time
#    }
#st.write("Validación del parámetro 'process_times_repair':", process_times_repair)


# Configuración de Tiempos de Procesado para Reparación

st.sidebar.header("Process times based on Easiness to Repair")


components = ["Component_A", "Component_B", "Component_C"]
process_times_repair = {}

for component in components:
    st.sidebar.markdown(
        f"<h3 style='margin-bottom: 5px; font-size: 16px;'>{component}</h4>",
        unsafe_allow_html=True
    )

    # Crear columnas para tiempos de procesamiento
    cols = st.sidebar.columns(3)

    with cols[0]:
        low_time = st.number_input(
            f"Low (min)",
            min_value=0,
            value=1200,
            step=10,
            key=f"{component}_low_time"
        )

    with cols[1]:
        medium_time = st.number_input(
            f"Medium (min)",
            min_value=0,
            value=1000,
            step=10,
            key=f"{component}_medium_time"
        )

    with cols[2]:
        high_time = st.number_input(
            f"High (min)",
            min_value=0,
            value=760,
            step=10,
            key=f"{component}_high_time"
        )

    process_times_repair[component] = {
        "Low": low_time,
        "Medium": medium_time,
        "High": high_time
    }


###################################################################################
#QUALITY AFTER REPARATION BASED ON EASINESS TO REPAIR
###################################################################################


# Configuración de Umbrales de Calidad después de Reparación
#st.sidebar.header("Umbrales de Calidad para Reparación")

#components = ["Component_A", "Component_B", "Component_C"]
#quality_levels = ["Low", "Medium", "High"]
#repair_quality_thresholds = {}


#for component in components:
#    st.sidebar.subheader(f"Quality Distribution for {component}")
#    repair_quality_thresholds[component] = {}
#
#    for initial_quality in quality_levels:
#        st.sidebar.markdown(f"**After {initial_quality} Quality**")
#
#        quality_low = st.sidebar.number_input(
#            f"% Low after {initial_quality} - {component}",
#            min_value=0, max_value=100, value=40, step=1,
#            key=f"{component}_{initial_quality}_low"
#        )#
#        q#uality_medium = st.sidebar.number_input(
#            f"% Medium after {initial_quality} - {component}",
#         #   min_value=0, max_value=100, value=30, step=1,
#         #   key=f"{component}_{initial_quality}_medium"
#        #)
#        #quality_high = st.sidebar.number_input(
#        #    f"% High after {initial_quality} - {component}",
#            min_value=0, max_value=100, value=30, step=1,
#        #    key=f"{component}_{initial_quality}_high"
#        #)#

#        # Validate total percentage
#        total_quality = quality_low + quality_medium + quality_high
#        if total_quality != 100:
#            st.sidebar.error(
#                f"The total for {initial_quality} in {component} must equal 100%. Current: {total_quality}%.")
#            repair_quality_thresholds[component][initial_quality] = None
#        else:
#            repair_quality_thresholds[component][initial_quality] = {
#                "Low": quality_low,
#                "Medium": quality_low + quality_medium,
#                "High": 100  # Always cumulative
#            }

components = ["Component_A", "Component_B", "Component_C"]
quality_levels = ["Low", "Medium", "High"]
repair_quality_thresholds = {}

# Define default values (originally set in your model)
default_quality_thresholds = { 
    'Component_A': {
        'Low': {'Low': 80, 'Medium': 10, 'High':10},
        'Medium': {'Low': 40, 'Medium': 20, 'High':20},
        'High': {'Low': 10, 'Medium': 20, 'High':70}
    },
    'Component_B': { 
        'Low': {'Low': 80, 'Medium': 10, 'High':10},
        'Medium': {'Low': 40, 'Medium': 20, 'High':20},
        'High': {'Low': 10, 'Medium': 20, 'High':70}
    },
    'Component_C': { 
        'Low': {'Low': 80, 'Medium': 10, 'High':10},
        'Medium': {'Low': 40, 'Medium': 20, 'High':20},
        'High': {'Low': 10, 'Medium': 20, 'High':70}
    }
}

st.sidebar.header("Component Quality Distribution after Repair")

# Iterate over each component
for component in components:

    st.sidebar.markdown(
        f"<h3 style='margin-bottom: 0px;'> {component}</h3>",
        unsafe_allow_html=True
    )

    repair_quality_thresholds[component] = {}

    # Group by initial quality
    for initial_quality in quality_levels:
        st.sidebar.markdown(
            f"<h4 style='margin-bottom: 0px;'>When easiness to repair is {initial_quality} </h4>",
            unsafe_allow_html=True
        )
        
        cols = st.sidebar.columns(3)

        with cols[0]:
            quality_low = st.number_input(
                f"% Low",
                min_value=0,
                max_value=100,
                value=default_quality_thresholds[component][initial_quality]['Low'],  # ✅ Default value
                step=1,
                key=f"{component}_{initial_quality}_low"
            )

        with cols[1]:
            quality_medium = st.number_input(
                f"% Medium",
                min_value=0,
                max_value=100,
                value=default_quality_thresholds[component][initial_quality]['Medium'],  # ✅ Default value
                step=1,
                key=f"{component}_{initial_quality}_medium"
            )

        # Calculate `quality_high` dynamically so that the total is always 100%
        quality_high = 100 - (quality_low + quality_medium)

        with cols[2]:
            st.number_input(
                f"% High",
                min_value=0,
                max_value=100,
                value=quality_high,  # ✅ Ensure cumulative total reaches 100%
                step=1,
                key=f"{component}_{initial_quality}_high"
            )

        # Validate that the sum is exactly 100%
        total_quality = quality_low + quality_medium + quality_high
        if total_quality != 100:
            st.sidebar.error(
                f"The total for {initial_quality} in {component} must be 100%. Currently: {total_quality}%."
            )
            repair_quality_thresholds[component][initial_quality] = None
        else:
            repair_quality_thresholds[component][initial_quality] = {
                "Low": quality_low,
                "Medium": quality_low + quality_medium,  # Cumulative sum
                "High": 100  # Always 100%
            }



# Opcional: Mostrar los tiempos de procesamiento configurados para depuración
# st.write("Validación del parámetro 'process_times_repair':", process_times_repair)


###############################################################################################3
#EJECUCIÓN DE LA SIMULACIÓN
###########################################################################################


# Botón para ejecutar la simulación
if st.button("Run Simulation"):
    # Actualizar los parámetros de entrada
    #st.write("Contenido de process_times_repair antes de la actualización:")
    #st.write(process_times_repair)

    process_parameters.update({
        "monitoring_interval": monitoring_interval,
        "warmup_period": warmup_period,
        "include_stacked_chart_diagram_for_good_quality_components": include_stacked_chart_diagram_for_good_quality_components,
        "replenish_buffers": replenish_buffers,
        "include_arrival_variability": include_arrival_variability,
        "include_demand_variability": include_demand_variability,
        "discard_at_cleaning_and_inspection": discard_at_cleaning_and_inspection,
        "demand": {
            "interval": demand_interval,
            "variability": demand_variability,
            "quantity_min": demand_quantity_min,
            "quantity_max": demand_quantity_max
        },
        "cores_arrival": {
            "interval": cores_arrival_interval,
            "variability": cores_arrival_variability,
            "batch_size_min": cores_batch_size_min,
            "batch_size_max": cores_batch_size_max
        },
         "cleaning_and_inspection": {
                "batch_size": 1, 
                "capacity": 1,   
                "quality_thresholds": cleaning_quality_thresholds,
                "process_times": process_parameters["cleaning_and_inspection"]["process_times"]  
            },
        "component_repair": {
                "capacity": repair_capacity,  # Configurado en otro lugar
                "quality_thresholds": repair_quality_thresholds,
                "easiness_to_repair_thresholds": repair_easiness_thresholds,
                "process_times": process_times_repair,  # Fijo desde modelo.py
                "max_repair_attempts": max_repair_attempts  # Configurado en otro lugar
            }
    })

    #st.write("Contenido de process_parameters después de la actualización:")
    #st.text(json.dumps(process_parameters, indent=4))
    #st.write("Contenido de process_times_repair:")
    #st.write(process_times_repair)
    #st.write("Contenido completo de process_parameters antes de la simulación:")
    #st.write(json.dumps(process_parameters, indent=4))


    # Ejecutar la simulación
    simulation_output = run_simulation(simulation_time, process_parameters, generate_plots=False)

    # Extraer resultados
    results = simulation_output["results"]
    monitoring_data = simulation_output["monitoring_data"]
    include_stacked_chart = simulation_output["include_stacked_chart"]

    # Mostrar resultados principales
    st.write("### Simulation Results")
    results_df = pd.DataFrame([results]).round(2)
    st.dataframe(results_df)

    # Mostrar gráficos
    st.write("### Result Charts")
    plot_results(monitoring_data)
    if include_stacked_chart_diagram_for_good_quality_components  == 'yes':
        plot_stacked_chart(monitoring_data)
        plot_discarded_components_stacked_chart(monitoring_data)




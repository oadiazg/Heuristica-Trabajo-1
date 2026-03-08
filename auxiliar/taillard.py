"""
Implementación de funciones optimizadas para NWJSSP
usando caching y reutilización de cálculos.
"""

from methods.neh_basic import compute_offsets, find_start


# ===============================
# CALCULO DE TIEMPO DE COMPLETITUD
# ===============================
def compute_completion_time_nwjssp(sequence, jobs, m, offsets_cache=None):
    '''Funcion para calcular el tiempo de completitud total (makespan y flow time) para NWJSSP'''
    '''Requiere una secuencia de trabajos, los objetos Job, el numero de maquinas, y opcionalmente un cache de offsets'''
    '''Devuelve el total flow time (∑Cj) de la secuencia evaluada'''
    # Si la secuencia está vacía, el flow time es 0
    if not sequence:
        return 0
    # Se inicializa el tiempo disponible de cada máquina en 0 y el total flow time en 0
    machine_available = [0] * m
    total_flow = 0
    # Se procesa cada trabajo en la secuencia
    for job_idx in sequence:
        # Se obtiene el objeto Job del índice
        job = jobs[job_idx]
        # Se obtienen los offsets del trabajo (tiempo acumulado de operaciones previas)
        # Si existe cache, se usa para evitar recalcularlos (OPTIMIZACION 4)
        if offsets_cache is not None:
            offsets = offsets_cache[job_idx]
        else:
            offsets = compute_offsets(job)
        # Se encuentra el start factible para que todas las operaciones se realicen cumpliendo No-Wait
        start = find_start(job, machine_available.copy(), offsets)
        # Se calcula el tiempo de completitud del trabajo (finalización en la última máquina)
        completion = start + offsets[-1] + job.operations[-1].p
        # Se suma al total flow time
        total_flow += completion
        # Se recorren las operaciones del trabajo actualizando el tiempo disponible de cada máquina
        for j, op in enumerate(job.operations):
            # Se obtiene la máquina de la operación
            machine = op.machine
            # Se calcula el tiempo de inicio de la operación actual
            start_op = start + offsets[j]
            # Se calcula el tiempo de finalización de la operación
            end_op = start_op + op.p
            # Se actualiza el tiempo disponible de la máquina
            machine_available[machine] = end_op
    
    # Se devuelve el total flow time de la secuencia
    return total_flow


# ===============================
# EVALUAR INSERCION PARCIAL
# ===============================
def evaluate_partial_insertion_nwjssp(sequence, new_job, insert_pos, jobs, m, offsets_cache=None):
    '''Funcion para evaluar el costo de insertar un trabajo en una posición específica'''
    '''Requiere la secuencia actual, el índice del trabajo a insertar, la posición, los objetos Job, el numero de maquinas, y opcionalmente cache de offsets'''
    '''Devuelve el total flow time (∑Cj) de la secuencia con el trabajo insertado'''
    # Se crea una copia de la secuencia actual
    temp_sequence = sequence.copy()
    # Se inserta el nuevo trabajo en la posición especificada
    temp_sequence.insert(insert_pos, new_job)
    
    # Se calcula el flow time de la nueva secuencia usando la función optimizada
    total_flow = compute_completion_time_nwjssp(temp_sequence, jobs, m, offsets_cache)
    
    # Se devuelve el total flow time
    return total_flow


# ===============================
# OBTENER ESTADO DE MAQUINAS
# ===============================
def get_machine_state_after_sequence(sequence, jobs, m, offsets_cache=None):
    '''Funcion para calcular el estado de disponibilidad de máquinas después de procesar una secuencia'''
    '''Esta función reutiliza cálculos previos para evitar recalcular (OPTIMIZACION 3)'''
    '''Requiere la secuencia de trabajos, los objetos Job, el numero de maquinas, y opcionalmente cache de offsets'''
    '''Devuelve un array con los tiempos de disponibilidad de cada máquina'''
    # Se inicializa el tiempo disponible de cada máquina en 0
    machine_available = [0] * m
    
    # Se procesa cada trabajo en la secuencia para actualizar los tiempos de máquinas
    for job_idx in sequence:
        # Se obtiene el objeto Job del índice
        job = jobs[job_idx]
        
        # Se obtienen los offsets del trabajo
        # Si existe cache, se usa para evitar recalcularlos (OPTIMIZACION 4)
        if offsets_cache is not None:
            offsets = offsets_cache[job_idx]
        else:
            offsets = compute_offsets(job)
        
        # Se encuentra el start factible para que todas las operaciones se realicen cumpliendo No-Wait
        start = find_start(job, machine_available.copy(), offsets)
        
        # Se recorren las operaciones del trabajo actualizando el tiempo disponible de cada máquina
        for j, op in enumerate(job.operations):
            # Se obtiene la máquina de la operación
            machine = op.machine
            # Se calcula el tiempo de inicio de la operación
            start_op = start + offsets[j]
            # Se calcula el tiempo de finalización de la operación
            end_op = start_op + op.p
            # Se actualiza el tiempo disponible de la máquina
            machine_available[machine] = end_op
    
    # Se devuelve el estado final de disponibilidad de máquinas
    return machine_available
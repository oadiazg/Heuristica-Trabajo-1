"""
Implementación del algoritmo NEH modificado (NEH-df) optimizado para NWJSSP.

Optimizaciones aplicadas:
1. find_start() mejorado (en neh_basic.py)
3. Reutilizar machine_available entre inserciones
4. Cachear offsets de todos los trabajos
"""

import statistics
from methods.neh_basic import evaluate_sequence, compute_offsets
from auxiliar.branch_and_bound import best_group_order
from auxiliar.taillard import (
    compute_completion_time_nwjssp,
    evaluate_partial_insertion_nwjssp,
    get_machine_state_after_sequence
)


# ==========================================
# INDICE DE PRIORIDAD AVG + STD
# ==========================================
def job_priority_index(job):
    '''Funcion para calcular el indice de prioridad para cada trabajo'''
    '''Requiere el objeto Job que deseamos evaluar'''
    '''Devuelve el indice de prioridad, definido por los autores como AVG + STD'''
    # Se obtienen los tiempos de procesamiento de todas las operaciones del trabajo
    processing_times = [op.p for op in job.operations]
    # Se calcula el promedio de los tiempos de procesamiento
    avg = statistics.mean(processing_times)
    # Se calcula la desviación estándar de los tiempos de procesamiento
    std = statistics.pstdev(processing_times)

    # Se devuelve el índice de prioridad como la suma del promedio y la desviación estándar
    return avg + std


# ==========================================
# ORDENAMIENTO DE JOBS
# ==========================================
def sort_jobs_by_priority(jobs):
    '''Funcion para ordenar los trabajos por su indice de prioridad'''
    '''Requiere la lista de objetos Job a ordenar'''
    '''Devuelve una lista de índices de trabajos ordenada por prioridad (mayor a menor)'''
    # Se crea una lista de índices de trabajos del 0 al n-1
    order = list(range(len(jobs)))
    # Se ordena la lista de índices según el índice de prioridad del trabajo correspondiente
    # Se ordena de mayor a menor (reverse=True)
    order.sort(
        key=lambda j: job_priority_index(jobs[j]),
        reverse=True
    )

    # Se devuelve la lista de índices ordenada
    return order


# ==========================================
# MEJOR INSERCION DE UN SOLO JOB
# ==========================================
def best_insertion_single_taillard(sequence, job, jobs, m, offsets_cache=None):
    '''Funcion para encontrar la mejor posición de inserción de un solo trabajo'''
    '''Incorpora OPTIMIZACION 3: Reutilizar machine_available entre inserciones'''
    '''Incorpora OPTIMIZACION 4: Usar offsets precalculados'''
    '''Requiere la secuencia actual, el índice del job a insertar, los objetos Job, numero de maquinas, y opcionalmente cache de offsets'''
    '''Devuelve la mejor posición de inserción y el valor de la función objetivo para esa inserción'''
    # Se inicializan variables para guardar la mejor posición y el mejor valor encontrados
    best_pos = 0
    best_value = float("inf")
    # OPTIMIZACION 3: Se calcula el estado de máquinas después de la secuencia actual UNA SOLA VEZ
    # Esto evita recalcular el estado de máquinas para cada posición de inserción
    machine_available_base = get_machine_state_after_sequence(sequence, jobs, m, offsets_cache)
    
    # Se prueba cada posición posible para insertar el trabajo
    for pos in range(len(sequence) + 1):
        # Se crea una copia de la secuencia actual
        temp_sequence = sequence.copy()
        # Se inserta el nuevo trabajo en la posición actual
        temp_sequence.insert(pos, job)
        # Se evalúa el costo de insertar el trabajo en esta posición
        # La función utiliza el cache de offsets (OPTIMIZACION 4)
        value = evaluate_partial_insertion_nwjssp(
            sequence,
            job,
            pos,
            jobs,
            m,
            offsets_cache
        )
        # Si el valor de la función objetivo es mejor que el mejor encontrado hasta ahora, se actualiza
        if value < best_value:
            best_value = value
            best_pos = pos
    
    # Se devuelve la mejor posición de inserción y el valor de la función objetivo
    return best_pos, best_value

# ==========================================
# MEJOR INSERCION DE UN GRUPO
# ==========================================
def insert_group_best_position_taillard(sequence, group_order, jobs, m, offsets_cache=None):
    '''Funcion para encontrar la mejor inserción de un grupo de trabajos en la secuencia'''
    '''Incorpora OPTIMIZACION 4: Usar offsets precalculados'''
    '''Requiere la secuencia actual, el orden del grupo, los objetos Job, numero de maquinas, y opcionalmente cache de offsets'''
    '''Devuelve la mejor secuencia resultante de insertar el grupo y el valor de la función objetivo para esa secuencia'''
    # Se inicializan variables para guardar la mejor secuencia y el mejor valor encontrados
    best_seq = None
    best_value = float("inf")
    
    # Se prueba cada posición posible para insertar el grupo completo
    for pos in range(len(sequence) + 1):
        # Se crea una copia de la secuencia actual
        temp = sequence.copy()
        # Se inserta el grupo completo en la posición actual (respetando el orden del grupo)
        for i, job in enumerate(group_order):
            # Se inserta cada trabajo del grupo manteniendo el orden relativo
            temp.insert(pos + i, job)
        # Se evalúa el costo de insertar el grupo en esta posición
        # Utiliza cache de offsets (OPTIMIZACION 4)
        value = compute_completion_time_nwjssp(temp, jobs, m, offsets_cache)
        # Si el valor de la función objetivo es mejor que el mejor encontrado hasta ahora, se actualiza
        if value < best_value:
            best_value = value
            best_seq = temp
    
    # Se devuelve la mejor secuencia y el valor de la función objetivo
    return best_seq, best_value


# ==========================================
# HEURISTICA NEH MODIFICADA (AUTORES)
# ==========================================
def neh_autores_taillard(jobs, m, F=2):
    '''Implementa el algoritmo NEH modificado con Rule-f (NEH-df) propuesto por Gao y autores'''
    '''Incorpora OPTIMIZACION 1: find_start() mejorado en neh_basic.py'''
    '''Incorpora OPTIMIZACION 3: Reutilizar machine_available entre inserciones'''
    '''Incorpora OPTIMIZACION 4: Cachear offsets de todos los trabajos'''
    '''Requiere los objetos Job, numero de maquinas, y tamaño del grupo F (por defecto 2)'''
    '''Devuelve una secuencia de trabajos construida'''
    n = len(jobs)
    # OPTIMIZACION 4: Se cachean TODOS los offsets de los trabajos UNA SOLA VEZ
    # Esto evita recalcularlos múltiples veces durante el algoritmo
    offsets_cache = {}
    for job_idx in range(n):
        # Para cada trabajo, se calcula y se guarda su offset
        offsets_cache[job_idx] = compute_offsets(jobs[job_idx])
    # STEP 1: Se ordenan los trabajos por índice de prioridad (AVG + STD) de mayor a menor
    Js = sort_jobs_by_priority(jobs)
    # Se inicializa la secuencia vacía
    sequence = []    
    # STEP 2: Se repite MIENTRAS el número de trabajos no insertados sea mayor o igual a F
    while len(Js) >= F:
        # Se obtiene el costo actual de la secuencia (antes de insertar un nuevo trabajo)
        if sequence:
            # Si la secuencia no está vacía, se calcula el total flow time actual
            current_cost = compute_completion_time_nwjssp(sequence, jobs, m, offsets_cache)
        else:
            # Si la secuencia está vacía, el costo es infinito (cualquier inserción será mejor)
            current_cost = float("inf")
        # Se toma el primer trabajo de la lista de trabajos no insertados
        j = Js[0]      
        # Se intenta inserción individual (Rule 2)
        # Se busca la mejor posición para insertar el trabajo individual
        pos, new_cost = best_insertion_single_taillard(sequence, j, jobs, m, offsets_cache)

        # Si C_max NO cambia o empeora (new_cost <= current_cost), insertar j y continuar
        if len(sequence) == 0 or new_cost <= current_cost:
            # Se inserta el trabajo en la mejor posición encontrada
            sequence.insert(pos, j)
            # Se remueve el trabajo de la lista de trabajos no insertados
            Js.pop(0)
        # Si C_max EMPEORA, aplicar Rule-f (inserción grupal con B&B)
        else:
            # Se seleccionan los primeros F trabajos del grupo de trabajos no insertados
            group = Js[:F]
            # Se obtiene el mejor orden del grupo usando Branch & Bound
            best_order = best_group_order(sequence, group, jobs, m, use_taillard=True, offsets_cache=offsets_cache)
            # Se valida que best_order no sea None (caso especial si el grupo está vacío)
            if best_order is None:
                # Fallback: Si no se encuentra orden válido, insertar trabajos individuales
                for job_idx in group:
                    # Se encuentra la mejor posición para cada trabajo del grupo
                    best_pos, _ = best_insertion_single_taillard(sequence, job_idx, jobs, m, offsets_cache)
                    # Se inserta el trabajo en la mejor posición encontrada
                    sequence.insert(best_pos, job_idx)
                # Se remueve los F trabajos insertados de la lista
                Js = Js[F:]
            else:
                # Se inserta el grupo en la mejor posición encontrada
                best_seq, best_cost = insert_group_best_position_taillard(
                    sequence,
                    best_order,
                    jobs,
                    m,
                    offsets_cache
                )
                
                # Se actualiza la secuencia con la mejor secuencia encontrada
                sequence = best_seq
                # Se remueve los F trabajos que acaban de ser insertados
                Js = Js[F:]
    
    # STEP 3: Se insertan los trabajos restantes (cuando |Js| < F) usando Rule 2
    for j in Js:
        # Para cada trabajo restante, se encuentra la mejor posición de inserción
        best_pos, _ = best_insertion_single_taillard(sequence, j, jobs, m, offsets_cache)
        # Se inserta el trabajo en la mejor posición encontrada
        sequence.insert(best_pos, j)
    
    # Se devuelve la secuencia de trabajos construida
    return sequence
"""
Implementación del algoritmo NEH modificado (NEH-df) propuesto por Gao y autores.
Para NWJSSP (No-Wait Job Shop Scheduling Problem).
"""

import statistics
from methods.neh_basic import evaluate_sequence
from auxiliar.branch_and_bound import best_group_order


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
def best_insertion_single(sequence, job, jobs, m):
    '''Funcion para encontrar la mejor posición de inserción de un solo trabajo'''
    '''Requiere la secuencia actual, el índice del job a insertar, los objetos Job, y el número de máquinas'''
    '''Devuelve la mejor posición de inserción y el valor de la función objetivo para esa inserción'''
    # Se inicializan variables para guardar la mejor posición y el mejor valor encontrados
    best_pos = 0
    best_value = float("inf")
    
    # Se prueba cada posición posible para insertar el trabajo (desde 0 hasta len(sequence))
    for pos in range(len(sequence) + 1):
        # Se crea una copia de la secuencia actual
        temp = sequence.copy()
        # Se inserta el nuevo trabajo en la posición actual
        temp.insert(pos, job)
        # Se evalúa el costo de insertar el trabajo en esta posición
        value = evaluate_sequence(temp, jobs, m)
        # Si el valor de la función objetivo es mejor que el mejor encontrado hasta ahora, se actualiza
        if value < best_value:
            best_value = value
            best_pos = pos
    
    # Se devuelve la mejor posición de inserción y el valor de la función objetivo
    return best_pos, best_value


# ==========================================
# GENERAR PERMUTACIONES DEL GRUPO
# ==========================================
def generate_group_permutations(group):
    '''Funcion para generar todas las permutaciones posibles de un grupo de trabajos (para G pequeno)'''
    '''Requiere la lista de trabajos del grupo a permutar'''
    '''Devuelve un iterador con todas las permutaciones posibles de los trabajos del grupo'''
    # Se importa itertools para usar la función permutations
    import itertools
    # Se devuelve un iterador con todas las permutaciones del grupo
    return itertools.permutations(group)


# ==========================================
# MEJOR INSERCION DE UN GRUPO (por permutaciones)
# ==========================================
def find_best_group_insertion(sequence, group, jobs, m):
    '''Funcion para encontrar la mejor inserción de un grupo de trabajos probando todas las permutaciones'''
    '''Requiere la secuencia actual, el grupo de trabajos a insertar, los objetos Job, y el número de máquinas'''
    '''Devuelve la mejor secuencia resultante de insertar el grupo y el valor de la función objetivo para esa secuencia'''
    # Se inicializan variables para guardar la mejor secuencia y el mejor valor encontrados
    best_sequence = None
    best_value = float("inf")
    
    # Se generan todas las permutaciones posibles del grupo de F trabajos
    permutations = generate_group_permutations(group)
    
    # Se recorren todas las permutaciones posibles del grupo
    for perm in permutations:
        # Se convierte la tupla de permutación a lista
        perm = list(perm)
        # Para cada permutación, se prueban todas las posiciones de inserción posibles para el grupo completo
        for pos in range(len(sequence) + 1):
            # Se crea una copia de la secuencia actual
            temp = sequence.copy()
            # Se inserta el grupo completo en la posición actual (respetando el orden de la permutación)
            for i, job in enumerate(perm):
                # Se inserta cada trabajo del grupo en la posición pos + i
                temp.insert(pos + i, job)
            # Se evalúa el costo de insertar el grupo en esta posición con esta permutación
            value = evaluate_sequence(temp, jobs, m)
            # Si el valor de la función objetivo es mejor que el mejor encontrado hasta ahora, se actualiza
            if value < best_value:
                best_value = value
                best_sequence = temp

    # Se devuelve la mejor secuencia y el valor de la función objetivo
    return best_sequence, best_value


# ==========================================
# MEJOR INSERCION DE UN GRUPO (por branch & bound)
# ==========================================
def insert_group_best_position(sequence, group_order, jobs, m):
    '''Funcion para insertar un grupo de trabajos en el mejor orden y posición'''
    '''Requiere la secuencia actual, el mejor orden del grupo encontrado por B&B, los objetos Job, y el número de máquinas'''
    '''Devuelve la mejor secuencia después de insertar el grupo y el valor de la función objetivo'''
    # Se inicializan variables para guardar la mejor secuencia y el mejor valor encontrados
    best_seq = None
    best_value = float("inf")

    # Se prueban todas las posiciones posibles para insertar el grupo
    for pos in range(len(sequence) + 1):
        # Se crea una copia de la secuencia actual
        temp = sequence.copy()

        # Se inserta el grupo en la posición actual (respetando el orden encontrado por B&B)
        for i, job in enumerate(group_order):
            # Se inserta cada trabajo del grupo manteniendo el orden
            temp.insert(pos + i, job)

        # Se evalúa la secuencia resultante después de insertar el grupo
        value = evaluate_sequence(temp, jobs, m)

        # Si el valor de la función objetivo es mejor que el mejor encontrado hasta ahora, se actualiza
        if value < best_value:
            best_value = value
            best_seq = temp

    # Se devuelve la mejor secuencia y el valor de la función objetivo
    return best_seq, best_value


# ==========================================
# HEURISTICA NEH MODIFICADA (AUTORES)
# ==========================================
def neh_autores(jobs, m, F=2):
    '''Implementa el algoritmo NEH modificado con Rule-f (NEH-df) propuesto por Gao y autores'''
    '''Requiere los objetos Job, numero de maquinas, y tamaño del grupo F (por defecto 2)'''
    '''Devuelve una secuencia de trabajos construida'''
    n = len(jobs)
    
    # STEP 1: Se ordenan los trabajos por índice de prioridad (AVG + STD) de mayor a menor
    Js = sort_jobs_by_priority(jobs)
    # Se inicializa la secuencia vacía
    sequence = []
    
    # STEP 2: Se repite MIENTRAS el número de trabajos no insertados sea mayor o igual a F
    while len(Js) >= F:
        
        # Se obtiene el costo actual de la secuencia (antes de insertar un nuevo trabajo)
        if sequence:
            # Si la secuencia no está vacía, se calcula el total flow time actual
            current_cost = evaluate_sequence(sequence, jobs, m)
        else:
            # Si la secuencia está vacía, el costo es infinito (cualquier inserción será mejor)
            current_cost = float("inf")
        
        # Se toma el primer trabajo de la lista de trabajos no insertados
        j = Js[0]
        
        # Se intenta inserción individual (Rule 2)
        # Se busca la mejor posición para insertar el trabajo individual
        pos, new_cost = best_insertion_single(sequence, j, jobs, m)
        
        # Si C_max NO empeora (new_cost <= current_cost), insertar j y continuar
        if len(sequence) == 0 or new_cost <= current_cost:
            # Se inserta el trabajo en la mejor posición encontrada
            sequence.insert(pos, j)
            # Se remueve el trabajo de la lista de trabajos no insertados
            Js.pop(0)
        
        # Si C_max EMPEORA significativamente, aplicar Rule-f (inserción grupal con B&B)
        else:
            # Se seleccionan los primeros F trabajos del grupo de trabajos no insertados
            group = Js[:F]
            
            # Se obtiene el mejor orden del grupo usando Branch & Bound
            best_order = best_group_order(sequence, group, jobs, m)
            
            # Se valida que best_order no sea None (caso especial si el grupo está vacío)
            if best_order is None:
                # Fallback: Si no se encuentra orden válido, insertar trabajos individuales
                for job_idx in group:
                    # Se encuentra la mejor posición para cada trabajo del grupo
                    best_pos, _ = best_insertion_single(sequence, job_idx, jobs, m)
                    # Se inserta el trabajo en la mejor posición encontrada
                    sequence.insert(best_pos, job_idx)
                # Se remueve los F trabajos insertados de la lista
                Js = Js[F:]
            else:
                # Se inserta el grupo en la mejor posición encontrada
                best_seq, best_cost = insert_group_best_position(
                    sequence,
                    best_order,
                    jobs,
                    m
                )
                
                # Se actualiza la secuencia con la mejor secuencia encontrada
                sequence = best_seq
                # Se remueve los F trabajos que acaban de ser insertados
                Js = Js[F:]
    
    # STEP 3: Se insertan los trabajos restantes (cuando |Js| < F) usando Rule 2
    for j in Js:
        # Para cada trabajo restante, se encuentra la mejor posición de inserción
        best_pos, _ = best_insertion_single(sequence, j, jobs, m)
        # Se inserta el trabajo en la mejor posición encontrada
        sequence.insert(best_pos, j)
    
    # Se devuelve la secuencia de trabajos construida
    return sequence
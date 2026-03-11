"""
Implementación del algoritmo NEH Aleatorizado Simple con Ruido.
Versión simplificada de neh_autores_taillard con criterio de aceptación ruidoso.

Características:
1. Una sola fase constructiva
2. Ruido controlado en el intervalo de aceptación
3. Mantiene Branch & Bound para inserciones grupales (Rule-f)
4. La única diferencia: criterio ruidoso en lugar de determinista
5. Hereda toda la lógica de neh_autores_taillard
"""
import statistics
import random
from methods.neh_basic import compute_offsets, read_instance, print_schedule
from auxiliar.branch_and_bound import best_group_order
from auxiliar.taillard import (
    compute_completion_time_nwjssp,
    evaluate_partial_insertion_nwjssp,
    get_machine_state_after_sequence,
    IncrementalSequenceEvaluator
)

# ==========================================
# INDICE DE PRIORIDAD AVG + STD
# ==========================================
def job_priority_index(job):
    """Indice de prioridad basado en promedio + desviación estándar de los tiempos de operación"""
    processing_times = [op.p for op in job.operations]
    avg = statistics.mean(processing_times)
    std = statistics.stdev(processing_times) if len(processing_times) > 1 else 0
    return avg + std

# ==========================================
# ORDENAMIENTO DE JOBS
# ==========================================
def sort_jobs_by_priority(jobs):
    """Ordena los trabajos de mayor a menor prioridad según AVG + STD"""
    n = len(jobs)
    order = list(range(n))
    # La lambda recibe un índice j, y ahora pasamos jobs[j] (objeto Job) a job_priority_index
    order.sort(key=lambda j: job_priority_index(jobs[j]), reverse=True)
    return order

# ==========================================
# CALCULAR COSTO INTRINSECO DE UN TRABAJO
# ==========================================
def get_job_processing_cost(job):
    """Devuelve el costo intrínseco de un trabajo como la suma de sus tiempos de procesamiento"""
    return sum(op.p for op in job.operations)

# ==========================================
# GENERAR UMBRAL ALEATORIO CON RUIDO
# ==========================================
def generate_noisy_threshold(cost_job_new, noise_ratio=0.3):
    """Funcion para generar un umbral aleatorio alrededor del costo del trabajo nuevo"""
    """Incorpora ruido mediante un intervalo [cost_job_new * (1 - noise_ratio), cost_job_new * (1 + noise_ratio)]"""
    """Requiere el costo intrínseco del trabajo y el ratio de ruido (por defecto 0.3, es decir ±30%)"""
    """Devuelve un umbral aleatorio dentro del intervalo definido"""
    min_threshold = cost_job_new * (1 - noise_ratio)
    max_threshold = cost_job_new * (1 + noise_ratio)
    noisy_threshold = random.uniform(min_threshold, max_threshold)
    return noisy_threshold

# ==========================================
# MEJOR INSERCION DE UN SOLO JOB
# ==========================================
def best_insertion_single_taillard(sequence, job, jobs, m, offsets_cache=None):
    """Encuentra la mejor posición para insertar un solo trabajo en la secuencia usando Taillard"""
    best_pos = 0
    best_cost = float("inf")

    if offsets_cache is None:
        offsets_cache = {}
        for job_idx in range(len(jobs)):
            offsets_cache[job_idx] = compute_offsets(jobs[job_idx])

    for pos in range(len(sequence) + 1):
        # Copia temporal de la secuencia
        temp_sequence = sequence.copy()
        # Insertar el trabajo en la posición pos
        temp_sequence.insert(pos, job)
        # Evaluar el costo total de la secuencia resultante
        cost = compute_completion_time_nwjssp(temp_sequence, jobs, m, offsets_cache)
        # Actualizar mejor costo y posición
        if cost < best_cost:
            best_cost = cost
            best_pos = pos

    return best_pos, best_cost

# ==========================================
# MEJOR INSERCION DE UN GRUPO
# ==========================================
def insert_group_best_position_taillard(sequence, group_order, jobs, m, offsets_cache=None):
    """Inserta un grupo de trabajos en la mejor posición dentro de la secuencia usando Taillard"""
    best_sequence = None
    best_cost = float("inf")

    if offsets_cache is None:
        offsets_cache = {}
        for job_idx in range(len(jobs)):
            offsets_cache[job_idx] = compute_offsets(jobs[job_idx])

    # Probar insertar el grupo en todas las posiciones posibles de la secuencia
    for pos in range(len(sequence) + 1):
        # Copia temporal de la secuencia
        temp_sequence = sequence.copy()
        # Insertar el grupo en el orden dado a partir de la posición pos
        for idx, job in enumerate(group_order):
            temp_sequence.insert(pos + idx, job)
        # Evaluar el costo total de la secuencia resultante
        cost = compute_completion_time_nwjssp(temp_sequence, jobs, m, offsets_cache)
        # Actualizar mejor costo y mejor secuencia
        if cost < best_cost:
            best_cost = cost
            best_sequence = temp_sequence.copy()

    return best_sequence, best_cost

# ==========================================
# HEURISTICA NEH SIMPLE CON RUIDO
# ==========================================
def neh_simple_noise(jobs, m, F=2, noise_ratio=0.3, seed=None):
    """
    Implementa el algoritmo NEH modificado con Rule-f (NEH-df) propuesto por Gao y autores
    Versión ALEATORIZADA: Criterio de aceptación ruidoso en lugar de determinista
    Incorpora optimizaciones: find_start() mejorado, evaluación incremental, caching de offsets, B&B optimizado
    Requiere los objetos Job, numero de maquinas, tamaño del grupo F (por defecto 2)
    noise_ratio controla la amplitud del intervalo de ruido como % del costo del trabajo (por defecto 0.3, ±30%)
    seed: semilla opcional para asegurar reproducibilidad de los números aleatorios generados
    Devuelve una secuencia de trabajos construida
    """
    # Semilla opcional para reproducibilidad
    if seed is not None:
        random.seed(seed)

    n = len(jobs)
    # OPTIMIZACION 4: Se cachean TODOS los offsets de los trabajos UNA SOLA VEZ
    # Esto evita recalcularlos múltiples veces durante el algoritmo
    offsets_cache = {}
    for job_idx in range(n):
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
            # Si la secuencia está vacía, el costo actual es 0
            current_cost = 0

        # Se toma el primer trabajo de la lista de trabajos no insertados
        j = Js[0]
        # Se obtiene el objeto Job para acceder a sus operaciones
        job = jobs[j]
        # Se calcula el costo intrínseco del trabajo nuevo (suma de tiempos de procesamiento)
        cost_job_new = get_job_processing_cost(job)
        # Se genera un umbral aleatorio alrededor del costo del trabajo nuevo
        # Este umbral introduce RUIDO CONTROLADO en el criterio de decisión
        # Intervalo: [cost_job_new * (1 - noise_ratio), cost_job_new * (1 + noise_ratio)]
        noisy_threshold = generate_noisy_threshold(cost_job_new, noise_ratio)

        # Se intenta inserción individual (Rule 2)
        # Se busca la mejor posición para insertar el trabajo individual
        pos, new_cost = best_insertion_single_taillard(sequence, j, jobs, m, offsets_cache)

        # CRITERIO ALEATORIZADO: Aceptar inserción si new_cost <= current_cost + noisy_threshold
        # El umbral aleatorio permite que a veces se acepte la inserción individual incluso cuando
        # el costo sube más de lo esperado (si el ruido es favorable)
        # O que se rechace incluso cuando el costo sube poco (si el ruido es desfavorable)
        # Esto introduce DIVERSIDAD en la exploración del espacio de soluciones
        if len(sequence) == 0 or new_cost <= current_cost + noisy_threshold:
            # Se inserta el trabajo en la mejor posición encontrada
            sequence.insert(pos, j)
            # Se remueve el trabajo de la lista de trabajos no insertados
            Js.pop(0)
        # Si el costo empeora MÁS del umbral aleatorio, aplicar Rule-f (inserción grupal con B&B)
        else:
            # Se seleccionan los primeros F trabajos del grupo de trabajos no insertados
            group = Js[:F]
            # Se obtiene el mejor orden del grupo usando Branch & Bound
            best_order = best_group_order(
                sequence,
                group,
                jobs,
                m,
                use_taillard=True,
                offsets_cache=offsets_cache
            )
            # Se valida que best_order no sea None (caso especial si el grupo está vac��o)
            if best_order is None:
                # Fallback: Si no se encuentra orden válido, insertar trabajos individuales
                for job_idx in group:
                    # Se encuentra la mejor posición para cada trabajo del grupo
                    best_pos, _ = best_insertion_single_taillard(sequence, job_idx, jobs, m, offsets_cache)
                    # Se inserta el trabajo en la mejor posición encontrada
                    sequence.insert(best_pos, job_idx)
                # Se remueven los F trabajos que acaban de ser insertados
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
        # Se encuentra la mejor posición para cada trabajo restante
        best_pos, _ = best_insertion_single_taillard(sequence, j, jobs, m, offsets_cache)
        # Se inserta el trabajo en la mejor posición encontrada
        sequence.insert(best_pos, j)

    # Se devuelve la secuencia de trabajos construida
    return sequence
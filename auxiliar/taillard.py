"""
Implementación de funciones optimizadas para NWJSSP con evaluación incremental.
Mantiene estado de máquinas para evitar recalcular desde el principio.
"""
from methods.neh_basic import compute_offsets, find_start

# ===============================
# CALCULO DE TIEMPO DE COMPLETITUD
# ===============================
def compute_completion_time_nwjssp(sequence, jobs, m, offsets_cache=None):
    'Funcion para calcular el tiempo de completitud total'
    'Requiere una secuencia de trabajos, los objetos Job, numero de maquinas, y opcionalmente cache de offsets'
    'Devuelve el total flow time (∑Cj) de la secuencia evaluada'
    if not sequence:
        return 0
    machine_available = [0] * m
    total_flow = 0
    for job_idx in sequence:
        job = jobs[job_idx]
        if offsets_cache is not None:
            offsets = offsets_cache[job_idx]
        else:
            offsets = compute_offsets(job)
        start = find_start(job, machine_available.copy(), offsets)
        completion = start + offsets[-1] + job.operations[-1].p
        total_flow += completion
        for j, op in enumerate(job.operations):
            machine = op.machine
            start_op = start + offsets[j]
            end_op = start_op + op.p
            machine_available[machine] = end_op
    return total_flow

# ===============================
# EVALUAR INSERCION PARCIAL
# ===============================
def evaluate_partial_insertion_nwjssp(sequence, new_job, insert_pos, jobs, m, offsets_cache=None):
    'Funcion para evaluar el costo de insertar un trabajo en una posición específica'
    'Requiere la secuencia actual, indice del trabajo a insertar, posicion, jobs, numero de maquinas, y opcionalmente cache de offsets'
    'Devuelve el total flow time de la secuencia con el trabajo insertado'
    temp_sequence = sequence.copy()
    temp_sequence.insert(insert_pos, new_job)
    total_flow = compute_completion_time_nwjssp(temp_sequence, jobs, m, offsets_cache)
    return total_flow

# ===============================
# OBTENER ESTADO DE MAQUINAS
# ===============================
def get_machine_state_after_sequence(sequence, jobs, m, offsets_cache=None):
    'Funcion para calcular el estado de disponibilidad de máquinas después de procesar una secuencia'
    'Requiere secuencia de trabajos, jobs, numero de maquinas, y opcionalmente cache de offsets'
    'Devuelve array con tiempos de disponibilidad de cada máquina'
    machine_available = [0] * m
    for job_idx in sequence:
        job = jobs[job_idx]
        if offsets_cache is not None:
            offsets = offsets_cache[job_idx]
        else:
            offsets = compute_offsets(job)
        start = find_start(job, machine_available.copy(), offsets)
        for j, op in enumerate(job.operations):
            machine = op.machine
            start_op = start + offsets[j]
            end_op = start_op + op.p
            machine_available[machine] = end_op
    return machine_available

# ===============================
# EVALUACION INCREMENTAL OPTIMIZADA
# ===============================
class IncrementalSequenceEvaluator:
    'Clase para evaluar inserciones de trabajos sin recalcular toda la secuencia'
    'Mantiene estado de máquinas para reutilizar cálculos'
    def __init__(self, jobs, m, offsets_cache=None):
        'Inicializa el evaluador con jobs, numero de maquinas, y opcionalmente cache de offsets'
        self.jobs = jobs
        self.m = m
        self.offsets_cache = offsets_cache
        self.machine_available = [0] * m
        self.total_flow = 0
        self.sequence = []
    def add_job_to_end(self, job_idx):
        'Agrega un trabajo al final de la secuencia y actualiza estado'
        'Requiere el indice del trabajo a agregar'
        'Devuelve el nuevo total flow time'
        job = self.jobs[job_idx]
        if self.offsets_cache is not None:
            offsets = self.offsets_cache[job_idx]
        else:
            offsets = compute_offsets(job)
        start = find_start(job, self.machine_available.copy(), offsets)
        completion = start + offsets[-1] + job.operations[-1].p
        self.total_flow += completion
        for j, op in enumerate(job.operations):
            machine = op.machine
            start_op = start + offsets[j]
            end_op = start_op + op.p
            self.machine_available[machine] = end_op
        self.sequence.append(job_idx)
        return self.total_flow
    def evaluate_insertion_cost(self, job_idx, insert_pos):
        'Evalua el costo de insertar un trabajo en una posicion sin agregarlo realmente'
        'Requiere indice del trabajo e indice de posicion'
        'Devuelve el total flow time si se insertara en esa posicion'
        temp_sequence = self.sequence.copy()
        temp_sequence.insert(insert_pos, job_idx)
        return compute_completion_time_nwjssp(temp_sequence, self.jobs, self.m, self.offsets_cache)
    def reset(self):
        'Reinicia el evaluador a estado vacío'
        self.machine_available = [0] * self.m
        self.total_flow = 0
        self.sequence = []
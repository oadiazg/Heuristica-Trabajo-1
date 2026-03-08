import time

# ===============================
# ESTRUCTURAS DE DATOS
# ===============================
class Operation:
    def __init__(self, machine, processing_time):
        self.machine = machine
        self.p = processing_time

class Job:
    def __init__(self, operations, release):
        self.operations = operations
        self.release = release

# ===============================
# LECTURA DE INSTANCIAS
# ===============================
def read_instance(file):
    'Funcion para leer cada instancia del trabajo (Cada instancia se asume el mismo formato de Anexo 2)'
    'Requiere el archivo file a leer'
    'Devuelve una lista de objetos Job y el número de máquinas (m)'
    with open(file) as f:
        n, m = map(int, f.readline().split()) 
        jobs = []
        for _ in range(n):
            data = list(map(int, f.readline().split()))
            operations = []
            for i in range(0, 2*m, 2):
                machine = data[i]
                p = data[i+1]
                operations.append(Operation(machine, p))
            release = data[-1]
            jobs.append(Job(operations, release))
    return jobs, m

# ===============================
# CALCULO DE OFFSETS (NO WAIT)
# ===============================
def compute_offsets(job):
    'Funcion para calcular el offset de cada operacion de un trabajo job'
    'Requiere un objeto Job'
    'Devuelve una lista de offsets para cada operacion del trabajo'
    offsets = [0]
    total = 0
    for op in job.operations[:-1]:
        total += op.p
        offsets.append(total)
    return offsets

# ===============================
# BUSCAR PRIMER INICIO FACTIBLE
# ===============================
def find_start(job, machine_available, offsets):
    'Funcion para encontrar el start factible para cumplir No-Wait'
    'Requiere un objeto Job, lista con tiempo disponible de cada máquina y offsets del trabajo'
    'Devuelve el tiempo de inicio factible start para el trabajo'
    start = job.release
    while True:
        feasible = True
        max_required_start = job.release
        for k, op in enumerate(job.operations):
            machine = op.machine
            start_op = start + offsets[k]
            if start_op < machine_available[machine]:
                new_start = machine_available[machine] - offsets[k]
                max_required_start = max(max_required_start, new_start)
                feasible = False
        if feasible:
            return start
        start = max_required_start

# ===============================
# PROGRAMAR UN TRABAJO (NEH BASICO)
# ===============================
def schedule_job(job, machine_available, job_id, schedule):
    'Funcion para programar un trabajo job en el schedule'
    'Requiere un objeto Job, lista con tiempo disponible de máquinas, id del trabajo y lista del schedule'
    'Devuelve el tiempo de finalizacion del trabajo programado'
    offsets = compute_offsets(job)
    start = find_start(job, machine_available, offsets)
    completion = 0
    for k, op in enumerate(job.operations):
        machine = op.machine
        begin = start + offsets[k]
        final = begin + op.p
        machine_available[machine] = final
        schedule.append({
            "job": job_id,
            "machine": machine,
            "start": begin,
            "finish": final,
            "operation": k
        })
        completion = final
    return completion

# ===============================
# EVALUAR SECUENCIA (NEH BASICO)
# ===============================
def evaluate_sequence(sequence, jobs, m, save_schedule=False):
    'Funcion para evaluar una secuencia de trabajos y calcular total flow time'
    'Requiere una secuencia de trabajos, los objetos Jobs, numero de maquinas'
    'Devuelve el total flow time o (total flow time, schedule) si save_schedule es True'
    machine_available = [0]*m
    total_flow = 0
    schedule = []
    for j in sequence:
        Cj = schedule_job(jobs[j], machine_available, j, schedule)
        total_flow += Cj
    if save_schedule:
        return total_flow, schedule
    else:
        return total_flow

# ===============================
# HEURISTICA CONSTRUCTIVA NEH
# ===============================
def construct_solution(jobs, m):
    'Funcion principal para construir solucion con heuristica constructiva NEH'
    'Requiere los objetos Jobs y el numero de maquinas'
    'Devuelve una secuencia de trabajos construida'
    n = len(jobs)
    order = list(range(n))
    order.sort(
        key=lambda j: jobs[j].release + sum(op.p for op in jobs[j].operations)
    )
    sequence = []
    for j in order:
        best_pos = 0
        best_value = float("inf")
        for pos in range(len(sequence)+1):
            temp = sequence.copy()
            temp.insert(pos, j)
            value = evaluate_sequence(temp, jobs, m)
            if value < best_value:
                best_value = value
                best_pos = pos
        sequence.insert(best_pos, j)
    return sequence

# ===============================
# IMPRIMIR SCHEDULE
# ===============================
def print_schedule(schedule):
    'Funcion para imprimir el schedule completo de la secuencia construida'
    print("\nSCHEDULE COMPLETO\n")
    schedule.sort(key=lambda x: x["start"])
    for op in schedule:
        print(
            f"Job {op['job']} | "
            f"Op {op['operation']} | "
            f"Machine {op['machine']} | "
            f"Start {op['start']} | "
            f"Finish {op['finish']}"
        )
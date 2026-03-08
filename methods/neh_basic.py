import time

# ===============================
# ESTRUCTURAS DE DATOS (Para no trabajar con diccionarios)
# ===============================
class Operation: # Representa una operación de un trabajo con su máquina y tiempo de procesamiento
    def __init__(self, machine, processing_time):
        self.machine = machine
        self.p = processing_time

class Job: # Representa un trabajo con su lista de operaciones y su tiempo de release
    def __init__(self, operations, release):
        self.operations = operations
        self.release = release

# ===============================
# LECTURA DE INSTANCIAS
# ===============================
def read_instance(file):
    'Funcion para leer cada instancia del trabajo (Cada instancia se asume el mismo formato de Ansxo 2)'
    'Requiere el archivo file a leer'
    'Devuelve una lista de objetos Job y el número de máquinas (m)'
    with open(file) as f:
        # La primera línea contiene el número de trabajos (n) y el número de máquinas (m)
        n, m = map(int, f.readline().split()) 
        jobs = []
        # Las siguientes n líneas contienen la información de cada trabajo en pares de id_maquina y tiempo de procesamiento
        # La última entrada de cada línea es el tiempo de release del trabajo:
        for _ in range(n):
            data = list(map(int, f.readline().split()))
            operations = []
            # Se recorren los pares de id_maquina y tiempo de procesamiento para crear las operaciones del trabajo
            for i in range(0, 2*m, 2):
                machine = data[i]
                p = data[i+1]
                operations.append(Operation(machine, p))
            # El último valor de la línea es el tiempo de release del trabajo
            release = data[-1]
            # Se crea un objeto Job con su lista de operaciones y su tiempo de release, y se agrega a la lista de trabajos
            jobs.append(Job(operations, release))

    return jobs, m

# ===============================
# CALCULO DE OFFSETS (NO WAIT)
# ===============================
def compute_offsets(job):
    'Funcion para calcular el offset de cada operacion de un trabajo job (tiempo acumulado de cada operacion anterior)'
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
    'Funcion para encontrar el start factible para que todas las operaciones del trabajo se realicen cumpliendo No-Wait'
    'Requiere un objeto Job, una lista con el tiempo disponible de cada máquina y los tiempos de offsets del trabajo'
    'Devuelve el tiempo de inicio factible start para el trabajo'
    # Se asume el primer inicio posible como el tiempo de release del trabajo
    start = job.release
    # Se intenta verificar si el inicio es factible
    while True:
        feasible = True
        # Se inicializa el track del máximo conflicto encontrado (OPTIMIZACION 1)
        max_required_start = job.release
        # Se recorren TODAS las operaciones del trabajo verificando que todos los tiempos se puedan cumplir con el tiempo disponible de cada máquina
        for k, op in enumerate(job.operations):
            # Se obtiene la máquina de la operación
            machine = op.machine
            # Se calcula el tiempo de inicio de la operación (start + offset)
            start_op = start + offsets[k]
            # Precisamente si el tiempo calculado es menor al tiempo disponible no se puede realizar la operacion
            if start_op < machine_available[machine]:
                # Se calcula el nuevo start necesario para que esta operación sea factible
                new_start = machine_available[machine] - offsets[k]
                # Se actualiza el máximo requerido de TODAS las operaciones (OPTIMIZACION 1)
                max_required_start = max(max_required_start, new_start)
                # Se marca como no factible para reintentar
                feasible = False
                # NO hay break aquí: continuamos chequeando todas las operaciones
                # para encontrar el máximo conflicto correcto
        # Si el start es factible para todas las operaciones se devuelve el start
        if feasible:
            return start
        # En lugar de incrementar de 1 en 1, se salta directamente al valor máximo requerido (OPTIMIZACION 1)
        start = max_required_start

# ===============================
# PROGRAMAR UN TRABAJO
# ===============================
def schedule_job(job, machine_available, job_id, schedule):
    'Funcion para programar un trabajo job en el schedule'
    'Requiere un objeto Job, una lista con el tiempo disponible de cada máquina, el id del trabajo y la lista del schedule'
    'Devuelve el tiempo de finalizacion del trabajo programado'
    # Se calculan los offsets de cada operacion del trabajo
    # Se encuentra el start factible para el trabajo con los offsets y el tiempo disponible de cada máquina
    offsets = compute_offsets(job)
    start = find_start(job, machine_available, offsets)
    completion = 0
    # Se recorren las operaciones del trabajo programando cada una en el schedule y actualizando el tiempo disponible de cada máquina
    # Para cada operacion se calcula el tiempo de inicio y finalizacion
    # Se actualiza el tiempo disponible de la máquina al tiempo de finalizacion de la operacion
    # Se agrega la operacion al schedule con su información de job, máquina, tiempo de inicio, tiempo de finalizacion y número de operacion
    # Finalmente se devuelve el tiempo de finalizacion del trabajo programado (tiempo de finalizacion de la última operacion)
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
# EVALUAR SECUENCIA
# ===============================
def evaluate_sequence(sequence, jobs, m, save_schedule=False):
    'Funcion para evaluar una secuencia de trabajos programandolos en el schedule y calculando el total flow time (∑Cj) parcial de la posible insercion'
    'Requiere una secuencia de trabajos, los objetos Jobs, el numero de maquinas, y un booleano para indicar si se desea guardar el schedule completo'
    'Devuelve el total flow time (∑Cj) de la secuencia evaluada, y opcionalmente el schedule completo si save_schedule es True'
    # Se inicializa el tiempo disponible de cada máquina en 0, el total flow time en 0 y una lista vacía para el schedule
    machine_available = [0]*m
    total_flow = 0
    schedule = []
    # Para cada trabajo se calcula su tiempo de finalizacion Cj
    # Se recalcula el tiempo total del flujo
    for j in sequence:
        Cj = schedule_job(jobs[j], machine_available, j, schedule)
        total_flow += Cj
    # Si se desea guardar el schedule completo se devuelve el total flow time y el schedule, de lo contrario solo se devuelve el total flow time
    if save_schedule:
        return total_flow, schedule
    else:
        return total_flow

# ===============================
# HEURISTICA CONSTRUCTIVA
# ===============================
def construct_solution(jobs, m):
    'Funcion principal para construir la solucion con la heuristica constructiva NEH'
    'Requiere los objetos Jobs y el numero de maquinas'
    'Devuelve una secuencia de trabajos construida'
    # Se ordenan los trabajos por el criterio de release + suma de tiempos de procesamiento, de mayor a menor
    n = len(jobs)
    order = list(range(n))
    order.sort(
        key=lambda j: jobs[j].release + sum(op.p for op in jobs[j].operations)
    )
    # Se inicializa la secuencia vacia
    sequence = []
    # Para cada trabajo (en el orden previsto) se encuentra su mejor posicion de insercion en la secuencia actual
    # Para cada posible posicion se evalua la secuencia con el trabajo insertado y se guarda la mejor posicion (la que minimiza el total flow time)
    for j in order:
        # Se intentara insertar el trabajo desde la posición 0 hasta la posición len(sequence) (al final de la secuencia actual)
        best_pos = 0
        best_value = float("inf")
        # Se recorre cada posible posición de inserción del trabajo j en la secuencia actual
        for pos in range(len(sequence)+1):
            temp = sequence.copy()
            temp.insert(pos, j)
            value = evaluate_sequence(temp, jobs, m)
            # Si el valor obtenido es mejor que el mejor valor encontrado hasta ahora, se actualiza el mejor valor y la mejor posición
            if value < best_value:
                best_value = value
                best_pos = pos
        # Finalmente se inserta el trabajo j en la mejor posición encontrada en la secuencia
        sequence.insert(best_pos, j)

    return sequence

# ===============================
# IMPRIMIR SCHEDULE
# ===============================
def print_schedule(schedule):
    'Funcion para imprimir el schedule completo de la secuencia construida'
    print("\nSCHEDULE COMPLETO\n")
    # Se imprime el schedule por orden de tiempo de inicio de cada operacion
    schedule.sort(key=lambda x: x["start"])
    for op in schedule:
        print(
            f"Job {op['job']} | "
            f"Op {op['operation']} | "
            f"Machine {op['machine']} | "
            f"Start {op['start']} | "
            f"Finish {op['finish']}"
        )

import time
import os
import random
import pandas as pd

from methods.neh_basic import (
    read_instance,
    evaluate_sequence,
    print_schedule
)

from methods.neh_grasp import neh_grasp
from methods.neh_simple_noise import neh_simple_noise
from methods.neh_autores_taillard import neh_autores_taillard


# ==========================================
# CONFIGURACION DEL METODO
# ==========================================

METHOD_FILES = {
    "NEH_AUTORES_TAILLARD": "resultados\\NWJSSP_OADG_NEH(constructive).xlsx",
    "NEH_SIMPLE_NOISE": "resultados\\NWJSSP_OADG_NEH(simple_noise).xlsx",
    "NEH_GRASP": "resultados\\NWJSSP_OADG_NEH(GRASP).xlsx",
}

# Parametros globales
GROUP_SIZE = 3
SEED = 42

NOISE_RATIO = 0.3

GRASP_ITERATIONS = 100
GRASP_ALPHA = 0.2


# ===============================
# INSTANCIAS
# ===============================

instances = [
"ft06.txt","ft06r.txt","ft10.txt","ft10r.txt","ft20.txt","ft20r.txt",
"tai_j10_m10_1.txt","tai_j10_m10_1r.txt",
"tai_j100_m10_1.txt","tai_j100_m10_1r.txt",
"tai_j100_m100_1.txt","tai_j100_m100_1r.txt",
"tai_j1000_m10_1.txt","tai_j1000_m10_1r.txt",
"tai_j1000_m100_1.txt","tai_j1000_m100_1r.txt",
"tai_j1000_m1000_1.txt","tai_j1000_m1000_1r.txt"
]


# ==========================================
# UTILIDADES DE INPUT
# ==========================================

def ask_int(prompt, min_value=None):
    while True:
        v = input(prompt).strip()
        if v.lstrip("-").isdigit():
            v = int(v)
            if min_value is None or v >= min_value:
                return v
        print("Valor inválido.")


def ask_float(prompt, min_value=None, max_value=None):
    while True:
        try:
            v = float(input(prompt))
            if (min_value is None or v >= min_value) and (max_value is None or v <= max_value):
                return v
        except:
            pass
        print("Valor inválido.")


def ask_yes_no(prompt):
    while True:
        v = input(prompt).lower().strip()
        if v in ("s"):
            return True
        if v in ("n"):
            return False
        print("Respuesta inválida.")


# ==========================================
# SELECCION DE METODO
# ==========================================

def choose_method():

    print("\nMetodo a usar:")
    print("1) NEH constructivo (autores + Taillard)")
    print("2) NEH simple noise")
    print("3) NEH GRASP")

    opt = ask_int("Selecciona: ")

    if opt == 1:
        return "NEH_AUTORES_TAILLARD"
    if opt == 2:
        return "NEH_SIMPLE_NOISE"
    if opt == 3:
        return "NEH_GRASP"

    raise ValueError("Metodo inválido")


# ==========================================
# CONFIGURACION DE PARAMETROS
# ==========================================
def configure_parameters(method):
    global GROUP_SIZE, SEED
    global NOISE_RATIO
    global GRASP_ITERATIONS, GRASP_ALPHA

    print("\nParametros actuales:")

    print("GROUP_SIZE =", GROUP_SIZE)

    if method == "NEH_SIMPLE_NOISE":
        print("NOISE_RATIO =", NOISE_RATIO)
        print("SEED =", SEED)

    if method == "NEH_GRASP":
        print("GRASP_ITERATIONS =", GRASP_ITERATIONS)
        print("SEED =", SEED)
        print("GRASP_ALPHA =", GRASP_ALPHA)

    if not ask_yes_no("\nCambiar parametros? (s/n): "):
        return

    GROUP_SIZE = ask_int("Nuevo GROUP_SIZE: ",1)

    if method == "NEH_SIMPLE_NOISE":

        NOISE_RATIO = ask_float("Nuevo NOISE_RATIO: ",0)
        SEED = ask_int("Nueva SEED: ")

    if method == "NEH_GRASP":

        GRASP_ITERATIONS = ask_int("Nuevo GRASP_ITERATIONS: ",1)
        SEED = ask_int("Nueva SEED: ")
        GRASP_ALPHA = ask_float("Nuevo GRASP_ALPHA (0-1): ",0,1)


# ==========================================
# SELECCION DE INSTANCIAS
# ==========================================
def choose_instances():
    print("\nModo de ejecución")
    print("1) Correr hasta instancia k")
    print("2) Correr una sola instancia")

    mode = ask_int("Selecciona: ")

    if mode == 1:
        for i,x in enumerate(instances,1):
            print(i,x)
        k = ask_int("Elegir k: ",1)
        return instances[:k], False
    if mode == 2:
        for i,x in enumerate(instances,1):
            print(i,x)
        idx = ask_int("Elegir instancia: ",1)
        report = ask_yes_no("Mostrar schedule completo? (s/n): ")
        return [instances[idx-1]], report
    
    raise ValueError("Modo inválido")


# ==========================================
# SOLVER
# ==========================================
def solve_instance(inst, method):
    file = "NWJSSP Instances\\" + inst
    jobs, m = read_instance(file)
    start_time = time.time()
    if method == "NEH_AUTORES_TAILLARD":
        sequence = neh_autores_taillard(jobs, m, F=GROUP_SIZE)
    elif method == "NEH_SIMPLE_NOISE":
        if SEED is not None:
            random.seed(SEED)
        sequence = neh_simple_noise(
            jobs, m,
            F=GROUP_SIZE,
            noise_ratio=NOISE_RATIO
        )
    elif method == "NEH_GRASP":
        sequence, best_cost, history = neh_grasp(
            jobs, m,
            F=GROUP_SIZE,
            num_iterations=GRASP_ITERATIONS,
            seed=SEED,
            alpha=GRASP_ALPHA
        )
    total_flow, schedule = evaluate_sequence(sequence, jobs, m, True)
    compute_time_ms = round((time.time() - start_time)*1000)
    n = len(jobs)
    job_start_times = [None]*n
    for op in schedule:
        if op["operation"] == 0:
            job_start_times[op["job"]] = op["start"]

    return total_flow, compute_time_ms, job_start_times, schedule

# ==========================================
# EXPORTAR RESULTADOS
# ==========================================
def write_results_to_excel(method, results):
    output_file = METHOD_FILES[method]
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    if os.path.exists(output_file):
        writer_kwargs = dict(
            engine="openpyxl",
            mode="a",
            if_sheet_exists="replace"
        )
    else:
        writer_kwargs = dict(
            engine="openpyxl",
            mode="w"
        )
    with pd.ExcelWriter(output_file, **writer_kwargs) as writer:
        for name, data in results.items():
            total_flow, compute_time_ms, job_start_times = data
            df = pd.DataFrame([
                [total_flow, compute_time_ms],
                job_start_times
            ])
            df.to_excel(writer, sheet_name=name, header=False, index=False)
    print("\nArchivo actualizado:", output_file)


# ==========================================
# MAIN
# ==========================================

def main():
    method = choose_method()
    configure_parameters(method)
    selected_instances, report_schedule = choose_instances()
    print("\nResumen:")
    print("Metodo:", method)
    print("Instancias:", len(selected_instances))
    results = {}
    for inst in selected_instances:
        total_flow, compute_time_ms, job_start_times, schedule = solve_instance(inst, method)
        results[inst.replace(".txt","")] = (
            total_flow,
            compute_time_ms,
            job_start_times
        )
        print(f"[OK] {inst} | Z={total_flow} | tiempo={compute_time_ms} ms")
        if report_schedule:
            print_schedule(schedule)
    write_results_to_excel(method, results)


if __name__ == "__main__":
    main()
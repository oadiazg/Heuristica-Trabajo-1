import time
import pandas as pd
from methods.neh_basic import (
    read_instance,
    construct_solution,
    evaluate_sequence,
    print_schedule
)

from methods.neh_simple_noise import neh_simple_noise
from methods.neh_autores_taillard import neh_autores_taillard

# ==========================================
# CONFIGURACION DEL METODO
# ==========================================
METHOD = "NEH_BASIC"              # Versión básica original
#METHOD = "NEH_AUTORES_TAILLARD"  # Versión optimizada (MÁS RÁPIDA)
#METHOD = "NEH_SIMPLE_NOISE"  # Versión simple aleatorizada
GROUP_SIZE = 3
NOISE_RATIO = 0.3  # ±30% de ruido

# ===============================
# INSTANCIAS
# ===============================
instances = [
"ft06.txt",
"ft06r.txt",
"ft10.txt",
"ft10r.txt",
"ft20.txt",
"ft20r.txt",
"tai_j10_m10_1.txt",
"tai_j10_m10_1r.txt",
"tai_j100_m10_1.txt",
"tai_j100_m10_1r.txt",
"tai_j100_m100_1.txt",
"tai_j100_m100_1r.txt",
"tai_j1000_m10_1.txt",
"tai_j1000_m10_1r.txt",
"tai_j1000_m100_1.txt",
"tai_j1000_m100_1r.txt",
"tai_j1000_m1000_1.txt",
"tai_j1000_m1000_1r.txt"
]


def ask_execution_mode():
    """Devuelve 'all' para todas las instancias o 'single' para una sola."""
    while True:
        print("\nModo de ejecucion:")
        print("1) Correr todas las instancias y exportar .xlsx")
        print("2) Correr una sola instancia")
        opt = input("Selecciona 1 o 2: ").strip()
        if opt == "1":
            return "all"
        if opt == "2":
            return "single"
        print("Opcion no valida. Intenta nuevamente.")


def ask_report_mode():
    """Devuelve True si se debe imprimir el schedule completo."""
    while True:
        print("\nNivel de reporte:")
        print("1) Solo Z y tiempo de computo")
        print("2) Z, tiempo de computo y schedule completo")
        opt = input("Selecciona 1 o 2: ").strip()
        if opt == "1":
            return False
        if opt == "2":
            return True
        print("Opcion no valida. Intenta nuevamente.")


def ask_single_instance():
    """Permite elegir una unica instancia desde la lista disponible."""
    while True:
        print("\nInstancias disponibles:")
        for idx, name in enumerate(instances, start=1):
            print(f"{idx}) {name}")

        raw = input("Elige numero de instancia o nombre exacto del archivo: ").strip()

        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(instances):
                return instances[idx - 1]

        if raw in instances:
            return raw

        print("Instancia no valida. Intenta nuevamente.")


def solve_instance(inst):
    """Ejecuta una instancia y retorna total_flow, tiempo_ms, start_times y schedule."""
    file = "NWJSSP Instances\\" + inst
    jobs, m = read_instance(file)

    start_time = time.time()  # Se inicia el tiempo de computo

    # Se obtiene la secuencia de trabajos construida con la heuristica escogida
    if METHOD == "NEH_BASIC":
        sequence = construct_solution(jobs, m)
    elif METHOD == "NEH_AUTORES_TAILLARD":
        sequence = neh_autores_taillard(jobs, m, F=GROUP_SIZE)
    elif METHOD == "NEH_SIMPLE_NOISE":
        sequence = neh_simple_noise(jobs, m, noise_ratio=NOISE_RATIO)
    else:
        raise ValueError("Metodo no reconocido")

    total_flow, schedule = evaluate_sequence(sequence, jobs, m, True)
    end_time = time.time()  # Se finaliza el tiempo de computo

    # Calcular tiempos de inicio de cada job
    n = len(jobs)
    job_start_times = [None] * n
    for op in schedule:
        j = op["job"]
        if op["operation"] == 0:
            job_start_times[j] = op["start"]

    compute_time_ms = round((end_time - start_time) * 1000)
    return total_flow, compute_time_ms, job_start_times, schedule

# ===============================
# MAIN
# ===============================
def main():
    'Funcion principal para ejecutar la heuristica constructiva en una instancia dada'
    run_mode = ask_execution_mode()
    report_schedule = ask_report_mode()

    if run_mode == "single":
        inst = ask_single_instance()
        total_flow, compute_time_ms, _, schedule = solve_instance(inst)
        print(
            f"\n[OK] Instancia {inst} terminada | "
            f"Z = {total_flow} | "
            f"Tiempo = {compute_time_ms} ms"
        )
        if report_schedule:
            print_schedule(schedule)
        return

    # Modo 'all': guardar resultados para exportar al final
    results = {}
    for inst in instances:
        total_flow, compute_time_ms, job_start_times, schedule = solve_instance(inst)
        results[inst.replace(".txt", "")] = (total_flow, compute_time_ms, job_start_times)

        print(
            f"[OK] Instancia {inst} terminada | "
            f"Z = {total_flow} | "
            f"Tiempo = {compute_time_ms} ms"
        )

        if report_schedule:
            print_schedule(schedule)

    # Crear archivo Excel final solo cuando se corren todas las instancias
    output_file = "resultados\\NWJSSP_OADG_NEH(BB).xlsx"
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for name, data in results.items():
            total_flow, compute_time_ms, job_start_times = data
            row1 = [total_flow, compute_time_ms]
            row2 = job_start_times
            df = pd.DataFrame([row1, row2])
            df.to_excel(writer, sheet_name=name, header=False, index=False)

    print("\nArchivo Excel generado:", output_file)


if __name__ == "__main__":
    main()
"""
Implementación de GRASP (Greedy Randomized Adaptive Search Procedure) para NWJSSP.

GRASP tiene 2 fases por iteración:
1. FASE CONSTRUCTIVA ALEATORIA: construir solución inicial con restricción aleatoria
2. FASE DE MEJORA LOCAL: mejorar con búsqueda local

En nuestro caso:
1. Fase constructiva: neh_autores_taillard pero con perturbación aleatoria de orden
2. Fase de mejora: búsqueda local 2-opt simple
3. Iteración: repetir num_iterations veces, guardar mejor
"""
import random
from methods.neh_autores_taillard import (
    neh_autores_taillard,
    sort_jobs_by_priority,
    best_insertion_single_taillard,
    insert_group_best_position_taillard
)
from auxiliar.branch_and_bound import best_group_order
from auxiliar.taillard import compute_completion_time_nwjssp
from methods.neh_basic import compute_offsets

# ==========================================
# FASE CONSTRUCTIVA ALEATORIZADA
# ==========================================
def construct_randomized(jobs, m, F=2, alpha=0.2, offsets_cache=None):
    '''Construcción aleatoria para GRASP: modifica el orden inicial aleatorialmente'''
    '''Requiere jobs, numero de maquinas, tamaño de grupo F, y parámetro alpha de aleatoriedad'''
    '''Devuelve una secuencia de trabajos construida de forma aleatoria'''
    
    n = len(jobs)
    if offsets_cache is None:
        offsets_cache = {}
        for job_idx in range(n):
            offsets_cache[job_idx] = compute_offsets(jobs[job_idx])
    
    # PASO 1: Obtener orden de prioridad inicial (determinista)
    Js = sort_jobs_by_priority(jobs)
    
    # PASO 2: PERTURBAR el orden aleatoriamente (esto hace que sea diferente cada vez)
    # alpha controla cuánto aleatoriedad: 0 = nada aleatorio, 1 = muy aleatorio
    num_to_shuffle = max(1, int(len(Js) * alpha))
    shuffle_indices = random.sample(range(len(Js)), num_to_shuffle)
    for idx in shuffle_indices:
        swap_idx = random.randint(0, len(Js) - 1)
        Js[idx], Js[swap_idx] = Js[swap_idx], Js[idx]
    
    # PASO 3: Construir solución con el orden perturbado usando neh_autores_taillard
    sequence = []
    
    while len(Js) >= F:
        if sequence:
            current_cost = compute_completion_time_nwjssp(sequence, jobs, m, offsets_cache)
        else:
            current_cost = 0
        
        j = Js[0]
        job = jobs[j]
        from methods.neh_autores_taillard import get_job_processing_cost
        cost_job_new = get_job_processing_cost(job)
        
        pos, new_cost = best_insertion_single_taillard(sequence, j, jobs, m, offsets_cache)
        
        # Criterio determinista (no ruidoso en construcción aleatoria)
        if len(sequence) == 0 or new_cost <= current_cost + cost_job_new:
            sequence.insert(pos, j)
            Js.pop(0)
        else:
            group = Js[:F]
            best_order = best_group_order(sequence, group, jobs, m, use_taillard=True, offsets_cache=offsets_cache)
            
            if best_order is None:
                for job_idx in group:
                    best_pos, _ = best_insertion_single_taillard(sequence, job_idx, jobs, m, offsets_cache)
                    sequence.insert(best_pos, job_idx)
                Js = Js[F:]
            else:
                best_seq, best_cost = insert_group_best_position_taillard(
                    sequence, best_order, jobs, m, offsets_cache
                )
                sequence = best_seq
                Js = Js[F:]
    
    # Insertar trabajos restantes
    for j in Js:
        best_pos, _ = best_insertion_single_taillard(sequence, j, jobs, m, offsets_cache)
        sequence.insert(best_pos, j)
    
    return sequence

# ==========================================
# BUSQUEDA LOCAL 2-OPT SIMPLE
# ==========================================
def local_search_2opt_simple(sequence, jobs, m, offsets_cache=None):
    '''Búsqueda local 2-opt: intenta intercambiar pares de trabajos'''
    '''Requiere secuencia, jobs, numero de maquinas, y opcionalmente cache de offsets'''
    '''Devuelve secuencia mejorada y su costo'''
    
    if not sequence or len(sequence) < 2:
        return sequence, compute_completion_time_nwjssp(sequence, jobs, m, offsets_cache)
    
    if offsets_cache is None:
        offsets_cache = {}
        for job_idx in range(len(jobs)):
            offsets_cache[job_idx] = compute_offsets(jobs[job_idx])
    
    current_sequence = sequence.copy()
    current_cost = compute_completion_time_nwjssp(current_sequence, jobs, m, offsets_cache)
    
    improved = True
    max_its = 20  # Máximo de iteraciones de mejora
    its = 0
    
    while improved and its < max_its:
        improved = False
        its += 1
        n = len(current_sequence)
        
        for i in range(n):
            for j in range(i + 2, n):  # j debe estar al menos 2 posiciones después de i
                # Intercambiar segmento [i+1, j]
                new_sequence = current_sequence.copy()
                new_sequence[i+1:j+1] = reversed(new_sequence[i+1:j+1])
                
                new_cost = compute_completion_time_nwjssp(new_sequence, jobs, m, offsets_cache)
                
                if new_cost < current_cost:
                    current_sequence = new_sequence
                    current_cost = new_cost
                    improved = True
                    break
            
            if improved:
                break
    
    return current_sequence, current_cost

# ==========================================
# GRASP
# ==========================================
def neh_grasp(jobs, m, F=2, num_iterations=10, seed=None, alpha=0.2):
    '''Implementa GRASP correctamente: construcción aleatoria + búsqueda local'''
    '''GRASP realiza num_iterations iteraciones de (construcción aleatoria + 2-opt)'''
    '''Requiere jobs, numero de maquinas, tamaño grupo F'''
    '''num_iterations: número de iteraciones (por defecto 10)'''
    '''seed: semilla para reproducibilidad'''
    '''alpha: parámetro de aleatoriedad en construcción (0-1, por defecto 0.2)'''
    '''Devuelve mejor secuencia, costo, e historial'''
    
    if seed is not None:
        random.seed(seed)
    
    # Precalcular offsets
    offsets_cache = {}
    for job_idx in range(len(jobs)):
        offsets_cache[job_idx] = compute_offsets(jobs[job_idx])
    
    best_sequence = None
    best_cost = float("inf")
    iteration_history = []
    
    print(f"\n  [GRASP] Iniciando {num_iterations} iteraciones...")
    
    for iteration in range(num_iterations):
        # ===============================================
        # FASE 1: CONSTRUCCIÓN ALEATORIA
        # ===============================================
        construction_sequence = construct_randomized(jobs, m, F=F, alpha=alpha, offsets_cache=offsets_cache)
        construction_cost = compute_completion_time_nwjssp(construction_sequence, jobs, m, offsets_cache)
        
        # ===============================================
        # FASE 2: BÚSQUEDA LOCAL
        # ===============================================
        improved_sequence, improved_cost = local_search_2opt_simple(
            construction_sequence,
            jobs,
            m,
            offsets_cache
        )
        
        # Guardar historial
        iteration_history.append({
            'iteration': iteration + 1,
            'construction_cost': construction_cost,
            'improved_cost': improved_cost,
            'improvement': construction_cost - improved_cost,
            'sequence': improved_sequence.copy()
        })
        
        # Actualizar mejor
        if improved_cost < best_cost:
            best_cost = improved_cost
            best_sequence = improved_sequence.copy()
            # print(f"    Iter {iteration + 1}: Z = {improved_cost} ✓ (mejora: {construction_cost - improved_cost})")
        else:
            # print(f"    Iter {iteration + 1}: Z = {improved_cost}")
            pass
    
    print(f"  [GRASP] Mejor solución encontrada: Z = {best_cost}\n")
    
    return best_sequence, best_cost, iteration_history
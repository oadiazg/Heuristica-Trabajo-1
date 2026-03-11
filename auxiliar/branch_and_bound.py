"""
Branch and Bound optimizado para encontrar el mejor orden de un grupo de trabajos.
Incorpora caching de offsets y evaluación eficiente.
"""
from auxiliar.taillard import compute_completion_time_nwjssp
from methods.neh_basic import evaluate_sequence

# ==========================================
# BRANCH AND BOUND PARA ORDENAR GRUPO
# ==========================================
def best_group_order(sequence, group, jobs, m, use_taillard=False, offsets_cache=None):
    'Funcion para encontrar el mejor orden de los trabajos del grupo usando Branch & Bound'
    'Requiere secuencia actual, grupo de trabajos a ordenar, jobs, numero de maquinas, flag use_taillard, y opcionalmente cache de offsets'
    'Devuelve el mejor orden del grupo encontrado'
    if not group:
        return None
    best_order = None
    best_value = float("inf")
    def branch(partial, remaining):
        'Función recursiva que implementa Branch & Bound con poda'
        'Requiere solución parcial y trabajos restantes a asignar'
        nonlocal best_order, best_value
        if not remaining:
            temp = sequence + partial
            if use_taillard:
                value = compute_completion_time_nwjssp(temp, jobs, m, offsets_cache)
            else:
                value = evaluate_sequence(temp, jobs, m)
            if value < best_value:
                best_value = value
                best_order = partial.copy()
            return
        for j in remaining:
            new_partial = partial + [j]
            temp = sequence + new_partial
            if use_taillard:
                bound = compute_completion_time_nwjssp(temp, jobs, m, offsets_cache)
            else:
                bound = evaluate_sequence(temp, jobs, m)
            if bound >= best_value:
                continue
            new_remaining = remaining.copy()
            new_remaining.remove(j)
            branch(new_partial, new_remaining)
    branch([], group)
    return best_order
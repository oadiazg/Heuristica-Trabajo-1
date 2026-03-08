"""
Branch and Bound para encontrar el mejor orden de un grupo de trabajos.

Optimizaciones:
- Usar offsets precalculados (OPTIMIZACION 4)
"""

from methods.neh_basic import evaluate_sequence
from auxiliar.taillard import compute_completion_time_nwjssp


# ==========================================
# BRANCH AND BOUND PARA ORDENAR GRUPO
# ==========================================

def best_group_order(sequence, group, jobs, m, use_taillard=False, offsets_cache=None):
    '''Funcion para encontrar el mejor orden de los trabajos del grupo usando Branch & Bound'''
    '''Incorpora OPTIMIZACION 4: Usar offsets precalculados'''
    '''Requiere la secuencia actual, el grupo de trabajos, los objetos Job, numero de maquinas, flag use_taillard, y opcionalmente cache de offsets'''
    '''Devuelve el mejor orden del grupo encontrado'''
    # Se valida que el grupo no esté vacío (si está vacío no hay nada que ordenar)
    if not group:
        return None
    # Se inicializan variables para guardar el mejor orden y el mejor valor encontrados
    best_order = None
    best_value = float("inf")
    # ======================================
    # BUSQUEDA RECURSIVA CON PODA
    # ======================================
    def branch(partial, remaining):
        '''Función recursiva que implementa Branch & Bound'''
        '''Requiere una solución parcial y los trabajos restantes a asignar'''
        '''Actualiza best_order y best_value globales si encuentra mejores soluciones'''
        nonlocal best_order, best_value
        # Si no quedan trabajos, se ha completado una solución completa del grupo
        if not remaining:
            # Se crea la secuencia completa: secuencia actual + orden parcial encontrado
            temp = sequence + partial
            # Se evalúa el costo de esta secuencia completa
            if use_taillard:
                # Si se usa la evaluación optimizada de Taillard con cache de offsets
                value = compute_completion_time_nwjssp(temp, jobs, m, offsets_cache)
            else:
                # Si se usa la evaluación estándar
                value = evaluate_sequence(temp, jobs, m)
            # Si el valor obtenido es mejor que el mejor encontrado hasta ahora, se actualiza
            if value < best_value:
                best_value = value
                best_order = partial.copy()
            # Se retorna de la llamada recursiva
            return
        # Expandir nodo: Se intenta agregar cada trabajo restante a la solución parcial
        for j in remaining:
            # Se agrega el trabajo j a la solución parcial
            new_partial = partial + [j]
            # Se calcula un bound (cota) para podar el árbol de búsqueda
            temp = sequence + new_partial
            # Se evalúa el costo de la solución parcial
            if use_taillard:
                # Si se usa la evaluación optimizada de Taillard con cache de offsets
                bound = compute_completion_time_nwjssp(temp, jobs, m, offsets_cache)
            else:
                # Si se usa la evaluación estándar
                bound = evaluate_sequence(temp, jobs, m)
            # Si el bound es igual o mayor que el mejor valor encontrado, se poda esta rama
            # (ya que cualquier extensión de esta rama tendrá costo >= bound)
            if bound >= best_value:
                continue
            # Se crean los trabajos restantes después de agregar j
            new_remaining = remaining.copy()
            new_remaining.remove(j)
            # Se hace una llamada recursiva para expandir más el árbol con el nuevo trabajo agregado
            branch(new_partial, new_remaining)
    # Se lanza la búsqueda recursiva comenzando con una solución parcial vacía
    # y todos los trabajos del grupo como trabajos restantes
    branch([], group)
    # Se devuelve el mejor orden del grupo encontrado
    return best_order
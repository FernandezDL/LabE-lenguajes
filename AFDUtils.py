import time

def keyFromValue(equivalents, search_value):
    """
    Funcion que busca una llave dentro de un diccionario
    :param equivalents: Diccionario a escarvar
    :param search_value: Valor a buscar
    :return:
    - Llave del diccionario donde se encuentra el valor
    - [] si el valor no existe dentro del diccionario
    """
    for key, value in equivalents.items():
        if value == search_value:
            return key
    return []


def move(s, c, transitions):
    """
        Funcion para moverse dentro de las transiciones
        :param s: Estado esperado
        :param c: Simbolo a buscar
        :param transitions: Diccionario de transiciones
        :return:
        - Estado destino de la transicione del estado s con el simbolo c
        """
    for state, transitions in transitions.items():
        if s == state:
            destiny = transitions.get(c, None)
            return destiny if destiny and len(destiny) > 0 else None


def simulateDFA(string, initialState, finalStates, transitions):
    """
    Metodo que simula un Automata Finito Determinista
    :param string: Cadena a simular
    :param initialState: Estado inicial del automata
    :param finalStates: Estados finales o de aceptacion del automata
    :param transitions: Diccionario de transiciones del automata
    :return:
    - Booleano si la cadena es aceptada por el automata
    - String del tiempo que tomo simular el automata
    """
    inicio = time.time()
    currState = initialState

    if string != "ε":
        for char in string:
            # time.sleep(1)
            if char == "ε":
                continue
            currState = move(s=currState, c=str(ord(char)), transitions=transitions)
            if currState is None:
                fin = time.time()
                return False, "{:.2e}".format(fin - inicio)

    fin = time.time()
    return currState in finalStates, "{:.2e}".format(fin - inicio)

def step(char, currState, transitions):
    return transitions.get(currState).get(str(char), None) if transitions.get(currState, None) else None
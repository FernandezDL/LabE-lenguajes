import json
from pythomata import SimpleDFA
from AFDUtils import keyFromValue, simulateDFA

ESTADOS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


class tempNFA(object):
    def __init__(self, filename):
        """
        Funcion constructora de la clase tempNFA, esta clase se utiliza para matener el automata finito no determinista
        que será convertido en automata finito determinista.
        :param filename:
        """
        with open(filename, "r", encoding="utf-8") as json_file:
            afn = json.load(json_file)

        self.states = afn["estados"]
        self.alphabet = afn["alfabeto"]
        self.initialState = afn["estadoInicial"]
        self.finalStates = afn["estadosFinales"]
        self.transitions = afn["transiciones"]


class AFD(object):
    def __init__(self, afnFilename):
        """
        Funcion constructa de la clase AFD, esta inicializa las variables a utilizar durante el funcionamiento de
        la construccion del AFD.
        :param afnFilename: Nombre del archivo donde se encuentra el AFN, se espera un archivo .json
        """
        self.afn = tempNFA(filename=afnFilename)

        self.states = []
        self.alphabet = self.afn.alphabet
        self.initialState = self.afn.initialState
        self.finalStates = []
        self.transitions = dict()
        self.equivalents = dict()

        if "ε" in self.alphabet:
            self.alphabet.remove("ε")

        self.NFAtoDFA()

    def epsilon_closure(self, states):
        """
        Funcion que crea la cerradura epsilon para los estados del AFN que contengan una transicion epsilon.
        :param states: Lista de estados
        :return: Lista de estados de la cerradura epsilon.
        """
        stack, cerradura = set(states), set(states)

        while len(stack) != 0:
            t = stack.pop()

            if t in self.afn.transitions and "ε" in self.afn.transitions[t]:
                for u in self.afn.transitions[t]["ε"]:
                    if u not in cerradura:
                        stack.add(u)
                        cerradura.add(u)

        cerradura = list(cerradura)
        return cerradura

    def moveTo(self, estados, symbol):
        """
        Metodo para moverse dentro de estados dependiendo del simbolo de entrada
        :param estados: Lista de estados
        :param symbol: Simbolo de entrada
        :return:
        - alcanzables: Lista de estados alcanzables por el simbolo de entrada
        """
        alcanzables = []

        for estado in estados:
            if estado in self.afn.transitions and symbol in self.afn.transitions[estado]:
                for transition in self.afn.transitions[estado][symbol]:
                    alcanzables.append(transition)

        return alcanzables

    def subsetConstruction(self):
        """
        Funcion que ejecuta la construccion por subconjuntos del AFN para crear el AFD. Utiliza los estados, pasando
        estos por la cerradura epsilon y luego desarrollando las transiciones entre los estados.
        """
        Dstates = [self.epsilon_closure([self.afn.initialState])]
        markStates = []
        states = []
        transitions = dict()

        while len(Dstates) != 0:
            T = Dstates.pop()

            if len(T) != 0:
                states.append(T)
                markStates.append(T)
                for symbol in self.alphabet:
                    u = self.epsilon_closure(self.moveTo(T, symbol))
                    if u not in Dstates and u not in markStates:
                        Dstates.append(u)

                    if tuple(T) in transitions:
                        transitions[tuple(T)][symbol] = list(u)
                    else:
                        transitions.update({tuple(T): {symbol: list(u)}})

        def generate_state_names(n):
            alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            state_names = []
            for i in range(n):
                quotient, remainder = divmod(i, len(alphabet))
                name = ""
                if quotient > 0:
                    name += alphabet[quotient - 1]
                name += alphabet[remainder]
                state_names.append(name)
            return state_names

        # Uso de la función
        self.states = generate_state_names(len(states))
        self.equivalents = {self.states[i]: states[i] for i in range(len(states))}
        final = [state for state in states for final in self.afn.finalStates if final in state]
        self.finalStates = [self.states[states.index(state)] for state in final]
        self.transitions = self.translateTransitions(transitions)
        self.initialState = [self.states[states.index(state)] for state in states if self.afn.initialState in state]

    def translateTransitions(self, transitions):
        """
        Funcion que toma las transiciones de un estado del AFN y retorna un diccionario con las nuevas transiciones
        del estado.
        :param transitions: Diccionario con las transiciones de un estado del AFN
        :return:
        - new_tramsitions : Diccionario con las transcisiones para el estado del AFD.
        """
        new_transitions = {}
        for key, value in self.equivalents.items():
            value = tuple(value)
            new_transitions[key] = {}
            for state, transitions_dict in transitions.items():
                if value == state:
                    [new_transitions[key].update(
                        {symbol: keyFromValue(equivalents=self.equivalents, search_value=value)}) for symbol, value in
                     transitions_dict.items()]
        return new_transitions

    def keyFromValue(self, search_value):
        """
        Metodo que recorre el diccionario de equivalentes para encontrar un valor dentro de los valores del diccionario
        :param search_value: Valor a buscar
        :return:
        - Llave del diccionario en el valor encontrado
        - [] se retorna si no se encuentra en valor en el diccionario de equivalentes.
        """
        for key, value in self.equivalents.items():
            if value == search_value:
                return key
        return []

    def writeJSONAFD(self):
        """
        Metodo que convierte en AFD en un archivo .json
        """
        afd = {
            "estados": self.states,
            "alfabeto": self.alphabet,
            "estadoInicial": self.initialState,
            "estadosFinales": self.finalStates,
            "transiciones": self.transitions,
            "equivalencias": self.equivalents
        }
        with open('./bin/lib/afd/afd.json', 'w') as outfile:
            json.dump(afd, outfile, indent=6)

    def graphDFA(self):
        """
        Metodo que grafica el AFD utilizando las librerias de Graphviz, genera un arhivo .svg con una leyenda.
        """
        alphabet = set(self.alphabet)
        states = set(self.transitions.keys())
        initial_state = self.initialState[0]
        accepting_states = set(self.finalStates)

        transition_function = dict()
        for currState, transitions in self.transitions.items():
            for symbol, destiny in transitions.items():
                if len(destiny) != 0:
                    if currState in transition_function:
                        transition_function[currState].update({symbol: destiny})
                    else:
                        transition_function.update({currState: {symbol: destiny}})

        dfa = SimpleDFA(states, alphabet, initial_state, accepting_states, transition_function)

        graph = dfa.trim().to_graphviz()

        legend = "\n".join([f"{key} = {value}" for key, value in self.equivalents.items()])
        legend = f"Equivalencias:\n{legend}"
        graph.attr(label=legend)

        graph.attr(rankdir='LR')
        graph.render("./bin/lib/afd/DFA", view=True)

    def NFAtoDFA(self):
        """
        Metodo que construye el AFD desde el AFN establecido al inicializar la clase Afd.
        """
        self.subsetConstruction()
        self.writeJSONAFD()
        self.graphDFA()

    def simulateDFA(self, string):
        """
        Metodo que prepara el AFD para ser simulado.
        :param string: Cadena a simular
        :return:
        - Metodo de simulacion simulateDFA del AFDUtils con los valores para el estado inicial, los estados
          de aceptacion y las transiciones del AFD
        """
        return simulateDFA(string=string, initialState=self.initialState[0], finalStates=self.finalStates,
                           transitions=self.transitions)

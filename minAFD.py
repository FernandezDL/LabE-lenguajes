import json
from pythomata import SimpleDFA
from afd import keyFromValue, simulateDFA


class tempDFA(object):
    def __init__(self, filename):
        """
        Funcion inicializadora de la clase tempDFA, este mantiene los datos del AFD a minimizar
        :param filename: Nombre del archivo donde estan los componentes del AFD
        """
        with open(filename, "r", encoding="utf-8") as json_file:
            afd = json.load(json_file)

        self.states = afd["estados"]
        self.alphabet = afd["alfabeto"]
        self.initialState = afd["estadoInicial"]
        self.finalStates = afd["estadosFinales"]
        self.transitions = afd["transiciones"]
        self.equivalents = afd["equivalencias"]


class minAfd(object):
    def __init__(self, afdFilename):
        """
        Funcion inicializadora de la clase minAFD, esta clase se encarga de crear un automata finito determinista
        minimizado en base a un automata finito determinista creado por el método de subconjuntos.
        :param afdFilename: Nombre del archivo .json donde estan los componentes del AFD a minimizar.
        """
        self.afd = tempDFA(filename=afdFilename)

        self.states = []
        self.alphabet = self.afd.alphabet
        self.initialState = ""
        self.finalStates = []
        self.transitions = dict()
        self.equivalents = dict()

        self.DFAtominDFA()

    def deleteUnreachableStates(self):
        """
        Funcion que elimina estado inalcanzables por el AFD
        """
        reachable = [self.afd.initialState[0]]
        for currState in self.afd.states:
            for symbol, destiny in self.afd.transitions[currState].items():
                if destiny not in reachable and len(destiny) != 0:
                    reachable.append(destiny)

        reachable.sort()
        self.afd.states = reachable

    def updateTransitions(self):
        """
        Funcion que actualiza las transiciones de los estados despues de eliminar los estados inalcanzables.
        """
        newTransitions = dict()
        for currState, transitions in self.afd.transitions.items():
            if currState in self.afd.states:
                for symbol, destiny in transitions.items():
                    if currState in self.afd.states and destiny in self.afd.states:
                        if currState not in newTransitions:
                            newTransitions.update({currState: {symbol: destiny}})
                        else:
                            newTransitions[currState].update({symbol: destiny})

        self.afd.transitions = newTransitions

    def hopcroft(self):
        """
        Funcion que realiza el algoritmo de Hopcroft para minimizar el automata finito determinista
        """
        terminals = self.afd.finalStates
        nonTerminals = list(set(self.afd.states).difference(set(self.afd.finalStates)))
        nonTerminals.sort()
        P = [nonTerminals, terminals]

        while True:
            newP = []
            for g in P:
                L = dict()
                for s in g:
                    groupId = []
                    for symbol in self.alphabet:
                        transitions = self.afd.transitions.get(s, None)
                        groupIdAdded = False

                        if transitions:
                            for h in P:
                                for symbol2, destiny in transitions.items():
                                    if symbol == symbol2 and destiny in h:
                                        groupId.append((symbol, tuple(h)))
                                        groupIdAdded = True
                                        break
                                if groupIdAdded:
                                    break
                        else:
                            groupId.append((symbol, None))

                    groupId = tuple(groupId)
                    L.setdefault(groupId, set()).add(s)

                newP.extend(L.values())

            if newP != P:
                P = newP
            else:
                break

        self.states = P

    def createMinDFA(self):
        """
        Funcion que genera el automata finito determinista minimizado
        """
        for currState, transitions in self.afd.transitions.items():
            for state in self.states:
                if currState in state:
                    for state2 in self.states:
                        for symbol, destiny in transitions.items():
                            if destiny in state2:
                                if tuple(state) not in self.transitions:
                                    self.transitions.update({tuple(state): {symbol: state2}})
                                else:
                                    self.transitions[tuple(state)].update({symbol: state2})
                    break

        for state in self.states:
            for final in self.afd.finalStates:
                if final in state:
                    self.finalStates.append(state)
                    break

        for i, state in enumerate(self.states):
            if self.afd.initialState[0] in state and i != 0:
                temp = self.states[0]
                self.states[0] = state
                self.states[i] = temp

        for i, state in enumerate(self.states):
            self.equivalents.update({"S" + str(i + 1): state})
            self.states[i] = "S" + str(i + 1)
            if self.afd.initialState[0] in state:
                self.initialState = state

        self.initialState = keyFromValue(equivalents=self.equivalents, search_value=self.initialState)

        self.finalStates = [keyFromValue(equivalents=self.equivalents, search_value=state) for state in
                            self.finalStates]

        self.transitions = self.translateTransitions(self.transitions)

    def translateTransitions(self, transitions):
        """
        Funcion que traduce las transiciones a un diccionario.
        :param transitions:
        :return:
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

    def writeJSONAFD(self):
        """
        Funcion que genera un archivo .json con los componentes del AFD minimizado
        """
        equivalents = dict()
        for key, value in self.equivalents.items():
            equivalents.update({key: list(value)})

        minDFA = {
            "estados": self.states,
            "alfabeto": self.alphabet,
            "estadoInicial": self.initialState,
            "estadosFinales": self.finalStates,
            "transiciones": self.transitions,
            "equivalencias": equivalents
        }
        with open('./bin/lib/minafd/minafd.json', 'w') as outfile:
            json.dump(minDFA, outfile, indent=6)

    def graphDFA(self):
        """
        Funcion que genera una imagen .svg representando el Automata Finito Determinista
        """
        alphabet = set(self.alphabet)
        states = set(self.transitions.keys())
        initial_state = self.initialState
        accepting_states = set(self.finalStates)

        dfa = SimpleDFA(states, alphabet, initial_state, accepting_states, self.transitions)

        graph = dfa.trim().to_graphviz()

        legend = "\n".join([f"{key} = {list(value)}" for key, value in self.equivalents.items()])
        legend = f"Equivalencias:\n{legend}"
        graph.attr(label=legend)

        graph.attr(rankdir='LR')
        graph.render("./bin/lib/minafd/minDFA", view=True)

    def DFAtominDFA(self):
        """
        Funcion que inicializa todos los metodos necesarios para minizar un automata finito determinista
        """
        self.deleteUnreachableStates()
        self.updateTransitions()
        self.hopcroft()
        self.createMinDFA()

        self.writeJSONAFD()
        self.graphDFA()

    def simulateMinDFA(self, string):
        """
        Funcion que simula un automata finito determinista minizado
        :param string: Cadena a simular
        :return: Metodo simulateDFA con la cadena a simular y los componentes del AFD minimizado
        """
        return simulateDFA(string=string, initialState=self.initialState, finalStates=self.finalStates,
                           transitions=self.transitions)

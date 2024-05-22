import json
from pythomata import SimpleDFA
from afd import keyFromValue, simulateDFA

ESTADOS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

class tempNFA(object):
    def __init__(self, filename):
        with open(filename, "r", encoding="utf-8") as json_file:
            afn = json.load(json_file)

        self.states = afn["estados"]
        self.alphabet = afn["alfabeto"]
        self.initialState = afn["estadoInicial"]
        self.finalStates = afn["estadosFinales"]
        self.transitions = afn["transiciones"]


class AFD(object):
    def __init__(self, afnFilename):
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
        alcanzables = []

        for estado in estados:
            if estado in self.afn.transitions and symbol in self.afn.transitions[estado]:
                for transition in self.afn.transitions[estado][symbol]:
                    alcanzables.append(transition)

        return alcanzables

    def subsetConstruction(self):
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

        self.states = generate_state_names(len(states))
        self.equivalents = {self.states[i]: states[i] for i in range(len(states))}
        final = [state for state in states for final in self.afn.finalStates if final in state]
        self.finalStates = [self.states[states.index(state)] for state in final]
        self.transitions = self.translateTransitions(transitions)
        self.initialState = [self.states[states.index(state)] for state in states if self.afn.initialState in state]

    def translateTransitions(self, transitions):
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
        for key, value in self.equivalents.items():
            if value == search_value:
                return key
        return []

    def writeJSONAFD(self):
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
        self.subsetConstruction()
        self.writeJSONAFD()
        self.graphDFA()

    def simulateDFA(self, string):
        return simulateDFA(string=string, initialState=self.initialState[0], finalStates=self.finalStates,
                           transitions=self.transitions)

import time

def keyFromValue(equivalents, search_value):
    for key, value in equivalents.items():
        if value == search_value:
            return key
    return []


def move(s, c, transitions):
    for state, transitions in transitions.items():
        if s == state:
            destiny = transitions.get(c, None)
            return destiny if destiny and len(destiny) > 0 else None


def simulateDFA(string, initialState, finalStates, transitions):
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
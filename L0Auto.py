from graphviz import Digraph
from automaton import Automaton
from directAfd import DirectAfd
from shunthingYard import shuntingYard
import pickle
import string

class Automatonn:
    def __init__(self, regex_dict, option=0):
        self.afds = {key: {'afd': DirectAfd(shuntingYard(regex), option=option), 'buffer': "", 'currState': "S0", 'counter': 0, 'aceptedState': False, 'stillInGame': True} for key, regex in regex_dict.items()}
        self.string = ""
        self.maxCounter = [None, 0]
        self.alphabet = set()
        self.getAlphabet()

    def getAlphabet(self):
        for value in self.afds.values():
            afd = value['afd']
            self.alphabet = self.alphabet.union(afd.alfabeto)

    def simulateAfds(self, char, nextChar):
        tokenFound = []
        
        initialTransition = False
        for key, value in self.afds.items():
            afd = value['afd']
            if afd.stepDirectAFD(char, 'S0') or afd.stepDirectAFD(char, value['currState']):
                initialTransition = True
                break
        
        if not str(char) in self.alphabet or not initialTransition:
            return False, char

        self.string += chr(char)

        for key, value in self.afds.items():
            afd = value['afd']

            if value['stillInGame']:
                nextState = afd.stepDirectAFD(char, value['currState'])
                if nextState is not None:
                    value['currState'] = nextState
                    value['counter'] += 1
                    value['buffer'] += chr(char)
                    if nextState in afd.estados_aceptacion:
                        value['aceptedState'] = True
                    nextStates = afd.stepDirectAFD(ord(nextChar), value['currState']) if not nextChar is None else None
                    if (value['counter'] > self.maxCounter[1]) or (not nextStates is None):
                        self.maxCounter = [key, value['counter']]

        if not self.maxCounter[0] is None:
            key = self.maxCounter[0]
            value = self.afds[self.maxCounter[0]]
            nextState = value['afd'].stepDirectAFD(ord(nextChar), value['currState']) if not nextChar is None else None
            if (not value['stillInGame'] and value['aceptedState']) or (nextChar is None and value['aceptedState']) or (nextState is None and value['aceptedState']):
                buffer = value['buffer']
                tokenFound.append([key, buffer])
                
                for key, value in self.afds.items():
                    value['counter'] = 0
                    value['currState'] = "S0"
                    value['aceptedState'] = False
                    value['stillInGame'] = True
                    value['buffer'] = ""
                self.string = ""
                self.maxCounter = [None, 0]

        return True, tokenFound

class AutomataLR0:
    def __init__(self, pickleFile, log_function=None, log_function2=None):
        self.tokens = []
        self.grammar = None
        with open(pickleFile, 'rb') as input:
            self.automatonYalex = pickle.load(input)
        self.productionNameMapping = {}
        self.log = log_function
        self.log2 = log_function2

    def readFile(self, yaplContent):
        comentariosAut = Automaton(regex_dict={"comentarios": "/\*(_)*\*/"})
        iChar = 0
        while iChar < len(yaplContent):
            char = yaplContent[iChar]
            nextChar = yaplContent[iChar + 1] if iChar + 1 < len(yaplContent) else None
            comentariosAut.simulateAfds(ord(char), nextChar)
            iChar += 1
        
        comentarios = comentariosAut.getTokens()['comentarios']
        for comentario in comentarios:
            yaplContent = yaplContent.replace(comentario, "")

        split = yaplContent.split("%%")
        if len(split) != 2:
            print("Error al leer el archivo. No se encontró el separador '%%'")
            return -1
        tokensContent = split[0]
        productionContent = split[1]

        tokensAutomaton = Automatonn(regex_dict={"tokens": "%token ['a'-'z''A'-'Z']+( ['a'-'z''A'-'Z']+)*", "ignores": "IGNORE( ['a'-'z''A'-'Z']+)+"})
        productionsAutomaton = Automaton(regex_dict={"productions": "['a'-'z''A'-'Z']+:\s*(['a'-'z''A'-'Z']+|\s|\|)+;"})

        tokens = []
        ignores = []
        iChar = 0
        while iChar < len(tokensContent):
            char = tokensContent[iChar]
            nextChar = tokensContent[iChar + 1] if iChar + 1 < len(tokensContent) else None
            found, tokensFound = tokensAutomaton.simulateAfds(ord(char), nextChar)
            if found:
                for item in tokensFound:
                    if item[0] == "tokens":
                        tokens.append(item[1])
                    else:
                        ignores.append(item[1])
            iChar += 1

        iChar = 0
        while iChar < len(productionContent):
            char = productionContent[iChar]
            nextChar = productionContent[iChar + 1] if iChar + 1 < len(productionContent) else None
            productionsAutomaton.simulateAfds(ord(char), nextChar)
            iChar += 1

        productions = productionsAutomaton.getTokens()['productions']

        if len(tokens) == 0:
            print("\t\033[31mError al leer el archivo. No se encontraron tokens.\033[0m")
            return -1
        if len(productions) == 0:
            print("\t\033[31mError al leer el archivo. No se encontraron producciones.\033[0m")
            return -1
        
        for token in tokens:
            token = token.replace("%token", "").strip()
            split = token.split(" ")
            for s in split:
                self.tokens.append(s.lower())

        for ignore in ignores:
            ignore = ignore.replace("IGNORE", "").strip()
            split = ignore.split(" ")
            for s in split:
                self.tokens.remove(s.lower())

        for i, production in enumerate(productions):
            productionName, rules = production.split(':')
            productionName = productionName.strip()

            encodedProductionName = string.ascii_uppercase[i % 26]
            self.productionNameMapping[productionName] = encodedProductionName

        grammar = {}
        for production in productions:
            productionName, rules = production.split(':')
            productionName = productionName.strip()
            encodedProductionName = self.productionNameMapping[productionName]
            rules = rules[:-1].split('|')

            encoded_rules = []
            for rule in rules:
                encoded_rule = []
                for symbol in rule.strip().split():
                    if symbol in self.productionNameMapping:
                        encoded_rule.append(self.productionNameMapping[symbol])
                    else:
                        encoded_rule.append(symbol)
                encoded_rules.append(tuple(encoded_rule))

            grammar[encodedProductionName] = encoded_rules

        for key, value in grammar.items():
            for i, rule in enumerate(value):
                newRule = []
                for symbol in rule:
                    if symbol.lower() in self.tokens and symbol.lower() in self.automatonYalex.variables and len(symbol) > len(self.automatonYalex.variables[symbol.lower()]):
                        newRule.append(self.automatonYalex.variables[symbol.lower()])
                    else:
                        newRule.append(symbol)
                value[i] = tuple(newRule)
        self.grammar = grammar
        self.buildLr0Automaton()
        self.visualizeAutomaton()

        for nonterminal in self.grammar:
            first_set = self.FIRST(nonterminal)
            if self.log2:
                self.log2(f"FIRST({nonterminal}): {first_set}")
                print(f"FIRST({nonterminal}): {first_set}")
        
    def isNonterminal(self, symbol):
        return symbol in self.grammar.keys()

    def closure(self, items):
        closureSet = set(items)
        added = True
        while added:
            added = False
            for item in closureSet.copy():
                production, dot = item
                if dot < len(production) and self.isNonterminal(production[dot]):
                    nextSymbol = production[dot]
                    for prod in self.grammar[nextSymbol]:
                        newItem = (prod, 0)
                        if newItem not in closureSet:
                            closureSet.add(newItem)
                            added = True
                            
        return closureSet
    
    def goto(self, items, symbol):
        gotoSet = set()
        for item in items:
            production, dot = item
            if dot < len(production) and production[dot] == symbol:
                gotoSet.add((production, dot + 1))

        # Calcula el cierre del conjunto resultante para completar el GOTO
        closure_result = self.closure(gotoSet)
        if self.log:
            self.log(f"Cierre de GOTO set: {', '.join(str(item) for item in closure_result)}")
            print(f"Cierre de GOTO set: {', '.join(str(item) for item in closure_result)}")

        return self.closure(gotoSet)

    def FIRST(self, symbol, in_process=None):
        if in_process is None:
            in_process = set()

        first = set()
        if symbol in in_process:
            return first  # Retorna un conjunto vacío si el símbolo ya está en proceso para evitar ciclos

        if symbol in self.tokens or symbol.islower():
            first.add(symbol)
        elif symbol in self.grammar:
            in_process.add(symbol)
            for production in self.grammar[symbol]:
                if production == ['ε']:
                    first.add('ε')
                else:
                    for prod_symbol in production:
                        if prod_symbol != symbol:  # Evita llamarse a sí mismo directamente
                            subset = self.FIRST(prod_symbol, in_process)
                            first.update(subset - {'ε'})
                            if 'ε' not in subset:
                                break
                    else:
                        first.add('ε')
            in_process.remove(symbol)
        return first

    def buildLr0Automaton(self):
        startProduction = list(self.grammar.keys())[0]
        startItem = (startProduction, 0)
        initialState = self.closure({startItem})
        
        states = [initialState]
        transitions = {}
        stateIndex = {tuple(initialState): 0}
        index = 1

        while index <= len(states):
            currentState = states[index - 1]
            for item in currentState:
                production, dot = item
                if dot < len(production):
                    nextSymbol = production[dot]
                    nextState = self.goto(currentState, nextSymbol)
                    if nextState not in states:
                        states.append(nextState)
                        stateIndex[tuple(nextState)] = len(states)
                    else:
                        pass
                    transitions[(index, nextSymbol)] = stateIndex[tuple(nextState)]
            index += 1
        
        self.states = states
        self.transitions = transitions
        return states, transitions
    
    def visualizeAutomaton(self):
        dot = Digraph()
        dot.attr(rankdir='LR')

        self.initialState = list(self.grammar.keys())[0]

        if (isinstance(self.initialState, tuple)):
            self.initialState = self.initialState[0]
    
        for i, state in enumerate(self.states):
            label = f"I{i}:\n"
            for production, position in state:
                key = next((k for k, v in self.grammar.items() if tuple(production) in v), self.initialState + "'")
                before = "".join(production[:position])
                after = "".join(production[position:])
                label += f"{key}→{before}·{after}\n"
            if self.initialState + "'→" + self.initialState + "·" in label:
                dot.node(str(i), label, shape='rect', style='rounded', color='green', fontcolor='black')
                dot.node("accept", "accept", shape='plaintext')
                dot.edge(str(i), "accept", label='$')
            else:
                dot.node(str(i), label, shape='rect', style='filled,rounded', fillcolor='red' if i == 0 else 'blue', fontcolor='white')
    
        for (state, symbol), nextState in self.transitions.items():
            dot.edge(str(state - 1), str(nextState - 1), label=symbol)
    
        dot.render('./bin/lib/L0Automaton/L0automaton', view=True)
        pass
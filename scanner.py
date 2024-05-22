import pickle
from directAfd import DirectAfd
from shunthingYard import shuntingYard
#Encabezado del archivo Yalex
#Sin encabezado

#Generador de funciones
def ejecutarAccion(accion):
    aEjecutar = "\ndef funcion():\n"
    for line in accion.split("\n"):
        aEjecutar += "\t" + line + "\n"
    aEjecutar += "\nresultado = funcion()"
    print("\033[32mAccion ejecutandose:\033[0m")
    try:
        exec(aEjecutar, globals(), locals())
        print(f"\033[32m\tResultado de la accion:\033[0m {locals()['resultado']}")
    except Exception as e:
        print(f"\033[31m\tError:\033[0m {e}")
    
#Clase Automaton
class Automaton:
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
                next_state = afd.stepDirectAFD(char, value['currState'])
                if next_state is not None:
                    value['currState'] = next_state
                    value['counter'] += 1
                    value['buffer'] += chr(char)
                    if next_state in afd.estados_aceptacion:
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


#Clase Scanner
class Scanner():
    def __init__(self, regex, file, option=0):
        self.originalRegex = regex
        self.regex = ""
        self.scanner = None
        self.tokens = []
        with open(file, 'rb') as input:
            self.automatonYalex = pickle.load(input)
        self.splitByHashtag()
        self.createAfd()
        
    
    def splitByHashtag(self):
        """
        Funcion que se encarga de separar los regex por cada #| o un #)
        :return:
        """
        i = 0
        last = 0
        self.originalRegex = self.originalRegex[1:-1]
        while i < len(self.originalRegex):
            if self.originalRegex[i] == "#" and (i+1 == len(self.originalRegex) or self.originalRegex[i + 1] == "|"):
                self.tokens.append(self.originalRegex[last:i])
                last = i + 2
                i += 2
                continue
            i += 1

    def createAfd(self):
        """
        Funcion que se encarga de crear los automatas identificados en la variable tokens
        :return:
        """
        automatas = {}
        variableNames = self.automatonYalex.rulesScanner
        for token in self.tokens:
            id = token
            if "'" + id + "'" in self.automatonYalex.chars:
                id = "'" + id + "'"
            elif '"' + id + '"' in self.automatonYalex.chars:
                id = '"' + id + '"'
            
            for key, value in variableNames.items():
                if value in token:
                    id = key
                    break
                
            automatas[id] = token
        self.scanner = Automaton(automatas)
        
    def scanFile(self, file):
        """
        Funcion que se encarga de leer el archivo y simular el scanner en base a él
        :param file: Archivo a leer
        :return:
        """
        with open(file, 'r', encoding='utf-8') as file:
            fileContent = file.read()
        iChar = 0
        last = 0
        while iChar < len(fileContent):
            char = fileContent[iChar]
            nextChar = fileContent[iChar + 1] if iChar + 1 < len(fileContent) else None
            tokensFound, tokens = self.scanner.simulateAfds(ord(char), nextChar)
            if tokensFound:
                last = iChar
                for item in tokens:
                    print(f"\033[1m\033[34mToken:\033[37m {item[0]}\033[0m -> '{item[1]}'")
                    if item[0][0] == "\\":
                        if "'" + item[0][1:] + "'" in self.automatonYalex.chars:
                            item[0] = "'" + item[0][1:] + "'"
                        elif '"' + item[0][1:] + '"' in self.automatonYalex.chars:
                            item[0] = '"' + item[0][1:] + '"'
                    accion = self.automatonYalex.actions.get(item[0], None)
                    if accion is not None and accion != "":
                        ejecutarAccion(accion)
            else:
                print(f"\033[31mError:\033[0m Token no reconocido: {char}")
            iChar += 1

#Trailer
#Sin trailer
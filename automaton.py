from directAfd import DirectAfd
from shunthingYard import shuntingYard

operators = "+*?|·^()[]_\\"
class Automaton:
    def __init__(self, regex_dict, option=0):
        self.afds = {key: {'afd': DirectAfd(shuntingYard(regex), option=option), 'counter': 0, 'buffer': "", 'currState': "S0", 'aceptedState': False, 'stillInGame': True, 'tokens': []} for key, regex in regex_dict.items()}
        self.string = ""
        self.maxCounters = {}
        self.maxKeys = set()
        self.variables = {}
        self.actions = {}
        self.toChange = []
        self.chars = []

    def getTokens(self):
        tokens_dict = {}
        for key, value in self.afds.items():
            tokens_dict[key] = value['tokens']
        return tokens_dict

    def simulateAfds(self, char, nextChar):
        tokenFound = None
        self.string += chr(char)
        for key, value in self.afds.items():
            afd = value['afd']

            if not value['stillInGame'] and not value['aceptedState']:
                value['stillInGame'] = True
                value['counter'] = 0
                value['currState'] = "S0"
                value['aceptedState'] = False
                value['buffer'] = ""

            if value['stillInGame']:
                value['buffer'] += chr(char)
                next_state = afd.stepDirectAFD(char, value['currState'])
                if next_state is not None:
                    value['currState'] = next_state
                    value['counter'] += 1
                    if next_state in afd.estados_aceptacion:
                        value['aceptedState'] = True
                        self.maxCounters[key] = value['counter']
                        self.maxKeys.add(key) ## 
                    else:
                        value['aceptedState'] = False
                else:
                    value['stillInGame'] = False

            else:
                if value['aceptedState']:
                    if value['counter'] == self.maxCounters[key]:
                        self.maxKeys.add(key)
                    else:
                        value['stillInGame'] = True
                        value['counter'] = 0
                        value['currState'] = "S0"
                        value['aceptedState'] = False
                        value['buffer'] = ""
                

        #if not any(afd['stillInGame'] for afd in self.afds.values()) or (self.maxKeys and not any(self.afds[key]['stillInGame'] for key in self.maxKeys)) or nextChar is None:
        if not any(afd['stillInGame'] for afd in self.afds.values()) or (self.maxKeys and not any(self.afds[key]['aceptedState'] for key in self.maxKeys)) or nextChar is None:
            tokenFound = {}
            maxCounters_sorted = {k: v for k, v in sorted(self.maxCounters.items(), key=lambda item: item[1], reverse=True)}
            keyx = list(maxCounters_sorted.keys())

            if len(keyx) > 0:
                key = keyx[0]
                buffer = self.afds[key]['buffer'][:-1] if not nextChar is None else self.afds[key]['buffer']
                self.afds[key]['tokens'].append(buffer)
                tokenFound[key] = buffer
            for key in self.afds.keys():
                self.afds[key]['counter'] = 0
                self.afds[key]['currState'] = "S0"
                self.afds[key]['aceptedState'] = False
                self.afds[key]['stillInGame'] = True
                self.afds[key]['buffer'] = ""
            self.string = ""
            self.maxCounters.clear()
            self.maxKeys.clear()
        return tokenFound

    def parseVariables(self):
        for token in self.afds['variables']['tokens']:
            parts = token.split('=')
            if len(parts) == 2:
                identifierParts = parts[0].split()
                if len(identifierParts) == 2 and identifierParts[0] == "let":
                    identifier = identifierParts[1]
                    value = parts[1].strip()
                    self.variables[identifier] = value
                else:
                    return f"\033[31mError:\033[0m Token de variable mal formado: {token}"
            else:
                    return f"\033[31mError:\033[0m Token de variable mal formado: {token}"
        return None

    def getVariables(self):
        return self.variables

    def getFirstRegex(self):
        """
        Genera el "regex sucio" a partir de la regla `rule tokens`.
        Args: ruleTokens (str): La regla `rule tokens` del archivo yalex.
        Returns: str: El "regex sucio" formado a partir de los tokens.
        """
        if not self.afds['rules']['tokens']:
            return f"\033[31mError:\033[0m No existe la parte de rule en el archivo"
        self.clearRules()
        ruleTokens = self.afds['rules']['tokens'][0]
        tokens = ruleTokens.split()

        cleanedTokens = []
        ignore = False
        for tokenId, token in enumerate(tokens):
            if token == '{' and tokens[tokenId - 1] != '\\':
                ignore = True
            elif token == '}' and ignore and tokens[tokenId - 1] != '\\':
                ignore = False
            elif token.startswith('(*'):
                ignore = True
            elif token.endswith('*)') and ignore:
                ignore = False
            elif not ignore:
                cleanedTokens.append(token)

        cleanedTokens = cleanedTokens[3:]

        items = []
        for token in cleanedTokens:
            oldToken = token
            token = token.replace("'", "").replace('"', "")
            if token == '|' and oldToken != "'|'" and oldToken != '"|"':
                continue
            items.append(oldToken)
            if oldToken.isalnum():
                self.toChange.append(oldToken)
            else:
                self.chars.append(oldToken)

        self.ruleItems = items
        return "(" + "#|".join(items) + "#)"

    def replaceVariables(self, regex):
        #self.changeActions()
        self.createVariablesDict()
        while self.toChange:
            token = self.toChange.pop()
            if token in self.variables:
                i = 0
                while i < len(regex):
                    if regex[i:i + len(token)] == token:
                        if i == 0 or regex[i - 1] not in "'\"" or (i + len(token) < len(regex) and regex[i + len(token)] not in "'\""):
                            l= regex[i+len(token)]
                            oldRegex = regex
                            regex = regex[:i] + self.variables[token] + regex[i + len(token):]
                            i += len(self.variables[token]) - 1
                            for newToken in self.variables.keys():
                                if newToken in regex and newToken not in oldRegex:
                                    self.toChange.append(newToken)
                    i += 1

        for char in self.chars:
            new = char[1:-1]
            i = 0
            charClass = False
            while i < len(regex):
                if regex[i] == '[':
                    charClass = True
                elif regex[i] == ']':
                    charClass = False
                elif not charClass and regex[i:i + len(char)] == char:
                    new = new if new not in operators else "\\" + new
                    regex = regex[:i] + new + regex[i + len(char):]
                    i += len(new) - 1
                i += 1

        return regex
    
    def createVariablesDict(self):
        variables_dict = {}
        for item in self.ruleItems:
            if item in self.variables:
                variables_dict[item] = self.replaceActionKeys(item)
            else:
                variables_dict[item] = item
        self.rulesScanner = variables_dict
               
    
    def replaceActionKeys(self, regex):
        toChange = self.toChange.copy()
        variables = self.variables.copy()
        while toChange:
            token = toChange.pop()
            if token in variables:
                i = 0
                while i < len(regex):
                    if regex[i:i + len(token)] == token:
                        if i == 0 or regex[i - 1] not in "'\"" or (i + len(token) < len(regex) and regex[i + len(token)] not in "'\""):
                            oldRegex = regex
                            regex = regex[:i] + variables[token] + regex[i + len(token):]
                            i += len(variables[token]) - 1
                            for newToken in variables.keys():
                                if newToken in regex and newToken not in oldRegex:
                                    toChange.append(newToken)
                    i += 1
        return regex
    
    def changeActions(self):
        # Cambiar las llaves de las acciones por su valor correspondiente
        for key, value in self.actions.copy().items():
            tempKey = self.replaceActionKeys(key)
            self.actions[tempKey] = value
            if key != tempKey:
                del self.actions[key]
        
    
    def clearRules(self):
        rules = self.afds['rules']['tokens'][0]
        comentsAutomata = Automaton({"comentario": "\(\*[^'\x01'-'\x1F']*\*\)"})
        i = 0
        while i < len(rules):
            char = rules[i]
            nextChar = rules[i + 1] if i + 1 < len(rules) else None
            comentsAutomata.simulateAfds(ord(char), nextChar)
            i += 1
        tokens = comentsAutomata.getTokens()
        for token in tokens['comentario']:
            self.afds['comentarios']['tokens'].append(token)
            rules = rules.replace(token, "")
        
        self.afds['rules']['tokens'][0] = rules

        self.setActions()

    def setActions(self):
        yalex_text = self.afds['rules']['tokens'][0]

        in_action = False
        current_token = ""
        current_action = ""
        toDelete = []

        ruleStateAFD = Automaton({"rule": "rule ['A'-'Z''a'-'z']+\s+="})
        i = 0
        while i < len(yalex_text):
            char = yalex_text[i]
            nextChar = yalex_text[i + 1] if i + 1 < len(yalex_text) else None
            ruleStateAFD.simulateAfds(ord(char), nextChar)
            i += 1
        statement = ruleStateAFD.getTokens()['rule'][0]

        i = len(statement)
        while i < len(yalex_text):
            char = yalex_text[i]
            if char == '{':
                in_action = True
                current_action = ""
                i += 1
                continue
            elif char == '}':
                in_action = False
                toDelete.append("{" + current_action + "}")
                current_token = self.replaceActionKeys(current_token.strip())
                if current_token == "":
                    self.afds['rules']['tokens'].append(current_action)
                    i += 1
                    continue
                self.actions[current_token.strip()] = current_action.strip()
                current_token = ""
                current_action = ""
                i += 1
                continue

            if char == '|' and yalex_text[i - 1] != "\\":
                current_token = ""
                i += 1
                continue

            if not in_action:
                current_token += char
            else:
                current_action += char

            i += 1

        for token in toDelete:
            self.afds['rules']['tokens'][0] = self.afds['rules']['tokens'][0].replace(token, "")

        return self.actions


    

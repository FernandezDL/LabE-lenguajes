operators = "#+*?|·^()[]_\\"
quotes = "'\""
def validation(regex):
    """
    Funcion que valida la expresion regex
    :param regex: expresion regex a evaluar
    :return:
    - String de error si la cadena no es valida
    - String con la cadena Regex si esta es valida
    """
    i = 1
    if len(regex) == 0:
        return {"error": i,
                "desc": "Ingrese una expresión regular."}

    stack = []
    i += 1
    for k, char in enumerate(regex):
        if char == "(" and regex[k - 1] != "\\":
            stack.append(char)
        elif char == ")" and regex[k - 1] != "\\":
            if not stack:
                return {"error": k,
                        "desc": "Paréntesis no balanceados en la expresión regular."}
            stack.pop()

    if stack:
        return {"error": i,
                "desc": "Paréntesis no balanceados en la expresión regular."}

    stack = []
    i += 1
    for k, char in enumerate(regex):
        if char == "[" and regex[k - 1] != "\\":
            stack.append(char)
        elif char == "]" and regex[k - 1] != "\\":
            if not stack:
                return {"error": i,
                        "desc": "Corchetes para clases no balanceados en la expresión regular."}
            stack.pop()

    if stack:
        return {"error": i,
                "desc": "Corchetes para clases no balanceados en la expresión regular."}

    operators = set("*+?|")
    i += 1
    for index in range(len(regex) - 1):
        current_char = regex[index]
        next_char = regex[index + 1]

        if current_char in operators and next_char in operators and next_char != "|":
            return {"error": i,
                    "desc": "Sintaxis incorrecta de operadores en la expresión regular."}

    i += 1
    if "|" in regex:
        for index in range(len(regex) - 1):
            current_char = regex[index]
            next_char = regex[index + 1]

            if current_char == "|" and next_char in "*+?" and regex[index - 1] != "\\":
                return {"error": i,
                        "desc": "Operador OR mal utilizado en la expresión regular."}

    i += 1
    if not regex[0].isalnum() and regex[0] != "(":
        return {"error": i,
                "desc": "Operador sin operando."}

    i += 1
    if all([char in "+*?|()" for char in regex]):
        return {"error": i,
                "desc": "Expresión no válida. Solamente contiene operandos."}

    return None

def expandirClases(regex):
    i = 0
    while i < len(regex):
        l = regex[i]
        m = regex[i-1]
        if regex[i] == '[' and regex[i - 1] != '\\':
            j = i
            while j < len(regex) and regex[j] != ']':
                if regex[j] == '\\' and j + 1 < len(regex) and regex[j + 1] != '\\':
                    j += 2
                else:
                    j += 1
            grupo = regex[i+1:j]
            if '^' in grupo:
                expandedGroup = complemento(grupo)
                regex = regex[:i] + expandedGroup + regex[j+1:]
                i = j
                continue
            expandedGroup = expandCharacterClass(grupo)
            regex = regex[:i] + expandedGroup + regex[j+1:]
            i += len(expandedGroup) - 1
        i += 1
    return regex

def replaceSpecialScapes(value):
    value = value.replace("\\s", " \t\n\r")
    value = value.replace("\\t", "\t")
    value = value.replace("\\n", "\n")
    return value

def expandCharacterClass(regex):
    regex = replaceSpecialScapes(regex)
    expandedChars = []
    i = 1
    while i < len(regex) - 1:
        if regex[i] == '\\':
            if regex[i+1] == 'x':
                hexChar = regex[i + 2:i + 4]
                expandedChars.append(chr(int(hexChar, 16)))
                i += 4
            else:
                expandedChars.append(regex[i + 1])
                i += 2
        elif regex[i] == '-' and i > 0 and i < len(regex) - 2 and i - 2 > 0 and regex[i - 2] != "'" and i + 2 < len(regex) and regex[i + 2] != "'":
            if len(expandedChars) > 0:
                expandedChars.pop()
            start = regex[i-2]
            end = regex[i+2]
            expandedChars.extend([chr(c) for c in range(ord(start), ord(end) + 1)])
            i += 3
        elif regex[i] != "'" or (regex[i] == "'" and regex[i-1] == "\\"):  # Regular character
            expandedChars.append(regex[i])
            i += 1
        else:
            i += 1
    return '(' + '|'.join(c if c not in operators and not c in quotes else "\\" + c for c in expandedChars) + ')'

def complemento(regex):
    """
    Funcion que expande complementos de los grupos de caracteres de la expresion regex
    :param regex: Expresion regex
    :return: Expresion regex con complemento de grupos de caracteres expandidos
    """
    expandedChars = []
    i = 2
    while i < len(regex) - 1:
        if regex[i] == '\\':
            if regex[i + 1] == 'x':
                hexChar = regex[i + 2:i + 4]
                expandedChars.append(chr(int(hexChar, 16)))
                i += 4
            else:
                expandedChars.append(regex[i + 1])
                i += 2
        elif regex[i] == '-' and i > 1 and i < len(regex) - 2 and i - 2 > 0 and regex[i - 2] != "'":
            if len(expandedChars) > 0:
                expandedChars.pop()
            start = chr(ord(regex[i - 2]))
            end = regex[i + 2]
            expandedChars.extend([chr(c) for c in range(ord(start), ord(end) + 1)])
            i += 3
        elif regex[i] != "'" or (regex[i] == "'" and regex[i - 1] == "\\"):
            expandedChars.append(regex[i])
            i += 1
        else:
            i += 1

    finalExpanded = []
    
    for c in range(256):
        if chr(c) not in expandedChars:
            finalExpanded.append(chr(c))

    return '(' + '|'.join(c if c not in operators and c not in quotes else "\\" + c for c in finalExpanded) + ')'

def allSymbols(regex): # reemplazar del regex el simbolo _ por todos los ASCII de 0 a 255
    """
    Funcion que reemplaza el simbolo _ por todos los ASCII de 0 a 255
    :param regex: Expresion regex
    :return: Expresion regex con simbolo _ reemplazado
    """
    if "_" not in regex:
        return regex
    
    i = 0
    while i < len(regex):
        if regex[i] == "_" and regex[i - 1] != "\\":
            regex = regex[:i] + "(" + '|'.join(chr(c) if chr(c) not in operators and chr(c) not in quotes else "\\" + chr(c) for c in range(0, 256)) + ")" + regex[i + 1:]
        i += 1
    return regex

def difference(regex):
    if "#" not in regex:
        return regex
    i = regex.index("#")
    if regex[i - 1] == "\\" or (regex[i - 1] != "]" and regex[i + 1] != "["):
        return regex
    
    grupo1B = ""
    grupo2B = ""
    
    while i >= 0:
        if regex[i] == "[" and regex[i - 1] != "\\":
            j = i
            while regex[j] != "]" and regex[j - 1] != "\\":
                j += 1
            grupo1B = regex[i:j + 1]
            break
        i -= 1

    i = regex.index("#")
    while i < len(regex):
        if regex[i] == "[" and regex[i - 1] != "\\":
            j = i
            while regex[j] != "]" and regex[j - 1] != "\\":
                j += 1
            grupo2B = regex[i:j + 1]
            break
        i += 1

    grupo1 = expandirClases(grupo1B)
    grupo2 = expandirClases(grupo2B)

    set1 = set()
    set2 = set()

    for i, char in enumerate(grupo1):
        if char == "\\":
            set1.add(grupo1[i + 1])
        elif char not in operators and char != "\\":
            set1.add(char)
    
    for i, char in enumerate(grupo2):
        if char == "\\":
            set2.add(grupo2[i + 1])
        elif char not in operators and char != "\\":
            set2.add(char)

    difference = set1 - set2

    return regex.replace(grupo1B + "#" + grupo2B, "(" + '|'.join(c if c not in operators and c not in quotes else "\\" + c for c in list(difference)) + ")")

def cleaner(regex):
    """
    Funcion que limpia la expresion regex, se encarga de limpiar los parentesis y reemplazar los caractares ? y + con
    sus equivalentes.
    :param regex: Expresion Regex
    :return: Expresion regex limpiada
    """
    firstCleaned = difference(regex)
    firstCleaned = expandirClases(firstCleaned)
    firstCleaned = allSymbols(firstCleaned)

    i = 0
    while i < len(firstCleaned):
        if firstCleaned[i] == "'":
            if i == 0 or firstCleaned[i - 1] != "\\":
                x = firstCleaned[:i]
                firstCleaned = firstCleaned[:i] + firstCleaned[i + 1:]
                i -= 1
        i += 1

    i = 0
    while i < len(firstCleaned) and "?" in firstCleaned:
        try:
            i = firstCleaned.index("?", i)
        except:
            break

        if firstCleaned[i - 1] == "\\":
            i += 2
            continue

        if firstCleaned[i - 1] == ")":
            j = i - 2
            contadorParentesis = 0

            while (firstCleaned[j] != "(" or contadorParentesis != 0 and j >= 0):
                if firstCleaned[j] == ")":
                    contadorParentesis += 1
                elif firstCleaned[j] == "(":
                    contadorParentesis -= 1
                j -= 1

            if firstCleaned[j] == "(" and contadorParentesis == 0:
                temp = firstCleaned[j:i]
                firstCleaned = firstCleaned.replace(temp + "?", "(" + temp + "|ε)")

        elif firstCleaned[i - 1] != ")":
            firstCleaned = firstCleaned.replace(firstCleaned[i - 1] + "?", "(" + firstCleaned[i - 1] + "|ε)")
        i += 1

    i = 0
    while i < len(firstCleaned) and "+" in firstCleaned:
        try:
            i = firstCleaned.index("+", i)
        except:
            break

        if firstCleaned[i - 1] == "\\":
            i += 2
            continue

        if firstCleaned[i - 1] == ")":
            j = i - 2
            contadorParentesis = 0

            while (firstCleaned[j] != "(" or contadorParentesis != 0 and j >= 0):
                if firstCleaned[j] == ")":
                    contadorParentesis += 1
                elif firstCleaned[j] == "(":
                    contadorParentesis -= 1
                j -= 1

            if firstCleaned[j] == "(" and contadorParentesis == 0:
                temp = firstCleaned[j:i]
                firstCleaned = firstCleaned.replace(temp + "+", temp + temp + "*")

        elif firstCleaned[i - 1] != ")":
            firstCleaned = firstCleaned.replace(firstCleaned[i - 1] + "+",
                                                firstCleaned[i - 1] + firstCleaned[i - 1] + "*")
        i += 1

    cleanedRegex = list(firstCleaned)

    concatSymbol = "·"
    regexWithConcatSymbol = []
    i = 0
    while i < len(cleanedRegex):
        char = cleanedRegex[i]
        escaped = False
        if i + 1 < len(cleanedRegex):
            nextChar = cleanedRegex[i + 1]
            if (char == '\\'):
                regexWithConcatSymbol.append(char)
                regexWithConcatSymbol.append(nextChar)
                escaped = True
                i += 1
            else:
                regexWithConcatSymbol.append(char)
            if (char != "(" and nextChar != ")" and nextChar not in "*+?|" and char != "|") and not escaped:
                regexWithConcatSymbol.append(concatSymbol)
            elif escaped and i + 1 < len(cleanedRegex) and cleanedRegex[i + 1] not in "*+?|)":
                regexWithConcatSymbol.append(concatSymbol)
        else:
            regexWithConcatSymbol.append(char)
        i += 1

    finalRegex = []
    i = 0
    while i < len(regexWithConcatSymbol):
        c = regexWithConcatSymbol[i]
        if c == "\\":
            if i + 1 < len(regexWithConcatSymbol) and regexWithConcatSymbol[i + 1] not in "snt":
                finalRegex.append(ord(regexWithConcatSymbol[i + 1]))
            elif regexWithConcatSymbol[i + 1] not in "nt":
                finalRegex.append("(")
                finalRegex.append(9)
                finalRegex.append("|")
                finalRegex.append(10)
                finalRegex.append("|")
                finalRegex.append(13)
                finalRegex.append("|")
                finalRegex.append(32)
                finalRegex.append(")")
            else:
                temp = 10 if regexWithConcatSymbol[i + 1] == "n" else 9
                finalRegex.append(temp)
            i += 1
        elif c not in operators or c == "ε":
            finalRegex.append(ord(c))
        elif c == "#" and regexWithConcatSymbol[i - 1] != "\\":  # Si es un #
            finalRegex.append(c)
        else:
            finalRegex.append(c)
        i += 1


    return finalRegex


def shuntingYard(infix):
    """
    Funcion que utiliza el algoritmo de Shunting Yard para pasar la expresion Regex de formato infix a formato posfix
    :param infix: Cadena regex en formato infix
    :return: Cadena regex en formato posfit
    """
    precedence = {
        "*": 4,
        "+": 4,
        "?": 4,
        "·": 3,
        "|": 2,
        "(": 1
    }

    infix = cleaner(infix)
    #print(infix)

    postfix = []
    stack = []

    for i, char in enumerate(infix):
        if isinstance(char, int) and chr(char).isalnum() or char == "ε":
            postfix.append(char)

        elif char == "(":
            stack.append(char)

        elif char == ")":
            while stack and stack[-1] != "(":
                postfix.append(stack.pop())
            stack.pop()

        elif char in precedence:
            while len(stack) > 0:
                peekedChar = stack[-1]
                peekedCharPrece = precedence.get(stack[-1], 0)
                currCharPrece = precedence[char]

                if (peekedCharPrece >= currCharPrece):
                    postfix.append(stack.pop())
                else:
                    break

            stack.append(char)

        else:
            postfix.append(char)

    while stack:
        postfix.append(stack.pop())

    return postfix

x = "{\s*(['A'-'}''\x21'-'\x39']|=|\n| )*\s*}"
#print(shuntingYard(x))
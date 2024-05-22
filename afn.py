import json
import time
from nodeTree import alphanum, ArbolExpresion
from graphviz import Digraph
from afd import move


class Estado:
    def __init__(self, count, aceptacion=False):
        """
        Metodo constructor de clase Estado, esta clase representa un estado del Automata Finito No Determinista
        :param count: El valor del estado actual, inicia en 0
        :param aceptacion: Booleano, inidica si el estado es un estado de aceptación
        """
        self.nombre = f'q{count}'
        self.aceptacion = aceptacion
        self.transiciones = {}

    def __str__(self):
        """
        Metodo que convierte el objeto Clase a una representacion en String
        :return:
        - String: Representando el nombre del estado
        """
        return self.nombre


class Transicion:
    def __init__(self, simbolo, estado):
        """
        Metodo constructor de clase Transición, en esta se almacenan el simbolo que lleva de un estado a otro y el
        estado al que se llega. Este objeto se almacena dentro de transiciones de un objeto Estado.
        :param simbolo: Simbolo esperado para realizar transición
        :param estado: Estado al que se llega dado el simbolo esperado
        """
        self.simbolo = simbolo
        self.estado = estado


class Fragmento:
    def __init__(self, inicio, aceptaciones):
        """
        Esta clase representa un fragmento del automata finito no determinista, por decirlo es un pequeño AFN que será
        parte del AFN completo al ser unido con los demas objetos Fragmento.
        :param inicio: Estado Inicial del fragmento
        :param aceptaciones: Estados de aceptación del fragmento
        """
        self.inicio = inicio
        self.aceptaciones = aceptaciones


class Afn(object):
    def __init__(self, regex, option=0):
        """
        Metodo constructor de la clase Afn, esta clase representa un Automata Finito No Determinista generado en base
        a una expresion Regex en formato posfix
        :param regex: Expresion regex en formato posfix utilizada para crear el AFN
        :param option: Representa si se visualiza y genera el archivo json para la clase.
        """
        self.estados_aceptacion = []
        self.estados = []
        self.estado_inicial = None
        self.alfabeto = set()
        self.transiciones = {}
        self.regex = regex
        self.pila = []
        self.count = 0
        self.construir()
        if option == 1:
            self.visualizar_afn()
            self.exportar_json()

    def construir(self):
        """
        Metodo que construye el AFN en base a la expresion Regex, dependiendo del caracter que encuentre en la expresion
        regex realiza un metodo para cada tipo:
        - Alfanumerico o epsilon: procesar_simbolo
        - * o Estrella de Kleene : aplicar_cierre_kleene
        - | o Or o Union: aplicar_union
        - · o And o Concatenación: aplicar_concatenacion

        Ademas se utiliza una pila para manejar los estados, se espera que al final del procesamiento unicamente quede
        el estado inicial dentro de la pila, donde esten definidas todas las transiciones del AFN.
        """
        for char in self.regex:
            if isinstance(char, int):
                if alphanum(chr(char)):
                    self.procesar_simbolo(char)
            elif char in '*|·':
                if char == '*':
                    self.aplicar_cierre_kleene()
                elif char == '|':
                    self.aplicar_union()
                elif char == '·':
                    self.aplicar_concatenacion()

        if len(self.pila) != 1:
            raise ValueError("La expresión regular no es válida")

    def procesar_simbolo(self, char):
        """
        Metodo que procesa un simbolo alfanumerico o un epsilon. Crea un estado vacio con una transicion del caracter
        hacia un estado de aceptacion y genera un fragmento en base a estos. Este fragmento es agreado a la pila.
        :param char:
        """
        estado_inicial = self.create_estado()
        estado_aceptacion = self.create_estado(aceptacion=True)
        estado_inicial.transiciones[char] = [estado_aceptacion]
        fragmento = Fragmento(estado_inicial, [estado_aceptacion])
        self.pila.append(fragmento)

    def aplicar_cierre_kleene(self):
        """
        Metodo que maneja la cerradura Kleene, crea un fragmento para epsilon y lo junta con el fragmento generado
        anteriormente dentro de otro fragmento que tendra el mismo estado inicial y transiciones hacia ambos, el
        fragmento generado para el caracter anterior y el fragmento generado para el epsilon. Este fragmento nuevo
        es agregado a la pila.
        """
        fragmento = self.pila.pop()

        estado_inicial = self.create_estado()
        estado_aceptacion = self.create_estado(aceptacion=True)

        estado_inicial.transiciones['ε'] = [fragmento.inicio, estado_aceptacion]
        for estado in fragmento.aceptaciones:
            estado.aceptacion = False
            estado.transiciones.setdefault('ε', []).append(fragmento.inicio)
            estado.transiciones.setdefault('ε', []).append(estado_aceptacion)

        nuevo_fragmento = Fragmento(estado_inicial, [estado_aceptacion])
        self.pila.append(nuevo_fragmento)

    def aplicar_union(self):
        """
        Metodo que maneja la union de dos fragmentos generados anteriormente. Crea un fragmento que une los estados
        de aceptacion de los dos fragmentos anteriores con un estado inicial nuevo que puede llegar hacia los estados
        de ambos fragmentos. Al final agrega el fragmento nuevo a la pila.
        """
        fragmento2 = self.pila.pop()
        fragmento1 = self.pila.pop()

        estado_inicial = self.create_estado()
        estado_aceptacion = self.create_estado(aceptacion=True)

        estado_inicial.transiciones['ε'] = [fragmento1.inicio, fragmento2.inicio]
        for estado in fragmento1.aceptaciones + fragmento2.aceptaciones:
            estado.aceptacion = False  # Los estados antiguos ya no son de aceptación
            estado.transiciones.setdefault('ε', []).append(estado_aceptacion)

        nuevo_fragmento = Fragmento(estado_inicial, [estado_aceptacion])
        self.pila.append(nuevo_fragmento)

    def aplicar_concatenacion(self):
        """
        Metodo que maneja la concatenacion de dos fragmentos, toma dos fragmentos generados anteriormente y junta los
        estados del fragmento generados más anteriormente con el generado más recientemente. Agrega el fragmento
        resultante a la pila.
        """
        fragmento2 = self.pila.pop()
        fragmento1 = self.pila.pop()

        for estado in fragmento1.aceptaciones:
            estado.aceptacion = False
            for simbolo, estados_destino in fragmento2.inicio.transiciones.items():
                estado.transiciones[simbolo] = estados_destino

        nuevo_fragmento = Fragmento(fragmento1.inicio, fragmento2.aceptaciones)
        self.pila.append(nuevo_fragmento)

    def create_estado(self, aceptacion=False):
        """
        Metodo que crea un estado, le da el valor del conteo actual y si es un estado de aceptacion o no, tambien
        incrementa el conteo por 1.
        :param aceptacion:
        :return:
        - Estado : con un nombre 'q'+ count y la condicion si es un estado de aceptacion
        """
        count = self.count
        self.count += 1
        return Estado(count, aceptacion)

    def visualizar_afn(self):
        """
        Funcion que genera la representacion grafica del AFN utilizando la libreria de GraphViz. Se recorre el AFN
        creando un dot con nodos para cada estado con sus transiciones.
        :return:
        - dot : graphviz dot con nodos para cada estado y sus transiciones.
        """
        dot = Digraph()
        dot.attr(rankdir='LR')
        dot.node('start', '', shape='point')
        dot.edge('start', str(self.pila[0].inicio))

        def visitar(estado, visitados):
            """
            Metodo interno de visualizar_afn, este visita y recorre cada estado recursivamente.
            :param estado: El estado a visitar
            :param visitados: Lista de estados visitados
            :return: Lista de estados visitados
            """
            if str(estado) in visitados:
                return
            visitados.add(str(estado))
            if estado.aceptacion:
                dot.node(str(estado), shape='doublecircle')
                self.estados_aceptacion.append(str(estado))
            else:
                dot.node(str(estado))

            for simbolo, estados_destino in estado.transiciones.items():
                simbolo = str(simbolo)
                for estado_destino in estados_destino:
                    dot.edge(str(estado), str(estado_destino), label=simbolo)
                    self.alfabeto.add(simbolo)
                    if str(estado) not in self.transiciones:
                        self.transiciones[str(estado)] = {simbolo: [str(estado_destino)]}
                    elif simbolo not in self.transiciones[str(estado)]:
                        self.transiciones[str(estado)][simbolo] = [str(estado_destino)]
                    else:
                        self.transiciones[str(estado)][simbolo].append(str(estado_destino))
                    visitar(estado_destino, visitados)
            return visitados

        self.estado_inicial = str(self.pila[0].inicio)
        self.estados = visitar(self.pila[0].inicio, set())

        dot.render('./bin/lib/afn/afn', view=True)

        return dot

    def exportar_json(self, archivo='./bin/lib/afn/afn.json'):
        """
        Funcion que genera un diccionario con los datos del AFN y genera un archivo json
        :param archivo: Nombre de archivo a generar.
        """
        afn_dict = {
            "estados": list(self.estados),
            "alfabeto": list(self.alfabeto),
            "estadoInicial": self.estado_inicial,
            "estadosFinales": self.estados_aceptacion,
            "transiciones": self.transiciones
        }
        with open(archivo, 'w', encoding="utf-8") as f:
            json.dump(afn_dict, f, indent=4, ensure_ascii=False)

    def epsilon_closure(self, states):
        """
        Funcion que genera la cerradura epsilon para cada estado donde se encuentra un simbolo epsilon para realizar
        una transicion.
        :param states: lista de estados
        :return: Lista de estados neuvos con la cerradura epsilon realizada
        """
        stack, cerradura = set(states), set(states)
        
        while len(stack) != 0:
            t = stack.pop()
            
            if t in self.transiciones and "ε" in self.transiciones[t]:
                for u in self.transiciones[t]["ε"]:
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
            if estado in self.transiciones and symbol in self.transiciones[estado]:
                for transition in self.transiciones[estado][symbol]:
                    alcanzables.append(transition)
        
        return alcanzables

    def simulateNFA(self, string):
        """
        Metodo de simulación de un AFN
        :param string: Cadena de simbolos a simular
        :return:
        - Booleano, representando si la cadena es aceptada o no
        - String, con el tiempo que tomo simular la cadena.
        """
        inicio = time.time()
        s = self.epsilon_closure([self.estado_inicial])
        for char in string:
            #time.sleep(1)
            s = self.epsilon_closure(self.moveTo(s, str(ord(char))))
        if len(set(s) & set(self.estados_aceptacion)) != 0:
            fin = time.time()
            return True, "{:.2e}".format(fin - inicio)
        else:
            fin = time.time()
            return False, "{:.2e}".format(fin - inicio)

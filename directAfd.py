import json
import time
from nodeTree import ArbolExpresion
from graphviz import Digraph
from AFDUtils import simulateDFA, step, move


class Dstate(object):
    def __init__(self, nombre, aceptacion=False):
        """
        Funcion constructora del objeto Dstate, esta clase representa un estado del afd directo, donde se le da un
        nombre y si es un estaod de aceptacion.
        :param nombre: El nombre del estado
        :param aceptacion: Si es un estado de aceptacion o no
        """
        self.nombre = nombre
        self.aceptacion = aceptacion
        self.transiciones = {}

    def add_transicion(self, simbolo, estado):
        """
        Funcion que agrega una transicion al diccionario de transiciones del Dstate
        :param simbolo:
        :param estado:
        """
        self.transiciones[simbolo] = estado

    def __repr__(self):
        """
        Funcion que crea una representacion en String del objeto Dstate
        :return:
        - String representacion con el nombre del Dstate y si es un estado de acpetacion
        """
        return f"Dstate({self.nombre}, Accept={self.aceptacion})"


class DirectAfd(object):
    def __init__(self, regex, option=0):
        """
        Funcion constructora del objeto DirectAfd, esta inicializa las variables a utilizar durante la creacion
        del automata finito determinista por construccion directa.
        :param regex: Expresion regex en formato posfix a utilizar para construir AFD
        """
        self.transiciones = {}
        self.estados_aceptacion = set()
        self.alfabeto = set()
        self.estados = set()
        self.estado_inicial = None
        self.arbol = ArbolExpresion(regex)
        self.raiz = self.arbol.raiz
        if option == 1:
            self.arbol.visualizar_arbol()
        self.Dstates = {}
        self.curr_estado = 0

        self.construir_afd()
        
        self.visualizar_afd(option=option)

    def nuevo_estado(self, positions, aceptacion=False):
        """
        Funcion que agrega un estado a la lista Dstates
        :param positions: La posicion del estado dentro del AFD
        :param aceptacion: Si el estado es de aceptacion o no
        :return:
        - Estado generado
        """
        nombre = f"S{self.curr_estado}"
        self.curr_estado += 1
        nuevo_estado = Dstate(nombre, aceptacion=aceptacion)
        self.Dstates[nombre] = (nuevo_estado, positions)
        return nuevo_estado

    def obtener_o_crear_estado(self, positions):
        """
        Funcion que determina si un estado ya existe y en caso que no genera un estado nuevo
        :param positions: Posicion del estado a buscar
        :return:
        - Estado, ya sea estado encotrado para la posicion o estado generado.
        """
        aceptacion = self.raiz.derecho.leaf in positions
        for nombre, (estado, pos) in self.Dstates.items():
            if pos == positions:
                return estado
        return self.nuevo_estado(positions, aceptacion)

    def construir_afd(self):
        """
        Funcion que construye el AFD. Utiliza una lista de pendientes, donde se almacenan los estados creados pero
        pendientes de ser alcanzados.
        :return:
        - inicial : Estado inicial
        - Dstates : Diccionario de estados del AFD
        """
        inicial = self.obtener_o_crear_estado(self.raiz.firstpos)
        pendientes = [inicial]
        procesados = set()

        while pendientes:
            curr_estado = pendientes.pop(0)
            if curr_estado.nombre in procesados:
                continue
            procesados.add(curr_estado.nombre)

            _, posicion = self.Dstates[curr_estado.nombre]

            simbolos_a_pos = {}
            for pos in posicion:
                simbolo = self.arbol.simbolos[pos - 1].valor
                if simbolo != 'ε' and simbolo != '#':
                    followpos = self.arbol.simbolos[pos - 1].followpos
                    if simbolo in simbolos_a_pos:
                        simbolos_a_pos[simbolo].update(followpos)
                    else:
                        simbolos_a_pos[simbolo] = set(followpos)

            for simbolo, pos in simbolos_a_pos.items():
                next_state = self.obtener_o_crear_estado(pos)
                curr_estado.add_transicion(simbolo, next_state)
                if next_state.nombre not in procesados and next_state not in pendientes:
                    pendientes.append(next_state)

        return inicial, self.Dstates

    def visualizar_afd(self, option = 0):
        """
        Funcion que recorre el AFD para crear una representacion grafica de este usando la libreria de Graphviz
        :return:
        - Dot : Digrafo con la representacion de cada estado y sus transiciones
        """
        dot = Digraph(comment='AFD Directo')
        dot.attr(rankdir='LR')
        dot.node('start', '', shape='point', style='invisible')

        for nombre, (estado, _) in self.Dstates.items():
            self.estados.add(nombre)
            if estado.aceptacion:
                dot.node(nombre, shape='doublecircle')
                self.estados_aceptacion.add(nombre)
            else:
                dot.node(nombre)

        for _, (estado, _) in self.Dstates.items():
            for simbolo, dest_state in estado.transiciones.items():
                ordChar = simbolo
                convert = False
                if ordChar in range(0, 33) or ordChar in range(127, 256) or ordChar == 92:
                    ordChar = "o:" + str(ordChar)
                    convert = True
                simbolo = str(simbolo)
                self.alfabeto.add(simbolo)
                if estado.nombre not in self.transiciones:
                    self.transiciones[estado.nombre] = {simbolo: dest_state.nombre}
                elif simbolo not in self.transiciones[estado.nombre]:
                    self.transiciones[estado.nombre][simbolo] = dest_state.nombre
                else:
                    self.transiciones[estado.nombre][simbolo].append(dest_state.nombre)
                dot.edge(estado.nombre, dest_state.nombre, label=chr(ordChar) if not convert else ordChar)
                #dot.edge(estado.nombre, dest_state.nombre, label=simbolo)

        self.estado_inicial = next(iter(self.Dstates))
        dot.edge('start', self.estado_inicial, style='bold')

        # Visualizar el gráfico
        if option == 1:
            dot.render('./bin/lib/dirafd/afd_directo', view=True)

        self.exportar_json()
        return dot

    def exportar_json(self, archivo='./bin/directAfd.json'):
        """
        Funcion que genera un archivo .json para representar el afd
        :param archivo:
        """
        afd_dict = {
            "estados": list(self.estados),
            "alfabeto": list(self.alfabeto),
            "estadoInicial": self.estado_inicial,
            "estadosFinales": list(self.estados_aceptacion),
            "transiciones": self.transiciones
        }
        with open(archivo, 'w', encoding="utf-8") as f:
            json.dump(afd_dict, f, indent=4, ensure_ascii=False)

    def simulateDirectAFD(self, string):
        """
        Funcion que simula el Automata Finito Determinista de construccion directa.
        :param string: Cadena a simular
        :return: Metodo simulateDFA con la cadena y los elementos del AFD directo.
        """
        return simulateDFA(string=string, initialState=self.estado_inicial, finalStates=self.estados_aceptacion,
                           transitions=self.transiciones)

    def stepDirectAFD(self, char, currState):
        """
        Funcion que simula el Automata Finito Determinista de construccion directa.
        :param char: Cadena a simular
        :return: Metodo step con el caracter y los elementos del AFD directo.
        """
        return step(char=char, currState=currState, transitions=self.transiciones)
        #return move(s=currState, c=str(char), transitions=self.transiciones)

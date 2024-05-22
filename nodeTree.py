from graphviz import Digraph


class Nodo:
    def __init__(self, valor, izquierdo=None, derecho=None, leafNum=None, nullability=False, firstpos=set(),
                 lastpos=set()):
        """
        Funcion constructora de un objeto Nodo utilizado dentro del arbol de nodos.
        :param valor: El caracter que representa este nodo
        :param izquierdo: El nodo hijo izquierdo
        :param derecho: El nodo hijo derecho
        :param leafNum: El numero de hoja que este nodo es, o None si no es una hoja
        :param nullability: Booleano representando si el nodo es anulable o no
        :param firstpos: La posicion inicial del nodo
        :param lastpos: La ultima posicion alcanzable del nodo.
        """
        self.valor = valor
        self.izquierdo = izquierdo
        self.derecho = derecho
        self.leaf = leafNum
        self.nullability = nullability
        self.firstpos = firstpos
        self.lastpos = lastpos
        self.followpos = {}

    def repr(self):
        """
        Funcion que genera una representacion del nodo
        :return:
        - String con el valor del nodo.
        """
        # strs = {"Valor": self.valor, "Firstpos": self.firstpos, "Lastpos": self.lastpos, "Followpos": self.followpos}
        # if self.leaf:
        #     strs["Leaf"] = self.leaf
        # return str(strs)
        valor = self.valor
        if isinstance(self.valor, int) and self.valor in range(0, 33) or self.valor in range(127, 256) or self.valor == 92:
            valor = "ord: " + str(self.valor)
        elif isinstance(self.valor, int):
            valor = chr(self.valor)
        return str(valor)


def alphanum(a):
    """
    Funcion que determina si un caracter a es alfanumerico, un epsilon o un #
    :param a: Caracter a evalua
    :return: Booleano si el caracter es aceptado o no
    """
    return a.isalpha() or a.isnumeric() or a == "ε"# or a == "#" or a not in "+*?|·^()[]_"


class ArbolExpresion:
    def __init__(self, regex):
        """
        Funcion constructora del arbol de nodos en base a una expresion Regex en formato posfix
        :param regex: Expresion regex a evaluar
        """
        self.regex = regex
        self.regex.append("#")
        self.regex.append("·")
        self.pila = []
        self.raiz = None
        self.simbolos = []
        self.count = 1
        self.construir_arbol()

    def construir_arbol(self):
        """
        Funcion constructora del arbol de nodos. Determina la nulabilidad de cada nodo, su firstpos y su lastpos
        dependiendo de que tipo de valor tenga el nodo, ademas adjunta cada nodo a su nodo padre y los ingresa a una
        pila. Encuentra el nodo raiz del arbol y luego genera los followpos para cada hoja del arbol.
        """
        for char in self.regex:
            canBeNull = False
            firstpos = None
            lastpos = None
            if isinstance(char, int) or char == "#":
                if isinstance(char, int) and chr(char) == "ε":
                    canBeNull = True
                #elif char.isalpha() or char.isnumeric() or char == "#":
                else:
                    firstpos = {self.count}
                    lastpos = {self.count}
                self.pila.append(self.create_leaf(valor=char, nullable=canBeNull, firstpos=firstpos, lastpos=lastpos))
            elif char in '*|·':
                if char == '*':
                    canBeNull = True
                    n1 = self.pila.pop()
                    self.pila.append(Nodo(char, n1, nullability=canBeNull, firstpos=n1.firstpos, lastpos=n1.lastpos))
                else:
                    n2 = self.pila.pop()
                    n1 = self.pila.pop()
                    if char == '|':
                        firstpos = n1.firstpos.union(n2.firstpos)
                        lastpos = n2.lastpos.union(n1.lastpos)
                        canBeNull = True if n1.nullability or n2.nullability else False
                    else:
                        canBeNull = True if n1.nullability and n2.nullability else False
                        firstpos = n1.firstpos
                        lastpos = n2.lastpos
                        if n1.nullability:
                            firstpos = n1.firstpos.union(n2.firstpos)
                        if n2.nullability:
                            lastpos = n2.lastpos.union(n1.lastpos)

                    self.pila.append(
                        Nodo(valor=char, izquierdo=n1, derecho=n2, nullability=canBeNull, firstpos=firstpos,
                             lastpos=lastpos))
        self.raiz = self.pila.pop()
        self.calcular_followpos()

    def create_leaf(self, valor, nullable=False, firstpos=None, lastpos=None):
        """
        Funcion que genera las hojas del arbol
        :param valor: Valor que tendra el nodo
        :param nullable: Si el nodo es anulable o no
        :param firstpos: La primer posicion alcanzable del nodo
        :param lastpos: La ultima posicion alcanzable del nodo
        :return:
        - nodo : Nodo generado en base a los parametros y el valor del conteo.
        """
        if lastpos is None:
            lastpos = set()
        if firstpos is None:
            firstpos = set()
        nodo = Nodo(valor, leafNum=self.count, nullability=nullable, firstpos=firstpos, lastpos=lastpos)
        self.simbolos.append(nodo)
        self.count += 1
        return nodo

    def calcular_followpos(self):
        """
        Funcion que calcula los followpos de cada nodo hoja. Estos se generan dependiendo de las firstpos y lastpos del
        nodo, de su nodo padre y sus nodo hermanos.
        """
        def visitar(nodo):
            """
            Funcion interna de calcular_followpos, recorre el arbol de nodos determinando la followpos de cada hoja
            de manera recursiva.
            :param nodo: nodo a recorrer
            """
            if nodo.valor == '·':
                for pos in nodo.izquierdo.lastpos:
                    # Asegúrate de inicializar followpos como un set si aún no se ha hecho
                    if self.simbolos[pos-1].followpos is None:
                        self.simbolos[pos-1].followpos = set()
                    self.simbolos[pos-1].followpos.update(nodo.derecho.firstpos)
            elif nodo.valor == '*':
                for pos in nodo.lastpos:
                    # Asegúrate de inicializar followpos como un set si aún no se ha hecho
                    if self.simbolos[pos-1].followpos is None:
                        self.simbolos[pos-1].followpos = set()
                    self.simbolos[pos-1].followpos.update(nodo.firstpos)

            if nodo.izquierdo:
                visitar(nodo.izquierdo)
            if nodo.derecho:
                visitar(nodo.derecho)

        # Inicializa followpos para cada símbolo como un set vacío
        for simbolo in self.simbolos:
            if isinstance(simbolo, Nodo):
                simbolo.followpos = set()
        visitar(self.raiz)

    def visualizar_arbol(self):
        """
        Funcion que genera utilizando la libreria Graphviz para crear una visualización del arbol de nodos generado.
        """
        def agregar_nodos_edges(raiz, dot=None):
            """
            Funcion interna de visualizar_arbol, esta funcion recorre los nodos y agrega el nodo al digrafo que será
            visualizado
            :param raiz: Nodo a recorer
            :param dot: dot de Digrafo utilizado para representar el arbol
            :return:
            - dot : Digraph del arbol de nodos
            """
            if dot is None:
                dot = Digraph()
                dot.node(name=str(raiz), label=str(raiz.repr()))

            if raiz.izquierdo:
                dot.node(name=str(raiz.izquierdo), label=str(raiz.izquierdo.repr()))
                dot.edge(str(raiz), str(raiz.izquierdo))
                agregar_nodos_edges(raiz.izquierdo, dot=dot)

            if raiz.derecho:
                dot.node(name=str(raiz.derecho), label=str(raiz.derecho.repr()))
                dot.edge(str(raiz), str(raiz.derecho))
                agregar_nodos_edges(raiz.derecho, dot=dot)

            return dot

        dot = agregar_nodos_edges(self.raiz)
        dot.render('./bin/lib/tree/arbol_expresion', view=True)  # Guarda y abre la imagen del árbol

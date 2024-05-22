from time import time
from shunthingYard import validation
from automaton import Automaton
import pickle
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from scannerWriter import ScannerWriter
from L0Auto import AutomataLR0

def yalexReader(yalexContent):
    tokens = {
        "encabezado": "{\s*(['!'-'z']+|.|=|\s*)*\s*}",
        "comentarios": "\(\*[^'\x01'-'\x1F']*\*\)",
        "variables": "let\s*(['a'-'z''A'-'Z']+)?\s*=?\s*([^'\x01'-'\x1F']#['\x7E'-'\xFF'])*",
        "rules": "rule\s*(['A'-'Z''a'-'z'])+\s*=\s*((\s*|(\\'|\\\")|['\x21'-'\xFF']+)(\s*{ *(_)* *}\s*)?(\s*\(\*[^'\x01'-'\x1F']*\*\)\s*)?)+"
    }

    automaton = Automaton(tokens, option=0) 

    iChar = 0
    while iChar < len(yalexContent):
        char = yalexContent[iChar]
        nextChar = yalexContent[iChar + 1] if iChar + 1 < len(yalexContent) else None
        automaton.simulateAfds(ord(char), nextChar)
        iChar += 1
    
    parse = automaton.parseVariables()
    if parse is not None:
        print(parse)
        return -1

    regex = automaton.getFirstRegex()
    if regex.startswith("\033[31mError:\033[0m"):
        print(regex)
        return -1
    
    regex = automaton.replaceVariables(regex)
    print(f"\033[1;36mRegex obtenido desde el archivo YALex:\n\033[0m{regex}")
    
    validateRegex = validation(regex)
    if validateRegex is not None:
        print("\t\033[31mERROR. {}\033[0m".format(validateRegex["desc"]))
        return -1
    
    pickeFile = 'automaton.pkl'
    with open(pickeFile, 'wb') as output:
        pickle.dump(automaton, output, pickle.HIGHEST_PROTOCOL)

    return regex, pickeFile

def cargar_archivo():
    archivo = filedialog.askopenfilename(filetypes=[("Archivos YALex", "*.yal")])
    if archivo:  # Verifica si se seleccionó un archivo
        try:
            with open(archivo, 'r') as f:
                contenido = f.read()  # Lee el contenido del archivo
                texto_yalex1.delete('1.0', tk.END)  # Borra el contenido actual del campo de texto
                texto_yalex1.insert(tk.END, contenido)  # Inserta el contenido del archivo en el campo de texto
        except Exception as e:
            tk.messagebox.showerror("\t\033[31mError", f"No se pudo abrir el archivo: {str(e)}")

def cargar_archivo_yapar():
    archivo = filedialog.askopenfilename(filetypes=[("Archivos YAPar", "*.yalp")])
    if archivo:  # Verifica si se seleccionó un archivo
        try:
            with open(archivo, 'r') as f:
                contenido = f.read()  # Lee el contenido del archivo
                texto_yalex2.delete('1.0', tk.END)  # Borra el contenido actual del campo de texto
                texto_yalex2.insert(tk.END, contenido)  # Inserta el contenido del archivo en el campo de texto
        except Exception as e:
            tk.messagebox.showerror("\t\033[31mError", f"No se pudo abrir el archivo: {str(e)}")

def procesar():
    yalex = texto_yalex1.get('1.0', tk.END)
    yalp= texto_yalex2.get('1.0', tk.END)
    main(yalex, yalp)

def escribir_en_texto_yalex3(texto):
    texto_yalex3.config(state='normal')
    texto_yalex3.insert(tk.END, texto + "\n")
    texto_yalex3.config(state='disabled')

def escribir_en_texto_yalex4(texto):
    texto_yalex4.config(state='normal')
    texto_yalex4.insert(tk.END, texto + "\n")
    texto_yalex4.config(state='disabled')

def main(yalexFile, yaplFile):
    """
    Funcion principal del programa, se encarga de ejecutar el programa principal
    :return:
        -  0 : Si el programa se ejecuta correctamente
        - -1 : Si el programa se encuentra un error durante su ejecucion
    """
    yalexResult = yalexReader(yalexFile)
    if yalexResult == -1:
        return -1
    
    regex, pickeFile = yalexResult
    
    print(f"\033[1;36m---------Creacion del archivo Scanner---------------\033[0m")
    scannerWriter = ScannerWriter(pickeFile)
    writerResult = scannerWriter.createScanner()
    if writerResult == -1:
        return -1
    
    print("\033[32mArchivo creado con éxito\033[0m")
    
    print(f"\033[1;36m\n---------Inicio de automata LR(0)---------------\n\033[0m")
    
    automaton = AutomataLR0(pickeFile, log_function=escribir_en_texto_yalex3, log_function2=escribir_en_texto_yalex4)

    readYalp = automaton.readFile(yaplFile)
    if readYalp == -1:
        return -1
    
    print("\033[32mArchivo Yalp leído con éxito\033[0m")
    print("\nTransitions numbers:", len(automaton.transitions))

    return 0

if __name__ == '__main__':
    # Crear la ventana principal
    ventana = tk.Tk()
    ventana.title("Interfaz YALex")

    # Marco para el primer cuadro de texto y botones
    frame1 = tk.Frame(ventana)
    frame1.pack(side=tk.LEFT, padx=5, pady=5)

    # Primer cuadro de texto
    texto_yalex1 = tk.Text(frame1, height=35, width=45)
    texto_yalex1.pack()

    # Botones para el primer cuadro de texto
    boton_procesar1 = tk.Button(frame1, text="Procesar", command=procesar)
    boton_procesar1.pack(side=tk.LEFT, padx=5, pady=5)

    boton_cargar1 = tk.Button(frame1, text="Cargar archivo", command=cargar_archivo)
    boton_cargar1.pack(side=tk.LEFT, padx=5, pady=5)

    # Marco para el segundo cuadro de texto y botones
    frame2 = tk.Frame(ventana)
    frame2.pack(side=tk.LEFT, padx=5, pady=5)

    # Segundo cuadro de texto
    texto_yalex2 = tk.Text(frame2, height=35, width=45)
    texto_yalex2.pack()

    boton_cargar2 = tk.Button(frame2, text="Cargar archivo", command=cargar_archivo_yapar)
    boton_cargar2.pack(side=tk.LEFT, padx=5, pady=5)

    main_frame = tk.Frame(ventana)
    main_frame.pack(side=tk.LEFT, padx=5, pady=5)

    # Marco para el tercer cuadro de texto de solo lectura
    frame3 = tk.Frame(main_frame)
    frame3.grid(row=0, column=0, padx=5, pady=5)

    # Tercer cuadro de texto de solo lectura
    texto_yalex3 = tk.Text(frame3, height=30, width=65)
    texto_yalex3.pack()
    texto_yalex3.config(state='disabled')

    frame4 = tk.Frame(main_frame)
    frame4.grid(row=1, column=0, padx=5, pady=5)

    # Tercer cuadro de texto de solo lectura
    texto_yalex4 = tk.Text(frame4, height=10, width=65)
    texto_yalex4.pack()
    texto_yalex4.config(state='disabled')

    # Ejecutar la aplicación
    ventana.mainloop()

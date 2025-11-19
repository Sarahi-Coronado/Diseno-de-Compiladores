import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
import os
from typing import List, Tuple, Dict, Any

class Token:
    def __init__(self, tipo: str, valor: str, linea: int, columna: int):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna
    
    def __repr__(self):
        return f"Token({self.tipo}, '{self.valor}', {self.linea}, {self.columna})"

class AnalizadorLexico:
    def __init__(self):
        self.tokens = []
        self.errores = []
        
        # Patrones para tokens - SOLO los de la gramática oficial
        self.patrones = [
            ('COMENTARIO', r'//.*?//'),
            ('ASIGNACION', r':='),
            ('PUNTO_PUNTO', r'\.\.'),
            ('OR', r'\|\|'),
            ('AND', r'&&'),
            ('NO_IGUAL', r'!='),
            ('MENOR_IGUAL', r'<='),
            ('MAYOR_IGUAL', r'>='),
            ('PROGRAM', r'\bprogram\b'),
            ('BEGIN', r'\bbegin\b'),
            ('END', r'\bend\b'),
            ('TYPE', r'\btype\b'),
            ('VAR', r'\bvar\b'),
            ('PROCEDURE', r'\bprocedure\b'),
            ('FUNCTION', r'\bfunction\b'),
            ('IF', r'\bif\b'),
            ('THEN', r'\bthen\b'),
            ('ELSE', r'\belse\b'),
            ('WHILE', r'\bwhile\b'),
            ('DO', r'\bdo\b'),
            ('INTEGER', r'\binteger\b'),
            ('BOOLEAN', r'\bboolean\b'),
            ('STRING', r'\bstring\b'),
            ('ARRAY', r'\barray\b'),
            ('OF', r'\bof\b'),
            ('TRUE', r'\btrue\b'),
            ('FALSE', r'\bfalse\b'),
            ('NUM', r'\d+(\.\d+)?([eE][-+]?\d+)?'),
            ('STRING_LIT', r'\"[^\"]*\"'),
            ('ID', r'[a-zA-Z_][a-zA-Z0-9_]*'),
            ('PUNTO', r'\.'),
            ('COMA', r','),
            ('PUNTO_COMA', r';'),
            ('DOS_PUNTOS', r':'),
            ('PARENTESIS_IZQ', r'\('),
            ('PARENTESIS_DER', r'\)'),
            ('CORCHETE_IZQ', r'\['),
            ('CORCHETE_DER', r'\]'),
            ('IGUAL', r'='),
            ('MENOR', r'<'),
            ('MAYOR', r'>'),
            ('SUMA', r'\+'),
            ('RESTA', r'-'),
            ('MULTIPLICACION', r'\*'),
            ('DIVISION', r'/'),
            ('MODULO', r'%'),
            ('NEGACION', r'!'),
        ]
    
    def analizar(self, codigo: str) -> Tuple[List[Token], List[str]]:
        self.tokens = []
        self.errores = []
        
        lineas = codigo.split('\n')
        numero_linea = 1
        
        for numero_linea, linea in enumerate(lineas, 1):
            posicion = 0
            while posicion < len(linea):
                # Saltar espacios
                if linea[posicion].isspace():
                    posicion += 1
                    continue
                
                encontrado = False
                
                # Buscar patrones
                for tipo_patron, patron in self.patrones:
                    regex = re.compile(patron)
                    match = regex.match(linea, posicion)
                    
                    if match:
                        valor = match.group()
                        # Ignorar comentarios
                        if tipo_patron == 'COMENTARIO':
                            posicion = match.end()
                            encontrado = True
                            break
                        
                        # Crear token
                        token = Token(tipo_patron, valor, numero_linea, posicion + 1)
                        self.tokens.append(token)
                        posicion = match.end()
                        encontrado = True
                        break
                
                if not encontrado:
                    # Carácter no reconocido
                    error = f"Error léxico en línea {numero_linea}, columna {posicion + 1}: Carácter '{linea[posicion]}' no reconocido"
                    self.errores.append(error)
                    posicion += 1
        
        # Agregar token EOF
        if self.tokens and self.tokens[-1].tipo != 'EOF':
            self.tokens.append(Token('EOF', '', numero_linea + 1, 1))
        
        return self.tokens, self.errores

class NodoAST:
    def __init__(self, tipo: str, valor: str = "", hijos: List[Any] = None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = hijos if hijos is not None else []
    
    def agregar_hijo(self, hijo):
        self.hijos.append(hijo)
    
    def __repr__(self):
        if self.valor:
            return f"{self.tipo}({self.valor})"
        return f"{self.tipo}"

class AnalizadorSintactico:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.posicion = 0
        self.errores = []
        self.ast = None
    
    def token_actual(self) -> Token:
        if self.posicion < len(self.tokens):
            return self.tokens[self.posicion]
        return None
    
    def avanzar(self):
        if self.posicion < len(self.tokens):
            self.posicion += 1
    
    def coincidir(self, tipo_esperado: str) -> bool:
        token = self.token_actual()
        if token and token.tipo == tipo_esperado:
            self.avanzar()
            return True
        return False
    
    def error(self, mensaje: str):
        token = self.token_actual()
        if token:
            self.errores.append(f"Error sintáctico en línea {token.linea}, columna {token.columna}: {mensaje}. Se encontró: '{token.valor}'")
        else:
            self.errores.append(f"Error sintáctico: {mensaje}")
    
    def esperar(self, tipo_esperado: str, mensaje: str) -> bool:
        if self.coincidir(tipo_esperado):
            return True
        else:
            self.error(mensaje)
            return False
    
    def analizar(self) -> bool:
        try:
            self.ast = self.program()
            # Verificar que no queden tokens sin procesar (excepto EOF)
            token_restante = self.token_actual()
            if token_restante and token_restante.tipo != 'EOF':
                self.error(f"Se esperaba fin de programa, pero hay tokens adicionales")
                return False
            return len(self.errores) == 0
        except Exception as e:
            self.errores.append(f"Error durante el análisis: {str(e)}")
            return False
    
    # Gramática: Program → program ID ';' DeclsOpt begin StmtList end '.' EOF
    def program(self) -> NodoAST:
        nodo = NodoAST("Program")
        
        if not self.esperar('PROGRAM', "Se esperaba 'program'"):
            return nodo
        
        token_id = self.token_actual()
        if not self.esperar('ID', "Se esperaba un identificador después de 'program'"):
            return nodo
        
        nodo.agregar_hijo(NodoAST("ID", token_id.valor))
        
        if not self.esperar('PUNTO_COMA', "Se esperaba ';' después del identificador del programa"):
            return nodo
        
        # DeclsOpt
        nodo_decls = self.decls_opt()
        if nodo_decls:
            nodo.agregar_hijo(nodo_decls)
        
        if not self.esperar('BEGIN', "Se esperaba 'begin'"):
            return nodo
        
        # StmtList
        nodo_stmts = self.stmt_list()
        if nodo_stmts:
            nodo.agregar_hijo(nodo_stmts)
        
        if not self.esperar('END', "Se esperaba 'end'"):
            return nodo
        
        if not self.esperar('PUNTO', "Se esperaba '.' al final del programa"):
            return nodo
        
        return nodo
    
    def decls_opt(self) -> NodoAST:
        # DeclsOpt → Decls | ε
        nodo_decls = self.decls()
        if nodo_decls and nodo_decls.hijos:
            return nodo_decls
        return None
    
    def decls(self) -> NodoAST:
        # Decls → Decl Decls | Decl
        nodo = NodoAST("Decls")
        
        nodo_decl = self.decl()
        if nodo_decl:
            nodo.agregar_hijo(nodo_decl)
            # Intentar obtener más declaraciones
            nodo_mas_decls = self.decls()
            if nodo_mas_decls and nodo_mas_decls.hijos:
                for hijo in nodo_mas_decls.hijos:
                    nodo.agregar_hijo(hijo)
        
        return nodo
    
    def decl(self) -> NodoAST:
        # Decl → TypeSection | VarSection | SubprogDecl
        token = self.token_actual()
        if not token:
            return None
        
        if token.tipo == 'TYPE':
            return self.type_section()
        elif token.tipo == 'VAR':
            return self.var_section()
        elif token.tipo in ['PROCEDURE', 'FUNCTION']:
            return self.subprog_decl()
        
        return None
    
    def type_section(self) -> NodoAST:
        # TypeSection → type TypeDefList
        nodo = NodoAST("TypeSection")
        
        if not self.coincidir('TYPE'):
            return None
        
        nodo_type_def = self.type_def_list()
        if nodo_type_def:
            nodo.agregar_hijo(nodo_type_def)
        
        return nodo
    
    def type_def_list(self) -> NodoAST:
        # TypeDefList → TypeDef TypeDefListTail
        nodo = NodoAST("TypeDefList")
        
        nodo_type_def = self.type_def()
        if nodo_type_def:
            nodo.agregar_hijo(nodo_type_def)
        
        nodo_tail = self.type_def_list_tail()
        if nodo_tail:
            nodo.agregar_hijo(nodo_tail)
        
        return nodo
    
    def type_def_list_tail(self) -> NodoAST:
        # TypeDefListTail → ';' TypeDef TypeDefListTail | ';'
        if self.coincidir('PUNTO_COMA'):
            nodo = NodoAST("TypeDefListTail")
            
            # Verificar si hay más type definitions
            nodo_type_def = self.type_def()
            if nodo_type_def:
                nodo.agregar_hijo(nodo_type_def)
                
                nodo_tail = self.type_def_list_tail()
                if nodo_tail:
                    nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None
    
    def type_def(self) -> NodoAST:
        # TypeDef → ID '=' Type
        nodo = NodoAST("TypeDef")
        
        token_id = self.token_actual()
        if not self.coincidir('ID'):
            return None
        
        nodo.agregar_hijo(NodoAST("ID", token_id.valor))
        
        if not self.esperar('IGUAL', "Se esperaba '=' en la definición de tipo"):
            return nodo
        
        nodo_type = self.type()
        if nodo_type:
            nodo.agregar_hijo(nodo_type)
        
        return nodo
    
    def type(self) -> NodoAST:
        # Type → SimpleType | ArrayType | NamedType
        token = self.token_actual()
        if not token:
            return None
        
        if token.tipo in ['INTEGER', 'BOOLEAN', 'STRING']:
            return self.simple_type()
        elif token.tipo == 'ARRAY':
            return self.array_type()
        elif token.tipo == 'ID':
            return self.named_type()
        
        self.error("Se esperaba un tipo (integer, boolean, string, array o tipo definido)")
        return None
    
    def simple_type(self) -> NodoAST:
        # SimpleType → integer | boolean | string
        token = self.token_actual()
        if token and token.tipo in ['INTEGER', 'BOOLEAN', 'STRING']:
            nodo = NodoAST("SimpleType", token.valor)
            self.avanzar()
            return nodo
        return None
    
    def array_type(self) -> NodoAST:
        # ArrayType → array '[' NUM '..' NUM ']' of Type
        nodo = NodoAST("ArrayType")
        
        if not self.coincidir('ARRAY'):
            return None
        
        if not self.esperar('CORCHETE_IZQ', "Se esperaba '[' después de array"):
            return nodo
        
        token_num1 = self.token_actual()
        if not self.esperar('NUM', "Se esperaba un número para el límite inferior del array"):
            return nodo
        
        nodo.agregar_hijo(NodoAST("NUM", token_num1.valor))
        
        if not self.esperar('PUNTO_PUNTO', "Se esperaba '..' entre los límites del array"):
            return nodo
        
        token_num2 = self.token_actual()
        if not self.esperar('NUM', "Se esperaba un número para el límite superior del array"):
            return nodo
        
        nodo.agregar_hijo(NodoAST("NUM", token_num2.valor))
        
        if not self.esperar('CORCHETE_DER', "Se esperaba ']' después de los límites del array"):
            return nodo
        
        if not self.esperar('OF', "Se esperaba 'of' después de la definición del array"):
            return nodo
        
        nodo_type = self.type()
        if nodo_type:
            nodo.agregar_hijo(nodo_type)
        
        return nodo
    
    def named_type(self) -> NodoAST:
        # NamedType → ID
        token = self.token_actual()
        if token and token.tipo == 'ID':
            nodo = NodoAST("NamedType", token.valor)
            self.avanzar()
            return nodo
        return None
    
    def var_section(self) -> NodoAST:
        # VarSection → var VarDefList
        nodo = NodoAST("VarSection")
        
        if not self.coincidir('VAR'):
            return None
        
        nodo_var_def = self.var_def_list()
        if nodo_var_def:
            nodo.agregar_hijo(nodo_var_def)
        
        return nodo
    
    def var_def_list(self) -> NodoAST:
        # VarDefList → VarDef VarDefListTail
        nodo = NodoAST("VarDefList")
        
        nodo_var_def = self.var_def()
        if nodo_var_def:
            nodo.agregar_hijo(nodo_var_def)
        
        nodo_tail = self.var_def_list_tail()
        if nodo_tail:
            nodo.agregar_hijo(nodo_tail)
        
        return nodo
    
    def var_def_list_tail(self) -> NodoAST:
        # VarDefListTail → ';' VarDef VarDefListTail | ';'
        if self.coincidir('PUNTO_COMA'):
            nodo = NodoAST("VarDefListTail")
            
            # Verificar si hay más definiciones de variables
            nodo_var_def = self.var_def()
            if nodo_var_def:
                nodo.agregar_hijo(nodo_var_def)
                
                nodo_tail = self.var_def_list_tail()
                if nodo_tail:
                    nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None
    
    def var_def(self) -> NodoAST:
        # VarDef → IdList ':' Type
        nodo = NodoAST("VarDef")
        
        nodo_id_list = self.id_list()
        if nodo_id_list:
            nodo.agregar_hijo(nodo_id_list)
        else:
            return None
        
        if not self.esperar('DOS_PUNTOS', "Se esperaba ':' después de la lista de identificadores"):
            return nodo
        
        nodo_type = self.type()
        if nodo_type:
            nodo.agregar_hijo(nodo_type)
        
        return nodo
    
    def id_list(self) -> NodoAST:
        # IdList → ID IdListTail
        nodo = NodoAST("IdList")
        
        token_id = self.token_actual()
        if not self.coincidir('ID'):
            return None
        
        nodo.agregar_hijo(NodoAST("ID", token_id.valor))
        
        nodo_tail = self.id_list_tail()
        if nodo_tail:
            nodo.agregar_hijo(nodo_tail)
        
        return nodo
    
    def id_list_tail(self) -> NodoAST:
        # IdListTail → ',' ID IdListTail | ε
        if self.coincidir('COMA'):
            nodo = NodoAST("IdListTail")
            
            token_id = self.token_actual()
            if not self.coincidir('ID'):
                self.error("Se esperaba un identificador después de ','")
                return nodo
            
            nodo.agregar_hijo(NodoAST("ID", token_id.valor))
            
            nodo_tail = self.id_list_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None
    
    def subprog_decl(self) -> NodoAST:
        # SubprogDecl → ProcedureDecl | FunctionDecl
        token = self.token_actual()
        if not token:
            return None
        
        if token.tipo == 'PROCEDURE':
            return self.procedure_decl()
        elif token.tipo == 'FUNCTION':
            return self.function_decl()
        
        return None
    
    def procedure_decl(self) -> NodoAST:
        # ProcedureDecl → procedure ID '(' ParamSectionOpt ')' ';' Block ';'
        nodo = NodoAST("ProcedureDecl")
        
        if not self.coincidir('PROCEDURE'):
            return None
        
        token_id = self.token_actual()
        if not self.esperar('ID', "Se esperaba un identificador para el procedimiento"):
            return nodo
        
        nodo.agregar_hijo(NodoAST("ID", token_id.valor))
        
        if not self.esperar('PARENTESIS_IZQ', "Se esperaba '(' después del nombre del procedimiento"):
            return nodo
        
        nodo_params = self.param_section_opt()
        if nodo_params:
            nodo.agregar_hijo(nodo_params)
        
        if not self.esperar('PARENTESIS_DER', "Se esperaba ')' después de los parámetros"):
            return nodo
        
        if not self.esperar('PUNTO_COMA', "Se esperaba ';' después de los parámetros del procedimiento"):
            return nodo
        
        nodo_block = self.block()
        if nodo_block:
            nodo.agregar_hijo(nodo_block)
        
        if not self.esperar('PUNTO_COMA', "Se esperaba ';' después del bloque del procedimiento"):
            return nodo
        
        return nodo
    
    def function_decl(self) -> NodoAST:
        # FunctionDecl → function ID '(' ParamSectionOpt ')' ';' Type ';' Block ';'
        nodo = NodoAST("FunctionDecl")
        
        if not self.coincidir('FUNCTION'):
            return None
        
        token_id = self.token_actual()
        if not self.esperar('ID', "Se esperaba un identificador para la función"):
            return nodo
        
        nodo.agregar_hijo(NodoAST("ID", token_id.valor))
        
        if not self.esperar('PARENTESIS_IZQ', "Se esperaba '(' después del nombre de la función"):
            return nodo
        
        nodo_params = self.param_section_opt()
        if nodo_params:
            nodo.agregar_hijo(nodo_params)
        
        if not self.esperar('PARENTESIS_DER', "Se esperaba ')' después de los parámetros"):
            return nodo
        
        if not self.esperar('PUNTO_COMA', "Se esperaba ';' después de los parámetros de la función"):
            return nodo
        
        nodo_type = self.type()
        if nodo_type:
            nodo.agregar_hijo(nodo_type)
        
        if not self.esperar('PUNTO_COMA', "Se esperaba ';' después del tipo de retorno"):
            return nodo
        
        nodo_block = self.block()
        if nodo_block:
            nodo.agregar_hijo(nodo_block)
        
        if not self.esperar('PUNTO_COMA', "Se esperaba ';' después del bloque de la función"):
            return nodo
        
        return nodo
    
    def param_section_opt(self) -> NodoAST:
        # ParamSectionOpt → ParamSection | ε
        if self.token_actual() and self.token_actual().tipo == 'ID':
            return self.param_section()
        return None
    
    def param_section(self) -> NodoAST:
        # ParamSection → ParamGroup ParamSectionTail
        nodo = NodoAST("ParamSection")
        
        nodo_group = self.param_group()
        if nodo_group:
            nodo.agregar_hijo(nodo_group)
        
        nodo_tail = self.param_section_tail()
        if nodo_tail:
            nodo.agregar_hijo(nodo_tail)
        
        return nodo
    
    def param_section_tail(self) -> NodoAST:
        # ParamSectionTail → ';' ParamGroup ParamSectionTail | ε
        if self.coincidir('PUNTO_COMA'):
            nodo = NodoAST("ParamSectionTail")
            
            nodo_group = self.param_group()
            if nodo_group:
                nodo.agregar_hijo(nodo_group)
            
            nodo_tail = self.param_section_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None
    
    def param_group(self) -> NodoAST:
        # ParamGroup → IdList ':' Type
        nodo = NodoAST("ParamGroup")
        
        nodo_id_list = self.id_list()
        if nodo_id_list:
            nodo.agregar_hijo(nodo_id_list)
        else:
            return None
        
        if not self.esperar('DOS_PUNTOS', "Se esperaba ':' después de la lista de parámetros"):
            return nodo
        
        nodo_type = self.type()
        if nodo_type:
            nodo.agregar_hijo(nodo_type)
        
        return nodo
    
    def block(self) -> NodoAST:
        # Block → DeclSOpt begin StmtList end
        nodo = NodoAST("Block")
        
        nodo_decls = self.decls_opt()
        if nodo_decls:
            nodo.agregar_hijo(nodo_decls)
        
        if not self.esperar('BEGIN', "Se esperaba 'begin' en el bloque"):
            return nodo
        
        nodo_stmts = self.stmt_list()
        if nodo_stmts:
            nodo.agregar_hijo(nodo_stmts)
        
        if not self.esperar('END', "Se esperaba 'end' en el bloque"):
            return nodo
        
        return nodo
    
    def stmt_list(self) -> NodoAST:
        # StmtList → Stmt StmtListTail
        nodo = NodoAST("StmtList")
        
        nodo_stmt = self.stmt()
        if nodo_stmt:
            nodo.agregar_hijo(nodo_stmt)
        
        nodo_tail = self.stmt_list_tail()
        if nodo_tail:
            nodo.agregar_hijo(nodo_tail)
        
        return nodo
    
    def stmt_list_tail(self) -> NodoAST:
        # StmtListTail → ';' Stmt StmtListTail | ε
        if self.coincidir('PUNTO_COMA'):
            nodo = NodoAST("StmtListTail")
            
            nodo_stmt = self.stmt()
            if nodo_stmt:
                nodo.agregar_hijo(nodo_stmt)
            
            nodo_tail = self.stmt_list_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None
    
    def stmt(self) -> NodoAST:
        # Stmt → AssignStmt | WhileStmt | CallStmt | IfStmt | Block | ε
        token = self.token_actual()
        if not token:
            return None
        
        # Guardar posición para backtracking
        pos_anterior = self.posicion
        
        if token.tipo == 'ID':
            # Podría ser AssignStmt o CallStmt
            # Intentar como variable (para asignación)
            resultado = self.variable()
            if resultado:
                # Verificar si sigue asignación
                if self.token_actual() and self.token_actual().tipo == 'ASIGNACION':
                    self.posicion = pos_anterior
                    return self.assign_stmt()
                else:
                    # Es CallStmt
                    self.posicion = pos_anterior
                    return self.call_stmt()
            
        elif token.tipo == 'WHILE':
            return self.while_stmt()
        elif token.tipo == 'IF':
            return self.if_stmt()
        elif token.tipo == 'BEGIN':
            return self.block()
        
        # ε producción - declaración vacía
        return None
    
    def assign_stmt(self) -> NodoAST:
        # AssignStmt → Variable ':=' Expr
        nodo = NodoAST("AssignStmt")
        
        nodo_variable = self.variable()
        if not nodo_variable:
            return None
        
        nodo.agregar_hijo(nodo_variable)
        
        if not self.esperar('ASIGNACION', "Se esperaba ':=' en la asignación"):
            return None
        
        nodo_expr = self.expr()
        if nodo_expr:
            nodo.agregar_hijo(nodo_expr)
        else:
            self.error("Se esperaba una expresión después de ':='")
            return None
        
        return nodo
    
    def variable(self) -> NodoAST:
        # Variable → ID VariableTail
        nodo = NodoAST("Variable")
        
        token_id = self.token_actual()
        if not self.coincidir('ID'):
            return None
        
        nodo.agregar_hijo(NodoAST("ID", token_id.valor))
        
        nodo_tail = self.variable_tail()
        if nodo_tail:
            nodo.agregar_hijo(nodo_tail)
        
        return nodo
    
    def variable_tail(self) -> NodoAST:
        # VariableTail → '[' Expr ']' VariableTail | ε
        if self.coincidir('CORCHETE_IZQ'):
            nodo = NodoAST("VariableTail")
            
            nodo_expr = self.expr()
            if nodo_expr:
                nodo.agregar_hijo(nodo_expr)
            else:
                self.error("Se esperaba una expresión dentro de los corchetes")
                return nodo
            
            if not self.esperar('CORCHETE_DER', "Se esperaba ']' después de la expresión"):
                return nodo
            
            # Llamada recursiva para múltiples dimensiones
            nodo_tail = self.variable_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None
    
    def call_stmt(self) -> NodoAST:
        # CallStmt → ID '(' ArgListOpt ')'
        nodo = NodoAST("CallStmt")
        
        token_id = self.token_actual()
        if not self.coincidir('ID'):
            return None
        
        nodo.agregar_hijo(NodoAST("ID", token_id.valor))
        
        if not self.esperar('PARENTESIS_IZQ', "Se esperaba '(' después del identificador en la llamada"):
            return nodo
        
        nodo_args = self.arg_list_opt()
        if nodo_args:
            nodo.agregar_hijo(nodo_args)
        
        if not self.esperar('PARENTESIS_DER', "Se esperaba ')' después de los argumentos"):
            return nodo
        
        return nodo
    
    def if_stmt(self) -> NodoAST:
        # IfStmt → if Expr then Stmt ElseOpt
        nodo = NodoAST("IfStmt")
        
        if not self.coincidir('IF'):
            return None
        
        nodo_expr = self.expr()
        if nodo_expr:
            nodo.agregar_hijo(nodo_expr)
        
        if not self.esperar('THEN', "Se esperaba 'then' después de la condición if"):
            return nodo
        
        nodo_stmt = self.stmt()
        if nodo_stmt:
            nodo.agregar_hijo(nodo_stmt)
        
        nodo_else = self.else_opt()
        if nodo_else:
            nodo.agregar_hijo(nodo_else)
        
        return nodo
    
    def else_opt(self) -> NodoAST:
        # ElseOpt → else Stmt | ε
        if self.coincidir('ELSE'):
            nodo = NodoAST("ElseOpt")
            
            nodo_stmt = self.stmt()
            if nodo_stmt:
                nodo.agregar_hijo(nodo_stmt)
            
            return nodo
        return None
    
    def while_stmt(self) -> NodoAST:
        # WhileStmt → while Expr do Stmt
        nodo = NodoAST("WhileStmt")
        
        if not self.coincidir('WHILE'):
            return None
        
        nodo_expr = self.expr()
        if nodo_expr:
            nodo.agregar_hijo(nodo_expr)
        
        if not self.esperar('DO', "Se esperaba 'do' después de la condición while"):
            return nodo
        
        nodo_stmt = self.stmt()
        if nodo_stmt:
            nodo.agregar_hijo(nodo_stmt)
        
        return nodo
    
    # BLOQUE COMÚN - Expresiones
    def expr(self) -> NodoAST:
        # Expr → Assign
        return self.assign()
    
    def assign(self) -> NodoAST:
        # Assign → Or AssignTail
        nodo_or = self.or_expr()
        if not nodo_or:
            return None
        
        nodo_tail = self.assign_tail()
        if nodo_tail:
            nodo = NodoAST("Assign")
            nodo.agregar_hijo(nodo_or)
            nodo.agregar_hijo(nodo_tail)
            return nodo
        
        return nodo_or
    
    def assign_tail(self) -> NodoAST:
        # AssignTail → '=' Assign | ε
        if self.coincidir('IGUAL'):
            nodo = NodoAST("AssignTail")
            
            nodo_assign = self.assign()
            if nodo_assign:
                nodo.agregar_hijo(nodo_assign)
            
            return nodo
        return None
    
    def or_expr(self) -> NodoAST:
        # Or → And OrTail
        nodo_and = self.and_expr()
        if not nodo_and:
            return None
        
        nodo_tail = self.or_tail()
        if nodo_tail:
            nodo = NodoAST("Or")
            nodo.agregar_hijo(nodo_and)
            nodo.agregar_hijo(nodo_tail)
            return nodo
        
        return nodo_and
    
    def or_tail(self) -> NodoAST:
        # OrTail → '||' And OrTail | ε
        if self.coincidir('OR'):
            nodo = NodoAST("OrTail")
            
            nodo_and = self.and_expr()
            if nodo_and:
                nodo.agregar_hijo(nodo_and)
            
            nodo_tail = self.or_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None
    
    def and_expr(self) -> NodoAST:
        # And → Eq AndTail
        nodo_eq = self.eq_expr()
        if not nodo_eq:
            return None
        
        nodo_tail = self.and_tail()
        if nodo_tail:
            nodo = NodoAST("And")
            nodo.agregar_hijo(nodo_eq)
            nodo.agregar_hijo(nodo_tail)
            return nodo
        
        return nodo_eq
    
    def and_tail(self) -> NodoAST:
        # AndTail → '&&' Eq AndTail | ε
        if self.coincidir('AND'):
            nodo = NodoAST("AndTail")
            
            nodo_eq = self.eq_expr()
            if nodo_eq:
                nodo.agregar_hijo(nodo_eq)
            
            nodo_tail = self.and_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None
    
    def eq_expr(self) -> NodoAST:
        # Eq → Rel EqTail
        nodo_rel = self.rel_expr()
        if not nodo_rel:
            return None
        
        nodo_tail = self.eq_tail()
        if nodo_tail:
            nodo = NodoAST("Eq")
            nodo.agregar_hijo(nodo_rel)
            nodo.agregar_hijo(nodo_tail)
            return nodo
        
        return nodo_rel
    
    def eq_tail(self) -> NodoAST:
        # EqTail → '==' Rel EqTail | '!=' Rel EqTail | ε
        token = self.token_actual()
        if token and token.tipo in ['IGUAL', 'NO_IGUAL']:
            self.avanzar()
            nodo = NodoAST("EqTail")
            
            nodo.agregar_hijo(NodoAST("OPERADOR", token.valor))
            
            nodo_rel = self.rel_expr()
            if nodo_rel:
                nodo.agregar_hijo(nodo_rel)
            
            nodo_tail = self.eq_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None
    
    def rel_expr(self) -> NodoAST:
        # Rel → Add RelTail
        nodo_add = self.add_expr()
        if not nodo_add:
            return None
        
        nodo_tail = self.rel_tail()
        if nodo_tail:
            nodo = NodoAST("Rel")
            nodo.agregar_hijo(nodo_add)
            nodo.agregar_hijo(nodo_tail)
            return nodo
        
        return nodo_add
    
    def rel_tail(self) -> NodoAST:
        # RelTail → '<' Add RelTail | '<=' Add RelTail | '>' Add RelTail | '>=' Add RelTail | ε
        token = self.token_actual()
        if token and token.tipo in ['MENOR', 'MENOR_IGUAL', 'MAYOR', 'MAYOR_IGUAL']:
            self.avanzar()
            nodo = NodoAST("RelTail")
            
            nodo.agregar_hijo(NodoAST("OPERADOR", token.valor))
            
            nodo_add = self.add_expr()
            if nodo_add:
                nodo.agregar_hijo(nodo_add)
            
            nodo_tail = self.rel_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None
    
    def add_expr(self) -> NodoAST:
        # Add → Mul AddTail
        nodo_mul = self.mul_expr()
        if not nodo_mul:
            return None
        
        nodo_tail = self.add_tail()
        if nodo_tail:
            nodo = NodoAST("Add")
            nodo.agregar_hijo(nodo_mul)
            nodo.agregar_hijo(nodo_tail)
            return nodo
        
        return nodo_mul
    
    def add_tail(self) -> NodoAST:
        # AddTail → '+' Mul AddTail | '-' Mul AddTail | ε
        token = self.token_actual()
        if token and token.tipo in ['SUMA', 'RESTA']:
            self.avanzar()
            nodo = NodoAST("AddTail")
            
            nodo.agregar_hijo(NodoAST("OPERADOR", token.valor))
            
            nodo_mul = self.mul_expr()
            if nodo_mul:
                nodo.agregar_hijo(nodo_mul)
            
            nodo_tail = self.add_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None
    
    def mul_expr(self) -> NodoAST:
        # Mul → Unary MulTail
        nodo_unary = self.unary_expr()
        if not nodo_unary:
            return None
        
        nodo_tail = self.mul_tail()
        if nodo_tail:
            nodo = NodoAST("Mul")
            nodo.agregar_hijo(nodo_unary)
            nodo.agregar_hijo(nodo_tail)
            return nodo
        
        return nodo_unary
    
    def mul_tail(self) -> NodoAST:
        # MulTail → '*' Unary MulTail | '/' Unary MulTail | '%' Unary MulTail | ε
        token = self.token_actual()
        if token and token.tipo in ['MULTIPLICACION', 'DIVISION', 'MODULO']:
            self.avanzar()
            nodo = NodoAST("MulTail")
            
            nodo.agregar_hijo(NodoAST("OPERADOR", token.valor))
            
            nodo_unary = self.unary_expr()
            if nodo_unary:
                nodo.agregar_hijo(nodo_unary)
            
            nodo_tail = self.mul_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None
    
    def unary_expr(self) -> NodoAST:
        # Unary → '!' Unary | '-' Unary | Postfix
        token = self.token_actual()
        if token and token.tipo in ['NEGACION', 'RESTA']:
            self.avanzar()
            nodo = NodoAST("Unary")
            
            nodo.agregar_hijo(NodoAST("OPERADOR", token.valor))
            
            nodo_unary = self.unary_expr()
            if nodo_unary:
                nodo.agregar_hijo(nodo_unary)
            
            return nodo
        
        return self.postfix_expr()
    
    def postfix_expr(self) -> NodoAST:
        # Postfix → Primary PostfixTail
        nodo_primary = self.primary_expr()
        if not nodo_primary:
            return None
        
        nodo_tail = self.postfix_tail()
        if nodo_tail:
            nodo = NodoAST("Postfix")
            nodo.agregar_hijo(nodo_primary)
            nodo.agregar_hijo(nodo_tail)
            return nodo
        
        return nodo_primary
    
    def postfix_tail(self) -> NodoAST:
        # PostfixTail → '(' ArgListOpt ')' PostfixTail | '[' Expr ']' PostfixTail | '.' ID PostfixTail | ε
        token = self.token_actual()
        if not token:
            return None
        
        if token.tipo == 'PARENTESIS_IZQ':
            nodo = NodoAST("PostfixTail")
            
            self.avanzar()  # Consumir '('
            
            nodo_args = self.arg_list_opt()
            if nodo_args:
                nodo.agregar_hijo(nodo_args)
            
            if not self.esperar('PARENTESIS_DER', "Se esperaba ')' después de los argumentos"):
                return nodo
            
            nodo_tail = self.postfix_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        
        elif token.tipo == 'CORCHETE_IZQ':
            nodo = NodoAST("PostfixTail")
            
            self.avanzar()  # Consumir '['
            
            nodo_expr = self.expr()
            if nodo_expr:
                nodo.agregar_hijo(nodo_expr)
            
            if not self.esperar('CORCHETE_DER', "Se esperaba ']' después de la expresión"):
                return nodo
            
            nodo_tail = self.postfix_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        
        elif token.tipo == 'PUNTO':
            nodo = NodoAST("PostfixTail")
            
            self.avanzar()  # Consumir '.'
            
            token_id = self.token_actual()
            if not self.esperar('ID', "Se esperaba un identificador después de '.'"):
                return nodo
            
            nodo.agregar_hijo(NodoAST("ID", token_id.valor))
            
            nodo_tail = self.postfix_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        
        return None
    
    def primary_expr(self) -> NodoAST:
        # Primary → ID | NUM | STRING | 'true' | 'false' | '(' Expr ')'
        token = self.token_actual()
        if not token:
            return None
        
        if token.tipo == 'ID':
            nodo = NodoAST("Primary", token.valor)
            self.avanzar()
            return nodo
        elif token.tipo == 'NUM':
            nodo = NodoAST("Primary", token.valor)
            self.avanzar()
            return nodo
        elif token.tipo == 'STRING_LIT':
            nodo = NodoAST("Primary", token.valor)
            self.avanzar()
            return nodo
        elif token.tipo == 'TRUE':
            nodo = NodoAST("Primary", "true")
            self.avanzar()
            return nodo
        elif token.tipo == 'FALSE':
            nodo = NodoAST("Primary", "false")
            self.avanzar()
            return nodo
        elif token.tipo == 'PARENTESIS_IZQ':
            self.avanzar()  # Consumir '('
            
            nodo_expr = self.expr()
            if not nodo_expr:
                self.error("Se esperaba una expresión dentro de los paréntesis")
                return None
            
            if not self.esperar('PARENTESIS_DER', "Se esperaba ')' después de la expresión"):
                return None
            
            return nodo_expr
        
        return None
    
    def arg_list_opt(self) -> NodoAST:
        # ArgListOpt → ArgList | ε
        nodo_args = self.arg_list()
        if nodo_args and nodo_args.hijos:
            return nodo_args
        return None
    
    def arg_list(self) -> NodoAST:
        # ArgList → Expr ArgListTail
        nodo = NodoAST("ArgList")
        
        nodo_expr = self.expr()
        if nodo_expr:
            nodo.agregar_hijo(nodo_expr)
        
        nodo_tail = self.arg_list_tail()
        if nodo_tail:
            nodo.agregar_hijo(nodo_tail)
        
        return nodo
    
    def arg_list_tail(self) -> NodoAST:
        # ArgListTail → ',' Expr ArgListTail | ε
        if self.coincidir('COMA'):
            nodo = NodoAST("ArgListTail")
            
            nodo_expr = self.expr()
            if nodo_expr:
                nodo.agregar_hijo(nodo_expr)
            
            nodo_tail = self.arg_list_tail()
            if nodo_tail:
                nodo.agregar_hijo(nodo_tail)
            
            return nodo
        return None

class InterfazCompilador:
    def __init__(self, root):
        self.root = root
        self.root.title("Compilador - Proyecto Final Diseño de Compiladores")
        self.root.geometry("1200x800")
        
        # Variables
        self.tokens = []
        self.errores_lexicos = []
        self.errores_sintacticos = []
        
        self.crear_interfaz()
        self.cargar_ejemplo_correcto()
    
    def crear_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame para editor de código
        editor_frame = ttk.LabelFrame(main_frame, text="Editor de Código Fuente", padding=10)
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        # Área de texto para código
        self.texto_codigo = scrolledtext.ScrolledText(editor_frame, width=80, height=20, font=("Consolas", 10))
        self.texto_codigo.pack(fill=tk.BOTH, expand=True)
        
        # Frame para botones
        botones_frame = ttk.Frame(main_frame)
        botones_frame.pack(fill=tk.X, pady=5)
        
        # Botones
        ttk.Button(botones_frame, text="Analizar Léxico", command=self.analizar_lexico).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones_frame, text="Analizar Sintáctico", command=self.analizar_sintactico).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones_frame, text="Limpiar Todo", command=self.limpiar).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones_frame, text="Cargar Ejemplo", command=self.cargar_ejemplo_correcto).pack(side=tk.LEFT, padx=5)
        
        # Frame para resultados
        resultados_frame = ttk.Frame(main_frame)
        resultados_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook para pestañas
        self.notebook = ttk.Notebook(resultados_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de tokens
        tokens_frame = ttk.Frame(self.notebook)
        self.notebook.add(tokens_frame, text="Tabla de Tokens")
        
        # Treeview para tokens
        columns = ("Tipo", "Valor", "Línea", "Columna")
        self.tree_tokens = ttk.Treeview(tokens_frame, columns=columns, show="headings")
        
        for col in columns:
            self.tree_tokens.heading(col, text=col)
            self.tree_tokens.column(col, width=150)
        
        scroll_tokens = ttk.Scrollbar(tokens_frame, orient=tk.VERTICAL, command=self.tree_tokens.yview)
        self.tree_tokens.configure(yscrollcommand=scroll_tokens.set)
        
        self.tree_tokens.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_tokens.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pestaña de errores
        errores_frame = ttk.Frame(self.notebook)
        self.notebook.add(errores_frame, text="Errores")
        
        # Área de texto para errores
        self.texto_errores = scrolledtext.ScrolledText(errores_frame, width=80, height=10, font=("Consolas", 10))
        self.texto_errores.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de AST
        ast_frame = ttk.Frame(self.notebook)
        self.notebook.add(ast_frame, text="Árbol de Derivación (AST)")
        
        # Área de texto para AST
        self.texto_ast = scrolledtext.ScrolledText(ast_frame, width=80, height=10, font=("Consolas", 10))
        self.texto_ast.pack(fill=tk.BOTH, expand=True)
    
    def analizar_lexico(self):
        codigo = self.texto_codigo.get("1.0", tk.END)
        
        # Limpiar resultados anteriores
        self.tree_tokens.delete(*self.tree_tokens.get_children())
        self.texto_errores.delete("1.0", tk.END)
        self.texto_ast.delete("1.0", tk.END)
        
        # Análisis léxico
        analizador = AnalizadorLexico()
        tokens, errores = analizador.analizar(codigo)
        
        # Mostrar tokens
        for token in tokens:
            if token.tipo != 'COMENTARIO' and token.tipo != 'EOF':  # No mostrar comentarios ni EOF
                self.tree_tokens.insert("", tk.END, values=(token.tipo, token.valor, token.linea, token.columna))
        
        # Mostrar errores
        if errores:
            for error in errores:
                self.texto_errores.insert(tk.END, error + "\n")
            messagebox.showerror("Errores Léxicos", f"Se encontraron {len(errores)} errores léxicos")
        else:
            messagebox.showinfo("Análisis Léxico", "No se encontraron errores léxicos")
    
    def analizar_sintactico(self):
        codigo = self.texto_codigo.get("1.0", tk.END)
        
        # Limpiar resultados anteriores
        self.texto_errores.delete("1.0", tk.END)
        self.texto_ast.delete("1.0", tk.END)
        
        # Análisis léxico primero
        analizador_lexico = AnalizadorLexico()
        tokens, errores_lexicos = analizador_lexico.analizar(codigo)
        
        if errores_lexicos:
            for error in errores_lexicos:
                self.texto_errores.insert(tk.END, "[LÉXICO] " + error + "\n")
            messagebox.showerror("Errores Léxicos", "Corrija los errores léxicos antes del análisis sintáctico")
            return
        
        # Análisis sintáctico
        analizador_sintactico = AnalizadorSintactico(tokens)
        es_valido = analizador_sintactico.analizar()
        
        # Mostrar errores sintácticos
        if analizador_sintactico.errores:
            for error in analizador_sintactico.errores:
                self.texto_errores.insert(tk.END, "[SINTÁCTICO] " + error + "\n")
        
        # Mostrar AST
        if analizador_sintactico.ast:
            self.mostrar_ast(analizador_sintactico.ast)
        
        if es_valido:
            messagebox.showinfo("Análisis Sintáctico", "✓ El análisis sintáctico fue EXITOSO\nEl código sigue la gramática correctamente")
        else:
            messagebox.showerror("Análisis Sintáctico", f"✗ Se encontraron {len(analizador_sintactico.errores)} errores sintácticos")
    
    def mostrar_ast(self, nodo, nivel=0):
        indentacion = "  " * nivel
        linea = f"{indentacion}{nodo.tipo}"
        if nodo.valor:
            linea += f": {nodo.valor}"
        self.texto_ast.insert(tk.END, linea + "\n")
        
        for hijo in nodo.hijos:
            self.mostrar_ast(hijo, nivel + 1)
    
    def limpiar(self):
        self.texto_codigo.delete("1.0", tk.END)
        self.tree_tokens.delete(*self.tree_tokens.get_children())
        self.texto_errores.delete("1.0", tk.END)
        self.texto_ast.delete("1.0", tk.END)
    
    def cargar_ejemplo_correcto(self):
        ejemplo = """program EjemploEstricto;

type
    Entero = integer;
    Arreglo = array [1..5] of Entero;
    Logico = boolean;

var
    datos: Arreglo;
    total, i: integer;
    bandera: Logico;

procedure Inicializar();
var
    j: integer;
begin
    j := 1;
    while j <= 5 do
    begin
        datos[j] := j * 10;
        j := j + 1
    end
end;

function CalcularSuma(); integer;
var
    suma, k: integer;
begin
    suma := 0;
    k := 1;
    while k <= 5 do
    begin
        suma := suma + datos[k];
        k := k + 1
    end;
    CalcularSuma := suma
end;

function EsMayor(a, b: integer); Logico;
begin
    if a > b then
        EsMayor := true
    else
        EsMayor := false
end;

begin
    Inicializar();
    total := CalcularSuma();
    
    i := 1;
    bandera := true;
    
    while i <= 5 do
    begin
        if EsMayor(datos[i], 25) then
            bandera := bandera && true
        else
            bandera := bandera && false;
        i := i + 1
    end
end.
"""
        self.texto_codigo.delete("1.0", tk.END)
        self.texto_codigo.insert("1.0", ejemplo)

def main():
    root = tk.Tk()
    app = InterfazCompilador(root)
    root.mainloop()

if __name__ == "__main__":
    main()
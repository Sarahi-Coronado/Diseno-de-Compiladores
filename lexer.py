#!/usr/bin/env python3
import re
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from collections import namedtuple

Token = namedtuple("Token", ["token", "cadena", "lexeme", "line", "col"])

KEYWORDS = {
    "program": "PROGRAM", "type": "TYPE", "var": "VAR", "procedure": "PROCEDURE",
    "function": "FUNCTION", "begin": "BEGIN", "end": "END", "integer": "INTEGER",
    "boolean": "BOOLEAN", "string": "STRING_T", "array": "ARRAY", "of": "OF",
    "if": "IF", "then": "THEN", "else": "ELSE", "while": "WHILE", "do": "DO",
    "true": "TRUE", "false": "FALSE"
}

token_specification = [
    ("WHITESPACE", r"[ \t]+"),
    ("NEWLINE", r"\r\n|\r|\n"),
    ("COMMENT", r"//[A-Za-z0-9]+//"),
    ("STRING", r"\"[^\"\n]*\""),
    ("NUM", r"\d+(\.\d+)?([eE][+-]?\d+)?"),
    ("ASSIGN", r":="),
    ("EQEQ", r"=="),
    ("EQUAL", r"="),
    ("NEQ", r"!="),
    ("LE", r"<="),
    ("GE", r">="),
    ("ANDAND", r"&&"),
    ("OROR", r"\|\|"),
    ("DOTDOT", r"\.\."),
    ("LT", r"<"),
    ("GT", r">"),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("MUL", r"\*"),
    ("DIV", r"/"),
    ("MOD", r"%"),
    ("NOT", r"!"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACK", r"\["),
    ("RBRACK", r"\]"),
    ("DOT", r"\."),
    ("SEMI", r";"),
    ("COMMA", r","),
    ("COLON", r":"),
    ("ID", r"[A-Za-z][A-Za-z0-9_]*"),
]

token_regex_list = [(name, re.compile(pattern)) for name, pattern in token_specification]

DESCRIPTION_MAP = {
    "ASSIGN": "ASIGNACION",
    "EQEQ": "IGUAL_IGUAL",
    "EQUAL": "IGUAL",
    "NEQ": "DIFERENTE",
    "LE": "MENOR_IGUAL",
    "GE": "MAYOR_IGUAL",
    "LT": "MENOR",
    "GT": "MAYOR",
    "PLUS": "SUMA",
    "MINUS": "RESTA",
    "MUL": "MULTIPLICACION",
    "DIV": "DIVISION",
    "MOD": "MODULO",
    "ANDAND": "AND",
    "OROR": "OR",
    "NOT": "NEGACION",
    "LPAREN": "PARENTESIS_ABRE",
    "RPAREN": "PARENTESIS_CIERRA",
    "LBRACK": "CORCHETE_ABRE",
    "RBRACK": "CORCHETE_CIERRA",
    "DOTDOT": "RANGO",
    "DOT": "PUNTO",
    "SEMI": "PUNTO_Y_COMA",
    "COMMA": "COMA",
    "COLON": "DOS_PUNTOS",
    "ID": "IDENTIFICADOR",
    "NUM": "NUMERO",
    "STRING": "CADENA",
    "EOF": "EOF"
}

class LexerError(Exception):
    def __init__(self, message, line, col):
        super().__init__(message)
        self.line = line
        self.col = col

def _advance_position(line, col, lexeme):
    if not lexeme:
        return line, col
    if "\n" not in lexeme and "\r" not in lexeme:
        return line, col + len(lexeme)
    parts = re.split(r"\r\n|\r|\n", lexeme)
    new_line = line + (len(parts) - 1)
    new_col = len(parts[-1]) + 1
    return new_line, new_col

def lex(source_text):
    tokens = []
    pos = 0
    line = 1
    col = 1
    length = len(source_text)
    while pos < length:
        match = None
        for tok_name, tok_re in token_regex_list:
            m = tok_re.match(source_text, pos)
            if m:
                lexeme = m.group(0)
                match = (tok_name, lexeme)
                break
        if not match:
            ch = source_text[pos]
            raise LexerError(f"Carácter inesperado: {repr(ch)}", line, col)
        tok_name, lexeme = match
        start_line, start_col = line, col
        pos += len(lexeme)
        line, col = _advance_position(line, col, lexeme)
        if tok_name in ("WHITESPACE", "NEWLINE", "COMMENT"):
            continue
        if tok_name == "ID":
            if lexeme.lower() in KEYWORDS:
                token_type = KEYWORDS[lexeme.lower()]
                cadena = "PALABRA_RESERVADA"
                tokens.append(Token(token_type, cadena, lexeme, start_line, start_col))
            else:
                token_type = "ID"
                cadena = DESCRIPTION_MAP.get("ID", "IDENTIFICADOR")
                tokens.append(Token(token_type, cadena, lexeme, start_line, start_col))
            continue
        if tok_name in ("NUM", "STRING"):
            token_type = tok_name
            cadena = DESCRIPTION_MAP.get(tok_name, tok_name)
            tokens.append(Token(token_type, cadena, lexeme, start_line, start_col))
            continue
        operator_map = {
            "ASSIGN": "ASSIGN", "EQUAL": "EQUAL", "EQEQ": "EQEQ", "NEQ": "NEQ",
            "LE": "LE", "GE": "GE", "ANDAND": "ANDAND", "OROR": "OROR", "DOTDOT": "DOTDOT",
            "LT": "LT", "GT": "GT", "PLUS": "PLUS", "MINUS": "MINUS", "MUL": "MUL",
            "DIV": "DIV", "MOD": "MOD", "NOT": "NOT", "LPAREN": "LPAREN", "RPAREN": "RPAREN",
            "LBRACK": "LBRACK", "RBRACK": "RBRACK", "DOT": "DOT", "SEMI": "SEMI",
            "COMMA": "COMMA", "COLON": "COLON"
        }
        tok_type = operator_map.get(tok_name, tok_name)
        cadena = DESCRIPTION_MAP.get(tok_name, DESCRIPTION_MAP.get(tok_type, tok_type))
        tokens.append(Token(tok_type, cadena, lexeme, start_line, start_col))
    tokens.append(Token("EOF", DESCRIPTION_MAP.get("EOF", "EOF"), "", line, col))
    return tokens

class AnalizadorLexicoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador Léxico")
        self.root.geometry("900x650")
        label = tk.Label(root, text="Ingrese código fuente:", font=("Arial", 12, "bold"))
        label.pack(pady=8)
        self.editor = scrolledtext.ScrolledText(root, width=110, height=30, font=("Consolas", 11))
        self.editor.pack(padx=10, pady=5, expand=True, fill="both")
        frame = tk.Frame(root)
        frame.pack(pady=8)
        btn_analyze = tk.Button(frame, text="Analizar Léxico", command=self.analizar, width=16)
        btn_analyze.pack(side=tk.LEFT, padx=6)
        btn_clear = tk.Button(frame, text="Limpiar", command=self.limpiar_editor, width=10)
        btn_clear.pack(side=tk.LEFT, padx=6)
        btn_exit = tk.Button(frame, text="Salir", command=root.quit, width=10)
        btn_exit.pack(side=tk.LEFT, padx=6)

    def limpiar_editor(self):
        self.editor.delete("1.0", tk.END)

    def analizar(self):
        source = self.editor.get("1.0", tk.END)
        if not source.strip():
            messagebox.showwarning("Aviso", "Debe ingresar código para analizar.")
            return
        try:
            tokens = lex(source)
            self.mostrar_tabla(tokens)
        except LexerError as le:
            self.mostrar_error(le, source)

    def mostrar_tabla(self, tokens):
        tabla = tk.Toplevel(self.root)
        tabla.title("Tabla de Tokens")
        tabla.geometry("900x520")
        lbl = tk.Label(tabla, text="Tabla de Tokens", font=("Arial", 12, "bold"))
        lbl.pack(pady=8)
        cols = ("#", "TOKEN", "CADENA", "LEXEMA", "LÍNEA", "COLUMNA")
        tree = ttk.Treeview(tabla, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            tree.heading(c, text=c)
            if c == "LEXEMA":
                tree.column(c, width=360, anchor=tk.W)
            elif c == "CADENA":
                tree.column(c, width=160, anchor=tk.W)
            elif c == "TOKEN":
                tree.column(c, width=140, anchor=tk.W)
            else:
                tree.column(c, width=80, anchor=tk.CENTER)
        tree.pack(expand=True, fill="both", padx=10, pady=8)
        for i, t in enumerate(tokens, start=1):
            lex = t.lexeme if t.lexeme != "" else "<EOF>"
            tree.insert("", "end", values=(i, t.token, t.cadena, lex, t.line, t.col))
        frame = tk.Frame(tabla)
        frame.pack(pady=6)
        btn_close = tk.Button(frame, text="Regresar", command=tabla.destroy, width=12)
        btn_close.pack(side=tk.LEFT, padx=6)
        def save_csv():
            try:
                import csv, tkinter.filedialog as fd
                path = fd.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
                if not path:
                    return
                with open(path, "w", newline='', encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(cols)
                    for i, t in enumerate(tokens, start=1):
                        lex = t.lexeme if t.lexeme != "" else "<EOF>"
                        w.writerow([i, t.token, t.cadena, lex, t.line, t.col])
                messagebox.showinfo("Guardado", "CSV guardado correctamente.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        btn_save = tk.Button(frame, text="Guardar CSV", command=save_csv, width=12)
        btn_save.pack(side=tk.LEFT, padx=6)

    def mostrar_error(self, error, source):
        v = tk.Toplevel(self.root)
        v.title("Error Léxico")
        v.geometry("760x320")
        lbl = tk.Label(v, text=f"Error Léxico en línea {error.line}, columna {error.col}", fg="red", font=("Arial", 12, "bold"))
        lbl.pack(pady=8)
        lines = source.splitlines()
        if 1 <= error.line <= len(lines):
            err_line = lines[error.line - 1]
            text_box = scrolledtext.ScrolledText(v, height=6, width=90, font=("Consolas", 11))
            text_box.pack(padx=10, pady=6)
            text_box.insert(tk.END, err_line + "\n")
            caret = " " * (max(0, error.col - 1)) + "^\n"
            text_box.insert(tk.END, caret)
            text_box.config(state="disabled")
        lbl2 = tk.Label(v, text=str(error), font=("Arial", 11))
        lbl2.pack(pady=6)
        frame = tk.Frame(v)
        frame.pack(pady=8)
        btn_retry = tk.Button(frame, text="Reintentar", command=v.destroy, width=12)
        btn_retry.pack(side=tk.LEFT, padx=6)
        btn_goto = tk.Button(frame, text="Ir al editor", command=lambda: (v.destroy(), self.root.deiconify()), width=12)
        btn_goto.pack(side=tk.LEFT, padx=6)

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalizadorLexicoGUI(root)
    root.mainloop()

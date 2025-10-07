#!/usr/bin/env python3
"""
Cumple con las siguientes especificaciones:
 - Ignora comentarios del tipo //[A-Za-z0-9]+//
 - Identificadores comienzan con letra (mayúscula o minúscula)
 - Strings: "Texto en string lit"
 - Números: enteros, decimales o notación científica (ej. 12.2, 123, 12e21, 13e-12)
"""

import sys
import re
from collections import namedtuple

Token = namedtuple("Token", ["type", "lexeme", "line", "col"])

# --------------------------------------
# PALABRAS RESERVADAS (no distinguen mayúsculas)
# --------------------------------------
KEYWORDS = {
    "program": "PROGRAM",
    "type": "TYPE",
    "var": "VAR",
    "procedure": "PROCEDURE",
    "function": "FUNCTION",
    "begin": "BEGIN",
    "end": "END",
    "integer": "INTEGER",
    "boolean": "BOOLEAN",
    "string": "STRING_T",
    "array": "ARRAY",
    "of": "OF",
    "if": "IF",
    "then": "THEN",
    "else": "ELSE",
    "while": "WHILE",
    "do": "DO",
    "true": "TRUE",
    "false": "FALSE"
}

# --------------------------------------
# EXPRESIONES REGULARES DE TOKENS
# (ordenadas por prioridad)
# --------------------------------------
token_specification = [
    ("WHITESPACE", r"[ \t]+"),                         # Espacios
    ("NEWLINE", r"\r\n|\r|\n"),                        # Saltos de línea
    ("COMMENT", r"//[A-Za-z0-9]+//"),                  # Comentarios personalizados
    ("STRING", r"\"[^\"\n]*\""),                       # String literal: "Texto"
    ("NUM", r"\d+(\.\d+)?(e[+-]?\d+)?"),               # Números enteros, decimales, científicos
    ("ASSIGN", r":="), ("EQEQ", r"=="), ("NEQ", r"!="),
    ("LE", r"<="), ("GE", r">="), ("ANDAND", r"&&"), ("OROR", r"\|\|"),
    ("DOTDOT", r"\.\."), ("LT", r"<"), ("GT", r">"),
    ("PLUS", r"\+"), ("MINUS", r"-"), ("MUL", r"\*"), ("DIV", r"/"),
    ("MOD", r"%"), ("NOT", r"!"),
    ("LPAREN", r"\("), ("RPAREN", r"\)"),
    ("LBRACK", r"\["), ("RBRACK", r"\]"),
    ("DOT", r"\."), ("SEMI", r";"), ("COMMA", r","), ("COLON", r":"),
    ("ID", r"[A-Za-z][A-Za-z0-9_]*"),                  # Identificadores válidos
]

# Compilar todas las expresiones
token_regex_list = [(name, re.compile(pattern, re.DOTALL)) for name, pattern in token_specification]

# --------------------------------------
# CLASE DE ERROR LÉXICO
# --------------------------------------
class LexerError(Exception):
    def __init__(self, message, line, col):
        super().__init__(message)
        self.line = line
        self.col = col

# --------------------------------------
# ANALIZADOR LÉXICO
# --------------------------------------
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
        pos += len(lexeme)

        # Contar líneas nuevas dentro del lexema
        if "\n" in lexeme or "\r" in lexeme:
            newlines = re.findall(r"\r\n|\r|\n", lexeme)
            line += len(newlines)
            col = 1
        else:
            col += len(lexeme)

        # Ignorar espacios, saltos y comentarios
        if tok_name in ("WHITESPACE", "NEWLINE", "COMMENT"):
            continue

        # Palabras reservadas
        if tok_name == "ID":
            if lexeme.lower() in KEYWORDS:
                tokens.append(Token(KEYWORDS[lexeme.lower()], lexeme, line, col - len(lexeme)))
            else:
                tokens.append(Token("ID", lexeme, line, col - len(lexeme)))
            continue

        # Números
        if tok_name == "NUM":
            tokens.append(Token("NUM", lexeme, line, col - len(lexeme)))
            continue

        # Strings
        if tok_name == "STRING":
            tokens.append(Token("STRING", lexeme, line, col - len(lexeme)))
            continue

        # Operadores y símbolos
        operator_map = {
            "ASSIGN": "ASSIGN", "EQEQ": "EQ", "NEQ": "NEQ", "LE": "LE", "GE": "GE",
            "ANDAND": "AND", "OROR": "OR", "DOTDOT": "DOTDOT", "LT": "LT", "GT": "GT",
            "PLUS": "PLUS", "MINUS": "MINUS", "MUL": "MUL", "DIV": "DIV", "MOD": "MOD",
            "NOT": "NOT", "LPAREN": "LPAREN", "RPAREN": "RPAREN", "LBRACK": "LBRACK",
            "RBRACK": "RBRACK", "DOT": "DOT", "SEMI": "SEMI", "COMMA": "COMMA", "COLON": "COLON"
        }
        tok_type = operator_map.get(tok_name, tok_name)
        tokens.append(Token(tok_type, lexeme, line, col - len(lexeme)))

    tokens.append(Token("EOF", "", line, col))
    return tokens

# --------------------------------------
# IMPRESIÓN DE TOKENS
# --------------------------------------
def print_tokens(tokens):
    print(f"{'No.':>3}  {'Token':<10}  {'Lexema':<20}  {'Línea':>4}  {'Col':>3}")
    print("-" * 50)
    for i, t in enumerate(tokens, start=1):
        lex = t.lexeme if len(t.lexeme) < 18 else t.lexeme[:15] + "..."
        print(f"{i:3}  {t.type:<10}  {lex:<20}  {t.line:>4}  {t.col:>3}")

# --------------------------------------
# MAIN
# --------------------------------------
def main():
    if len(sys.argv) == 2:
        try:
            with open(sys.argv[1], "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            print("Error al abrir el archivo:", e)
            sys.exit(1)
    else:
        source = """program Demo;
var x: integer;
begin
  //esteesuncomentario//
  x := 12.3e-2;
  y := "Texto en string lit";
end.
"""

    try:
        toks = lex(source)
        print("\n✅ Tabla de tokens generada:\n")
        print_tokens(toks)
    except LexerError as le:
        print("\n❌ Error léxico:")
        print(f"Línea {le.line}, Columna {le.col} - {le}")
        lines = source.splitlines()
        if 1 <= le.line <= len(lines):
            err_line = lines[le.line - 1]
            print("  ", err_line)
            print("  ", " " * (le.col - 1) + "^")
        sys.exit(1)

if __name__ == "__main__":
    main()

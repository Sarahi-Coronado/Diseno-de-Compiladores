import React, { useState } from "react";
import "./App.css";

function App() {
  const [codigo, setCodigo] = useState("");
  const [tokens, setTokens] = useState([]);
  const [error, setError] = useState(null);

  // Palabras reservadas
  const KEYWORDS = {
    program: "PROGRAM", type: "TYPE", var: "VAR", procedure: "PROCEDURE",
    function: "FUNCTION", begin: "BEGIN", end: "END", integer: "INTEGER",
    boolean: "BOOLEAN", string: "STRING_T", array: "ARRAY", of: "OF",
    if: "IF", then: "THEN", else: "ELSE", while: "WHILE", do: "DO",
    true: "TRUE", false: "FALSE"
  };

  // Mapeo de descripción de tokens
  const DESCRIPTION_MAP = {
    ASSIGN: "ASIGNACION",
    EQEQ: "IGUAL_IGUAL",
    EQUAL: "IGUAL",
    NEQ: "DIFERENTE",
    LE: "MENOR_IGUAL",
    GE: "MAYOR_IGUAL",
    LT: "MENOR",
    GT: "MAYOR",
    PLUS: "SUMA",
    MINUS: "RESTA",
    MUL: "MULTIPLICACION",
    DIV: "DIVISION",
    MOD: "MODULO",
    ANDAND: "AND",
    OROR: "OR",
    NOT: "NEGACION",
    LPAREN: "PARENTESIS_ABRE",
    RPAREN: "PARENTESIS_CIERRA",
    LBRACK: "CORCHETE_ABRE",
    RBRACK: "CORCHETE_CIERRA",
    DOTDOT: "RANGO",
    DOT: "PUNTO",
    SEMI: "PUNTO_Y_COMA",
    COMMA: "COMA",
    COLON: "DOS_PUNTOS",
    ID: "IDENTIFICADOR",
    NUM: "NUMERO",
    STRING: "CADENA",
    EOF: "EOF"
  };

  // Patrones de tokens
  const tokenPatterns = [
    ["WHITESPACE", /^[ \t]+/],
    ["NEWLINE", /^\r\n|\r|\n/],
    // Comentarios: todo lo que esté entre "// ... //"
    ["COMMENT", /^\/\/[\s\S]*?\/\//],
    ["STRING", /^"[^"\n]*"/],
    ["NUM", /^\d+(\.\d+)?([eE][+-]?\d+)?/],
    ["ASSIGN", /^:=/],
    ["EQEQ", /^==/],
    ["EQUAL", /^=/],
    ["NEQ", /^!=/],
    ["LE", /^<=/],
    ["GE", /^>=/],
    ["ANDAND", /^&&/],
    ["OROR", /^\|\|/],
    ["DOTDOT", /^\.\./],
    ["LT", /^</],
    ["GT", /^>/],
    ["PLUS", /^\+/],
    ["MINUS", /^-/],
    ["MUL", /^\*/],
    ["DIV", /^\//],
    ["MOD", /^%/],
    ["NOT", /^!/],
    ["LPAREN", /^\(/],
    ["RPAREN", /^\)/],
    ["LBRACK", /^\[/],
    ["RBRACK", /^\]/],
    ["DOT", /^\./],
    ["SEMI", /^;/],
    ["COMMA", /^,/],
    ["COLON", /^:/],
    ["ID", /^[A-Za-z][A-Za-z0-9_]*/],
  ];

  // Analizador léxico
  const lex = (source) => {
    let pos = 0;
    let line = 1;
    let col = 1;
    const tokens = [];

    while (pos < source.length) {
      let matched = false;

      for (let [type, regex] of tokenPatterns) {
        const slice = source.slice(pos);
        const m = slice.match(regex);
        if (m && m.index === 0) {
          const lexeme = m[0];
          const startLine = line;
          const startCol = col;

          // Avanzar línea y columna
          const lines = lexeme.split(/\r\n|\r|\n/);
          if (lines.length > 1) {
            line += lines.length - 1;
            col = lines[lines.length - 1].length + 1;
          } else {
            col += lexeme.length;
          }
          pos += lexeme.length;

          // Ignorar espacios, saltos de línea y comentarios
          if (type === "WHITESPACE" || type === "NEWLINE" || type === "COMMENT") {
            matched = true;
            break;
          }

          // Determinar tokenType y CADENA
          let tokenType = type;
          let cadena = DESCRIPTION_MAP[type] || type;

          if (type === "ID") {
            const kw = KEYWORDS[lexeme.toLowerCase()];
            if (kw) {
              tokenType = kw;
              cadena = "PALABRA_RESERVADA";
            } else {
              tokenType = "ID";
              cadena = DESCRIPTION_MAP["ID"];
            }
          }

          if (type === "NUM" || type === "STRING") {
            cadena = DESCRIPTION_MAP[type];
          }

          // Mapear operadores
          const operatorMap = {
            ASSIGN: "ASSIGN", EQUAL: "EQUAL", EQEQ: "EQEQ", NEQ: "NEQ",
            LE: "LE", GE: "GE", ANDAND: "ANDAND", OROR: "OROR", DOTDOT: "DOTDOT",
            LT: "LT", GT: "GT", PLUS: "PLUS", MINUS: "MINUS", MUL: "MUL",
            DIV: "DIV", MOD: "MOD", NOT: "NOT", LPAREN: "LPAREN", RPAREN: "RPAREN",
            LBRACK: "LBRACK", RBRACK: "RBRACK", DOT: "DOT", SEMI: "SEMI",
            COMMA: "COMMA", COLON: "COLON"
          };

          if (operatorMap[type]) {
            tokenType = operatorMap[type];
            cadena = DESCRIPTION_MAP[tokenType];
          }

          tokens.push({ token: tokenType, cadena, lexeme, line: startLine, col: startCol });
          matched = true;
          break;
        }
      }

      if (!matched) {
        setError({ line, col, char: source[pos] });
        return [];
      }
    }

    // Token EOF
    tokens.push({ token: "EOF", cadena: DESCRIPTION_MAP["EOF"], lexeme: "", line, col });
    return tokens;
  };

  const handleAnalizar = () => {
    setError(null);
    const result = lex(codigo);
    setTokens(result);
  };

  // Generar números de línea
  const getLineNumbers = () => {
    const lines = codigo.split("\n").length;
    return Array.from({ length: lines }, (_, i) => i + 1).join("\n");
  };

  return (
    <div className="App">
      <h1>Analizador Léxico React</h1>

      <div className="editor-container">
        <pre className="line-numbers">{getLineNumbers()}</pre>
        <textarea
          value={codigo}
          onChange={(e) => setCodigo(e.target.value)}
          placeholder="Escribe tu código aquí..."
        />
      </div>

      <button onClick={handleAnalizar}>Analizar</button>

      {error && (
        <p style={{ color: "red" }}>
          Error Léxico en línea {error.line}, columna {error.col}: "{error.char}"
        </p>
      )}

      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>TOKEN</th>
            <th>CADENA</th>
            <th>LEXEMA</th>
            <th>LÍNEA</th>
            <th>COLUMNA</th>
          </tr>
        </thead>
        <tbody>
          {tokens.map((t,i)=>(
            <tr key={i}>
              <td>{i+1}</td>
              <td>{t.token}</td>
              <td>{t.cadena}</td>
              <td>{t.lexeme || "<EOF>"}</td>
              <td>{t.line}</td>
              <td>{t.col}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;

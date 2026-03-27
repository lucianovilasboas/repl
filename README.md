# HP 50g RPN Calculator Simulator

Simulador da calculadora **HP 50g** em modo **RPN** (Reverse Polish Notation), implementado em Python como um REPL interativo de linha de comando.

## Funcionalidades

- **Stack infinita** com display de 4 níveis (estilo HP 50g: `4: 3: 2: 1:`)
- **Aritmética**: `+`, `-`, `*`, `/`, `NEG`, `ABS`, `MOD`, `IP`, `FP`, `MIN`, `MAX`, `SIGN`, `%`, `FLOOR`, `CEIL`
- **Científico**: `SIN`, `COS`, `TAN`, `ASIN`, `ACOS`, `ATAN`, `LOG`, `LN`, `EXP`, `SQRT`, `SQ`, `^`, `INV`, `!`, `PI`, `SINH`, `COSH`, `TANH`, `D->R`, `R->D`, `XROOT`, `ALOG`
- **Manipulação de stack**: `DUP`, `DROP`, `SWAP`, `OVER`, `ROT`, `ROLL`, `PICK`, `DEPTH`, `CLEAR`, `DUP2`, `DROP2`, `DUPN`, `DROPN`, `NDUP`, `UNROT`, `ROLLD`
- **Comparação**: `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Lógica**: `AND`, `OR`, `NOT`, `XOR`, `IFT`, `IFTE`
- **Variáveis**: `STO`, `RCL`, `PURGE`, `VARS`, `STO+`, `STO-`, `STO*`, `STO/`
- **Listas**: `{ 1 2 3 }`, `LIST→`, `→LIST`, `GET`, `PUT`, `SIZE`, `HEAD`, `TAIL`, `REVLIST`, `SORT`
- **Programas RPL**: `<< >>` ou `« »`, `EVAL`, `IF/THEN/ELSE/END`, `FOR/NEXT/STEP`, `START/NEXT/STEP`, `WHILE/REPEAT/END`, `DO/UNTIL/END`
- **Modos angulares**: `DEG`, `RAD`, `GRAD`
- **Formato de exibição**: `FIX n`, `SCI n`, `ENG n`, `STD`
- **UNDO** (desfazer última operação)
- **Persistência** automática de stack, variáveis e configurações entre sessões
- **Histórico de comandos** com setas cima/baixo

## Instalação

```bash
# Criar e ativar ambiente virtual (recomendado)
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

Ao iniciar, o REPL exibe a stack no estilo HP 50g:

```
  ╔═══════════════════════════════════════════╗
  ║         HP 50g RPN Simulator (MVP)        ║
  ║                                           ║
  ║  Type RPN expressions. Commands:          ║
  ║    HELP  — list all operations            ║
  ║    UNDO  — undo last operation            ║
  ║    QUIT  — save and exit                  ║
  ╚═══════════════════════════════════════════╝

  { RAD STD }
  4:
  3:
  2:
  1:

>
```

### Exemplos

```
> 3 4 +
  1:                                        7

> 2 3 * 4 +
  1:                                       10

> PI 2 / SIN
  1:                                        1

> DEG
> 90 SIN
  1:                                        1

> 5 !
  1:                                      120
```

### Variáveis

```
> 42 'X' STO          — armazena 42 na variável X
> X                    — empurra o valor de X na stack (42)
> 'X' RCL             — idem
> 10 'X' STO+         — soma 10 a X (agora X=52)
> VARS                — lista todas as variáveis
> 'X' PURGE           — remove a variável X
```

### Listas

```
> { 1 2 3 4 5 }       — empurra a lista na stack
> SIZE                 — 5
> 3 GET                — obtém 3º elemento (3)
> { 10 20 } { 30 } +  — concatena: { 10 20 30 }
> LIST→               — explode lista na stack
```

### Programas RPL

```
> << DUP * >> 'SQ' STO     — define programa SQ (eleva ao quadrado)
> 7 SQ                      — executa: 49

> << DUP 1 > IF DUP 1 - FACT * THEN >> 'FACT2' STO
> 5 FACT2                   — recursão: 120

> 1 10 FOR I I NEXT         — empurra 1 a 10 na stack

> << WHILE DUP 0 > REPEAT 1 - END >> 'COUNTDOWN' STO
> 5 COUNTDOWN               — conta de 5 até 0
```

### Controles

| Comando | Descrição |
|---------|-----------|
| `HELP`  | Lista todas as operações disponíveis |
| `UNDO`  | Desfaz a última operação |
| `QUIT` / `EXIT` / `Q` | Salva estado e encerra |
| `↑` / `↓` | Navega pelo histórico de comandos |

## Testes

```bash
python -m pytest tests/ -v
```

```
tests/test_arithmetic.py  ✓ 14 tests
tests/test_parser.py      ✓ 14 tests
tests/test_programs.py    ✓ 10 tests
tests/test_scientific.py  ✓ 15 tests
tests/test_stack.py       ✓  8 tests
tests/test_variables.py   ✓  6 tests
                          ─────────
                          67 passed
```

## Estrutura do Projeto

```
rpn/
├── main.py           — REPL interativo (entry point)
├── rpn_types.py      — Sistema de tipos (RPNNumber, RPNString, RPNList, RPNProgram, RPNSymbol)
├── stack.py          — Engine da stack RPN
├── parser.py         — Tokenizer/parser de entrada
├── operations.py     — Registry de operações + dispatch
├── display.py        — Formatação estilo HP 50g
├── state.py          — Persistência em JSON (~/.rpn50g_state.json)
├── ops/
│   ├── arithmetic.py — Operações aritméticas
│   ├── stack_ops.py  — Manipulação de stack
│   ├── scientific.py — Funções científicas e trigonométricas
│   ├── comparison.py — Operadores de comparação
│   ├── logic.py      — Operadores lógicos
│   ├── variables.py  — Gestão de variáveis
│   ├── list_ops.py   — Operações com listas
│   └── program.py    — Interpretador RPL (programas + estruturas de controle)
├── tests/            — Testes unitários (pytest)
└── requirements.txt
```

## Persistência

O estado (stack, variáveis e configurações) é salvo automaticamente ao sair com `QUIT` e restaurado ao reiniciar. Os arquivos ficam em:

- `~/.rpn50g_state.json` — stack, variáveis e configurações
- `~/.rpn50g_history` — histórico de comandos

## Limitações (fora do escopo MVP)

- Unidades (HP 50g Units)
- Matrizes / vetores
- Álgebra simbólica / equações
- Gráficos
- Precisão arbitrária (usa float/int nativo do Python)
- Comunicação serial / USB com calculadora real

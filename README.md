# MyRPN Calculator Simulator

Simulador de calculadora **RPN** (Reverse Polish Notation) inspirado na HP 50g, implementado em Python como um REPL interativo de linha de comando.

## Funcionalidades

- **Stack infinita** com display estilo HP 50g (visor com moldura, barra de status, soft-keys de variáveis)
- **Aritmética**: `+`, `-`, `*`, `/`, `NEG`, `ABS`, `MOD`, `IP`, `FP`, `MIN`, `MAX`, `SIGN`, `%`, `FLOOR`, `CEIL`
- **Científico**: `SIN`, `COS`, `TAN`, `ASIN`, `ACOS`, `ATAN`, `LOG`, `LN`, `EXP`, `SQRT`, `SQ`, `^`, `INV`, `!`, `PI`, `SINH`, `COSH`, `TANH`, `D->R`, `R->D`, `XROOT`, `ALOG`
- **Manipulação de stack**: `DUP`, `DROP`, `SWAP`, `OVER`, `ROT`, `ROLL`, `PICK`, `DEPTH`, `CLEAR`, `DUP2`, `DROP2`, `DUPN`, `DROPN`, `NDUP`, `UNROT`, `ROLLD`
- **Comparação**: `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Lógica**: `AND`, `OR`, `NOT`, `XOR`, `IFT`, `IFTE`
- **Variáveis**: `STO`, `RCL`, `PURGE`, `VARS`, `STO+`, `STO-`, `STO*`, `STO/`
- **Listas**: `{ 1 2 3 }`, `LIST→`, `→LIST`, `GET`, `PUT`, `SIZE`, `HEAD`, `TAIL`, `REVLIST`, `SORT`, `SUB`, `ADD`, `NSUB`, `DOLIST`, `MAPLIST`, `STREAM`
- **Estatísticas de listas**: `ΣLIST`/`SUMLIST`, `SSQLIST`, `ΠLIST`/`PRODLIST`, `MAXLIST`, `MINLIST`, `MEAN`, `MEDIAN`, `SDEV`, `PSDEV`, `VAR`, `PVAR`, `TOTAL`, `ΔLIST`/`DELTALIST`
- **Vetores**: `[ 1 2 3 ]`, `DOT`, `CROSS`, `VNORM`, `TOVECT`, `FROMVECT`, `VGET`, `VPUT`
- **Matrizes**: `[[ [1 2] [3 4] ]]`, `DET`, `MINV`, `TRN`, `IDN`, `TRACE`, `RREF`, `TOMAT`, `FROMMAT`, `MDIMS`, `MGET`, `MPUT`, `CON`, `RANM`, `MNORM`
- **Aritmética vetorial/matricial**: `+`, `-`, `*`, `/`, `NEG`, `ABS` funcionam com vetores, matrizes e combinações escalar×vetor/matriz
- **Programas RPL**: `<< >>` ou `« »`, `EVAL`, `IF/THEN/ELSE/END`, `FOR/NEXT/STEP`, `START/NEXT/STEP`, `WHILE/REPEAT/END`, `DO/UNTIL/END`, `CASE/THEN/END`, `IFERR/THEN/ELSE/END`, `→` / `->` (variáveis locais)
- **Modos angulares**: `DEG`, `RAD`, `GRAD`
- **Formato de exibição**: `FIX n`, `SCI n`, `ENG n`, `STD`
- **Níveis visíveis da stack**: `STKL` (ex: `8 STKL` para exibir 8 níveis, padrão 4)
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
python repl.py
```

Ao iniciar, o REPL exibe o visor da calculadora HP 50g:

```
  MyRPN Simulator · HELP | UNDO | QUIT
  ╔═══════════════════════════════════════════════╗
  ║ RAD  STD                             { HOME } ║
  ╟───────────────────────────────────────────────╢
  ║  4:                                           ║
  ║  3:                                           ║
  ║  2:                                           ║
  ║  1:                                           ║
  ╠═══════╤═══════╤═══════╤═══════╤═══════╤═══════╣
  ║       │       │       │       │       │       ║
  ╚═══════╧═══════╧═══════╧═══════╧═══════╧═══════╝

>
```

A barra inferior (soft-keys) exibe automaticamente as variáveis definidas, como na calculadora real.

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
> { 10 20 30 40 50 } 2 4 SUB  — sublista: { 20 30 40 }
```

### Estatísticas de Listas

```
> { 1 2 3 4 5 } SUMLIST   — soma: 15
> { 1 2 3 } SSQLIST        — soma dos quadrados: 14 (1+4+9)
> { 2 3 5 } PRODLIST       — produto: 30
> { 3 1 4 1 5 } MAXLIST    — máximo: 5
> { 3 1 4 1 5 } MINLIST    — mínimo: 1
> { 2 4 6 } MEAN           — média: 4
> { 3 1 2 } MEDIAN         — mediana: 2
> { 2 4 4 4 5 5 7 9 } SDEV — desvio padrão amostral (n-1)
> { 2 4 4 4 5 5 7 9 } PSDEV— desvio padrão populacional (n)
> { 2 4 4 4 5 5 7 9 } VAR  — variância amostral (n-1)
> { 2 4 4 4 5 5 7 9 } PVAR — variância populacional (n)
> { 1 2 3 4 } TOTAL        — soma acumulada: { 1 3 6 10 }
> { 1 3 6 10 } ΔLIST       — diferenças sucessivas: { 2 3 4 }
```

### Programação Funcional com Listas

```
> { 1 2 3 } << DUP * >> DOLIST    — aplica a cada: { 1 4 9 }
> { 10 20 30 } << 1 + >> MAPLIST  — mapeia: { 11 21 31 }
> { 1 2 3 4 } << + >> STREAM      — reduce/fold: 10
> { 1 2 3 4 } << * >> STREAM      — reduce/fold: 24
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

### Variáveis Locais (→)

O operador `→` (ou `->`) captura valores da stack em variáveis locais, executa um bloco, e limpa as variáveis ao sair:

```
> 10 3 << -> A B << A B + >> >> EVAL
  1:                                       13

> << -> N << N N * >> >> 'SQ' STO
> 6 SQ
  1:                                       36

> 5 3 << -> X Y << X Y - X Y + * >> >> EVAL
  1:                                       16    — (5-3)*(5+3) = 16
```

### CASE (seleção múltipla)

```
> 2 << CASE
       DUP 1 == THEN "um" END
       DUP 2 == THEN "dois" END
       DUP 3 == THEN "tres" END
       "outro"
     END >> EVAL
  2:                                        2
  1:                                   "dois"
```

### IFERR (tratamento de erros)

```
> 4 0 << IFERR / THEN "Erro: divisão por zero" ELSE "OK" END >> EVAL
  1:                   "Erro: divisão por zero"

> 4 2 << IFERR / THEN "Erro" ELSE "OK" END >> EVAL
  2:                                        2
  1:                                     "OK"
```

### Vetores

```
> [ 1 2 3 ]                — empurra vetor na stack
  1:                             [ 1 2 3 ]

> [ 4 5 6 ] +                — soma vetor a vetor
  1:                             [ 5 7 9 ]

> [ 3 4 ] ABS                — norma euclidiana
  1:                                        5

> [ 1 0 0 ] [ 0 1 0 ] CROSS  — produto vetorial
  1:                             [ 0 0 1 ]

> [ 1 2 3 ] [ 4 5 6 ] DOT    — produto escalar
  1:                                       32

> [ 10 20 30 ] 2 VGET        — elemento na posição 2
  1:                                       20
```

### Matrizes

```
> [[ [ 1 2 ] [ 3 4 ] ]]      — empurra matriz 2×2
  1:                  [[ [ 1 2 ] [ 3 4 ] ]]

> [[ [ 5 6 ] [ 7 8 ] ]] *    — multiplicação de matrizes
  1:            [[ [ 19 22 ] [ 43 50 ] ]]

> [[ [ 1 2 ] [ 3 4 ] ]] DET  — determinante
  1:                                       -2

> [[ [ 1 2 ] [ 3 4 ] ]] MINV — inversa
  1:          [[ [ -2 1 ] [ 1.5 -0.5 ] ]]

> [[ [ 1 2 ] [ 3 4 ] ]] TRN  — transposta
  1:            [[ [ 1 3 ] [ 2 4 ] ]]

> 3 IDN                       — identidade 3×3
  1:    [[ [ 1 0 0 ] [ 0 1 0 ] [ 0 0 1 ] ]]

> [[ [ 1 2 ] [ 3 4 ] ]] 2 *  — escalar × matriz
  1:            [[ [ 2 4 ] [ 6 8 ] ]]

> [[ [ 1 2 ] [ 3 4 ] ]] [ 5 6 ] *  — matriz × vetor
  1:                           [ 17 39 ]
```

### Carregando Programas de Arquivo

Use o comando `LOAD` para carregar um arquivo `.rpl`:

```
> LOAD prog1.rpl
```

#### Formato do arquivo `.rpl`

```rpl
# somar
// comentário — linhas com // são ignoradas
<< WHILE DEPTH 1 > REPEAT + END >>

# negar
<< -> N << N NEG >> >>

// código anônimo (sem # name) é executado diretamente
3 4 +
```

**Regras:**

| Linha | Significado |
|-------|-------------|
| `# nome` | Inicia uma seção nomeada. O código que segue é armazenado em `variables['NOME']` como um `RPNProgram`. |
| `// ...` | Comentário — ignorado. |
| Código sem `#` | Seção anônima — executada imediatamente na stack (comportamento legado). |

- O nome é sempre extraído da **primeira linha após o símbolo `#`** e armazenado em **maiúsculas**.
- Se o corpo for um único bloco `<< ... >>`, seus tokens internos são usados diretamente. Caso contrário, todos os tokens são embrulhados em um novo `RPNProgram`.
- Após o `LOAD`, os programas ficam disponíveis como variáveis e podem ser chamados pelo nome:

```
> LOAD prog1.rpl
  Loaded 'prog1.rpl': SOMAR, NEGAR

> { 1 2 3 4 5 } SOMAR
  1:                                       15

> 7 NEGAR
  1:                                       -7
```

### Controles

| Comando | Descrição |
|---------|-----------|
| `LOAD arquivo` | Carrega arquivo `.rpl` e define programas nomeados como variáveis |
| `HELP`  | Lista todas as operações disponíveis |
| `UNDO`  | Desfaz a última operação |
| `n STKL` | Define o número de níveis visíveis na stack (1–32, padrão 4) |
| `QUIT` / `EXIT` / `Q` | Salva estado e encerra |
| `↑` / `↓` | Navega pelo histórico de comandos |

## Testes

```bash
# Testes do core da calculadora
python -m pytest tests/ -v

# Testes da API REST
python -m pytest api/tests/ -v

# Todos os testes
python -m pytest tests/ api/tests/ -v
```

```
tests/test_arithmetic.py  ✓ 14 tests
tests/test_list_stats.py  ✓ 36 tests
tests/test_matrix.py      ✓ 39 tests
tests/test_parser.py      ✓ 14 tests
tests/test_programs.py    ✓ 23 tests
tests/test_scientific.py  ✓ 15 tests
tests/test_stack.py       ✓  8 tests
tests/test_variables.py   ✓  6 tests
api/tests/test_auth.py    ✓  6 tests
api/tests/test_calculate.py ✓ 13 tests
api/tests/test_operations.py ✓  8 tests
api/tests/test_sessions.py  ✓  9 tests
                          ─────────
                         191 passed
```

## Estrutura do Projeto

```
rpn/
├── repl.py           — REPL interativo (entry point)
├── rpn_types.py      — Sistema de tipos (RPNNumber, RPNString, RPNList, RPNProgram, RPNSymbol, RPNVector, RPNMatrix)
├── stack.py          — Engine da stack RPN
├── parser.py         — Tokenizer/parser de entrada
├── operations.py     — Registry de operações + dispatch
├── display.py        — Formatação e visor estilo HP 50g
├── state.py          — Persistência em JSON (~/.rpn50g_state.json)
├── ops/
│   ├── arithmetic.py — Operações aritméticas
│   ├── stack_ops.py  — Manipulação de stack
│   ├── scientific.py — Funções científicas e trigonométricas
│   ├── comparison.py — Operadores de comparação
│   ├── logic.py      — Operadores lógicos
│   ├── variables.py  — Gestão de variáveis
│   ├── list_ops.py   — Operações com listas
│   ├── matrix.py     — Operações com vetores e matrizes
│   └── program.py    — Interpretador RPL (programas + estruturas de controle)
├── api/
│   ├── main.py       — FastAPI app factory (entry point da API)
│   ├── config.py     — Configuração via variáveis de ambiente
│   ├── database.py   — Async SQLAlchemy engine (SQLite)
│   ├── models.py     — ORM: User, CalcSession
│   ├── schemas.py    — Pydantic request/response schemas
│   ├── auth.py       — JWT + bcrypt password hashing
│   ├── calculator.py — Bridge entre API e core da calculadora
│   ├── dependencies.py — FastAPI Depends (auth, session loading)
│   ├── routers/
│   │   ├── auth.py       — Register, login, refresh
│   │   ├── sessions.py   — CRUD de sessões
│   │   ├── calculate.py  — Execute e undo
│   │   ├── stack.py      — Push, get, clear
│   │   └── operations.py — Descoberta de operações (público)
│   └── tests/        — Testes da API (pytest-asyncio)
├── tests/            — Testes unitários do core (pytest)
├── requirements.txt
├── Dockerfile        — Build multi-stage (Python 3.12-slim)
├── docker-compose.yml — Orquestração do container
└── .dockerignore     — Arquivos excluídos do build
```

## Docker

O projeto pode ser executado em container Docker, ideal para deploy da API REST.

### Requisitos

- Docker
- Docker Compose

### Subir o container

```bash
# Build e start
docker compose up -d

# Ver logs
docker compose logs -f api

# Parar
docker compose down
```

A API estará disponível em `http://localhost:8000` (docs em `/docs`).

### Configuração

Variáveis de ambiente podem ser definidas antes de subir o container:

```bash
# Gerar chave secreta segura
export RPN_SECRET_KEY=$(openssl rand -hex 32)

# Subir com a chave definida
docker compose up -d
```

Ou via arquivo `.env` na raiz do projeto:

```env
RPN_SECRET_KEY=sua-chave-secreta-aqui
RPN_CORS_ORIGINS=["https://meuapp.com"]
```

### Persistência

O banco SQLite é armazenado em um volume Docker nomeado (`rpn_data`), persistente entre reinicializações do container.

```bash
# Ver volumes
docker volume ls

# Remover volume (apaga o banco!)
docker volume rm repl_rpn_data
```

### Build manual da imagem

```bash
docker build -t rpn-calculator-api .
docker run -p 8000:8000 -e RPN_SECRET_KEY=minha-chave rpn-calculator-api
```

---

## Persistência (CLI)

O estado (stack, variáveis e configurações) é salvo automaticamente ao sair com `QUIT` e restaurado ao reiniciar. Os arquivos ficam em:

- `~/.rpn50g_state.json` — stack, variáveis e configurações
- `~/.rpn50g_history` — histórico de comandos

## Limitações (fora do escopo MVP)

- Unidades (HP 50g Units)
- Álgebra simbólica / equações
- Gráficos
- Precisão arbitrária (usa float/int nativo do Python)
- Comunicação serial / USB com calculadora real

---

## REST API

O projeto inclui uma **API REST** completa construída com **FastAPI**, permitindo integrar a calculadora RPN em aplicações web, mobile ou qualquer cliente HTTP.

### Iniciar o servidor

```bash
# Instalar dependências (se ainda não fez)
pip install -r requirements.txt

# Iniciar o servidor
uvicorn api.main:app --reload

# O servidor estará em http://localhost:8000
# Documentação interativa: http://localhost:8000/docs (Swagger UI)
# Documentação alternativa: http://localhost:8000/redoc
```

### Autenticação

A API usa **JWT (JSON Web Tokens)** com tokens de acesso e refresh.

```bash
# Registrar um usuário
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "email": "demo@example.com", "password": "secret123"}'

# Login (retorna access_token e refresh_token)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "secret123"}'

# Usar o token nas requisições autenticadas
export TOKEN="<access_token_recebido>"
```

### Sessões de cálculo

Cada usuário pode ter múltiplas sessões independentes, cada uma com sua própria stack, variáveis e configurações.

```bash
# Criar uma sessão
curl -X POST http://localhost:8000/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "minha_calc"}'

# Listar sessões
curl http://localhost:8000/sessions -H "Authorization: Bearer $TOKEN"
```

### Executar expressões RPN

```bash
# Calcular 3 4 + DUP *  →  49
curl -X POST http://localhost:8000/sessions/{session_id}/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "3 4 + DUP *"}'

# Desfazer última operação
curl -X POST http://localhost:8000/sessions/{session_id}/undo \
  -H "Authorization: Bearer $TOKEN"
```

### Manipulação direta da stack

```bash
# Ver a stack atual
curl http://localhost:8000/sessions/{session_id}/stack \
  -H "Authorization: Bearer $TOKEN"

# Push de um valor
curl -X POST http://localhost:8000/sessions/{session_id}/stack/push \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": 42, "type": "number"}'

# Push de um vetor
curl -X POST http://localhost:8000/sessions/{session_id}/stack/push \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": [1, 2, 3], "type": "vector"}'

# Limpar a stack
curl -X DELETE http://localhost:8000/sessions/{session_id}/stack \
  -H "Authorization: Bearer $TOKEN"
```

### Descoberta de operações (público, sem autenticação)

```bash
# Listar categorias
curl http://localhost:8000/operations/categories

# Listar operações (com filtros e paginação)
curl "http://localhost:8000/operations?category=arithmetic&limit=10"

# Buscar por nome
curl "http://localhost:8000/operations?q=SIN"

# Detalhes de uma operação
curl http://localhost:8000/operations/DUP
```

### Endpoints da API

| Método | Endpoint | Auth | Descrição |
|--------|----------|------|-----------|
| `POST` | `/auth/register` | Não | Registrar novo usuário |
| `POST` | `/auth/login` | Não | Login (retorna JWT) |
| `POST` | `/auth/refresh` | Não | Renovar token de acesso |
| `POST` | `/sessions` | Sim | Criar sessão de cálculo |
| `GET` | `/sessions` | Sim | Listar sessões do usuário |
| `GET` | `/sessions/{id}` | Sim | Detalhes da sessão (stack, vars, settings) |
| `DELETE` | `/sessions/{id}` | Sim | Remover sessão |
| `POST` | `/sessions/{id}/reset` | Sim | Resetar sessão |
| `PATCH` | `/sessions/{id}/settings` | Sim | Atualizar modo angular/formato |
| `POST` | `/sessions/{id}/execute` | Sim | Executar expressão RPN |
| `POST` | `/sessions/{id}/undo` | Sim | Desfazer última operação |
| `GET` | `/sessions/{id}/stack` | Sim | Ver stack atual |
| `POST` | `/sessions/{id}/stack/push` | Sim | Push de valor tipado |
| `DELETE` | `/sessions/{id}/stack` | Sim | Limpar stack |
| `GET` | `/operations/categories` | Não | Listar categorias de operações |
| `GET` | `/operations` | Não | Listar operações (filtro, busca, paginação) |
| `GET` | `/operations/{name}` | Não | Detalhes de uma operação |

### Configuração

Variáveis de ambiente (prefixo `RPN_`):

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `RPN_SECRET_KEY` | auto-gerado | Chave secreta para JWT |
| `RPN_DATABASE_URL` | `sqlite+aiosqlite:///./rpn_api.db` | URL do banco de dados |
| `RPN_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Validade do token de acesso |
| `RPN_CORS_ORIGINS` | `["*"]` | Origens CORS permitidas |

### Testes da API

```bash
# Executar testes da API
python -m pytest api/tests/ -v

# Executar todos os testes (core + API)
python -m pytest tests/ api/tests/ -v
```

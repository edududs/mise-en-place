> Arquivo historico da aula 5. Para o estado atual, consulte [CURSO.md](../../CURSO.md).

# Curso: concorrência em Python pela analogia da cozinha

Documento principal — a linha de raciocínio do curso inteiro, para não se perder
entre as aulas. Tudo aqui é decisão registrada, não rascunho.

**Ambiente**: Python 3.13.9, 10 cores, GIL ativo, **somente stdlib** (`uvx` disponível
para `mypy`/`ruff`/`hypothesis`).

### Layout do curso — cada aula é um SNAPSHOT completo

Uma aula não é um trecho de código: é **o todo naquele ponto da evolução**. Esse
princípio não mudou; o que mudou é *como* o snapshot é guardado — ver **§0**: até a aula
5 foi pasta-cópia, e da 6 em diante é tag + changelog no git (que dá o mesmo snapshot sem
duplicar o toolchain 150 vezes). O estado atual do disco:

- `ex1.py`, `ex2.py` — as duas primeiras, ainda de arquivo único.
- `ex3/`, `ex4/`, `ex5/`, … — **pastas**, cada uma um package autocontido (com
  packages internos), rodável com `python3 -m exN`.
- A aula N+1 é a aula N **inteira** mais os acréscimos dela. O **diff entre pastas
  é a aula**: nada quebra retroativamente e a evolução fica visível.

```bash
python3 ex1.py     python3 ex2.py           # aulas de arquivo único
python3 -m ex3     python3 -m ex4     python3 -m ex5
uvx mypy --strict ex1.py ex2.py             # tem que passar limpo, sempre
uvx mypy --strict -p ex3 -p ex4             # (um alvo por vez: mypy não mistura)
uvx ruff format .  &&  uvx ruff check .
```

**Regra de lint registrada**: `TID252` (preferir import absoluto) fica **desligada** de
propósito. São os imports relativos que fazem cada pasta de aula ser autocontida e
copiável sem mexer em `sys.path` — é a decisão de layout mandando na ferramenta, e não
o contrário.

---

## 0. Repositório, versionamento e toolchain

**Escala real do projeto: 150+ aulas.** Isso muda a resposta sobre layout, e a razão é
uma só: **dependência e ferramenta não podem ser duplicadas.**

### A decisão: um repo, uma versão por aula, changelog e tag

Com `pydantic`, `rich`/`textual`, `uv.lock`, `ruff.toml` e `pyrightconfig.json` no jogo,
150 pastas-cópia significam **150 cópias do toolchain**. Subir a versão do pydantic uma
vez produziria 150 aulas divergentes, das quais 149 ninguém vai corrigir. Não é questão
de estilo — é o que mataria o projeto por volta da aula 20.

E o que a pasta-cópia dava, o git devolve inteiro:

| Necessidade | Como fica |
|---|---|
| "cada aula é o todo e roda pra sempre" | `git checkout aula-042` — o mundo inteiro naquele ponto |
| "abrir duas aulas lado a lado" | `git worktree add ../aula-041 aula-041` — pastas reais, zero cópia manual |
| "não perder a evolução" | tag imutável + `CHANGELOG.md` + `git diff aula-041 aula-042` |
| "ver todas as aulas na árvore" | `docs/aulas/NNN-titulo.md` fica em `main` **para sempre** |

O princípio que resolve a tensão: **doc acumula, código evolui.** A narrativa de toda
aula continua visível em `main` (uma página markdown por aula, permanente); só o *código*
daquela aula vive na tag. Nada de 150 cópias, nada de aula perdida.

Bônus: versionamento passa a ser **matéria** do curso (SemVer, Conventional Commits,
changelog derivado do histórico, tag imutável, CI por tag).

**Exceção registrada (Rule of Three)**: em saltos arquiteturais grandes — o antes/depois
da hexagonal, por exemplo — vale manter *uma* pasta-snapshot para o diff ficar lado a
lado no doc. Uma, quando ganhar; não por padrão.

**Migração — feita.** `git init` + um commit por aula + tag `aula-01..aula-05`, com
`CHANGELOG.md` e uma página por aula em `docs/aulas/`. Verificado:
`git worktree add ../aula-03 aula-03` produz uma árvore com apenas `ex1/ex2/ex3` e ela
roda isolada.

**Primeiro movimento da aula 6** (planejado, não feito): promover `ex5/` ao projeto vivo
(`src/`) e apagar `ex3..ex5` no mesmo commit — recuperáveis pra sempre nas tags. Enquanto
as cópias existem, o diff `aula-03..aula-04` acusa 33 arquivos e 2220 linhas quando a
aula acrescentou **um package**: é a duplicação falando alto, e é o próprio argumento da
consolidação.

### Forma do repositório

```
cozinha-tycoon/                    # repo único, uv
├── pyproject.toml                 # uv + deps (workspace quando a hexagonal chegar)
├── uv.lock  ruff.toml  pyrightconfig.json
├── CHANGELOG.md                   # uma entrada por aula
├── CURSO.md                       # este documento: o norte
├── docs/aulas/NNN-titulo.md       # a narrativa de cada aula, permanente
├── docs/specs/<assunto>.md        # a pesquisa de operação real (§5.2)
├── src/                           # as 8 caixas da §5 como packages
└── tests/
```

**Ideia registrada para a trilha T3**: quando a hexagonal chegar, transformar as caixas
em **membros de workspace `uv`** — aí a fronteira deixa de depender de disciplina e passa
a ser imposta pelo gerenciador de pacotes (o package de domínio *não consegue* importar
`textual`, porque `textual` não é dependência dele). Fronteira verificada por
ferramenta > fronteira combinada por convenção.

### Toolchain (padrão herdado do workspace VR + endurecido)

- **`uv`** para tudo: `uv run`, `uv add`, `uv.lock` commitado.
- **`ruff`** com `select = ["ALL"]`, `preview = true` + `explicit-preview-rules = true`,
  e ignores por **nome de regra** (não código) — igualzinho ao `ruff.toml` do `feeds`,
  que é a fonte única do padrão. Herdar dele: `line-too-long` ignorado (formatter cuida),
  `relative-imports` ignorado, docstrings obrigatórias desligadas, `print` liberado,
  `per-file-ignores` para testes. `line-length = 100`, `target-version = "py313"`.
- **`pyright`** com a forma do `pyrightconfig.json` do welcome, mas em
  **`typeCheckingMode: "strict"`**: aqui é greenfield, não tem legado pra acomodar, e o
  objetivo declarado é 100% de tipagem. Diferença consciente em relação ao padrão do
  workspace (que usa `standard` + ~40 regras em `warning` porque convive com Django).
- **`mypy --strict`** também, enquanto for barato: dois checadores discordam em casos
  reais (variância, `Protocol`, narrowing) e cada discordância dessas é uma aula.
- **`pytest`** + `pytest-asyncio` + **`hypothesis`** (trilha T7).

---

## 1. O contrato didático

Regras que valem para todo arquivo do curso — as mesmas convenções do workspace
`mobile-sim-welcome` (`.cursor/skills/ecosystem-arch/SKILL.md` §6 + Tipagem Estática):

- `from __future__ import annotations`; type hints em tudo; `mypy --strict` limpo.
- `X | None` (nunca `Optional`); return types explícitos; `Iterator`/`AsyncIterator`
  no lugar de `Generator`/`AsyncGenerator` quando o chamador só percorre (ISP).
- Zero magic numbers/strings: constante `Final` nomeada ou `Enum`.
  - **Exceção registrada**: dentro de literal de `dataclass` congelada, o *nome do
    campo* já nomeia o número (`chance_de_sobremesa=0.80`). Criar 36 `Final` para os
    campos de um perfil pioraria a leitura. `Final` fica para os botões de regência
    (taxas, quantidade de garçons, fator de tempo, sementes).
- Guard clauses; sem primitive obsession (`dataclass`); SRP; sem God Object.
- Arquivo com ~500 linhas no máximo; package expõe facade mínima no `__init__.py`.
- Nomes de domínio em português; exceções com sufixo `Error`.
- **O código é a aula**: comentário explica o *porquê* e amarra na analogia.
  Cada arquivo fecha com um bloco "as lições" no rodapé.

---

## 2. Mapa da analogia (tabela mestra)

| Cozinha | Python | Lição |
|---|---|---|
| Expedidor (uma pessoa, nunca para) | event loop | se ele para, o restaurante todo para |
| Pedido em andamento | `Task` | unidade de trabalho independente |
| Receita | `async def` / gerador de passos | política: o que fazer |
| Forno / água fervendo | `await` | espera não ocupa ninguém |
| Cozinheiro olhando a panela | `time.sleep` | o pecado mortal |
| Sovar 10kg de massa | trabalho CPU-bound | async não ajuda; precisa de outro core |
| Balcão de pedidos | `asyncio.Queue` | de onde a brigada puxa |
| Balcão com limite | `Queue(maxsize=N)` | backpressure: a pressão aparece na porta |
| Vagas da estação | `asyncio.Semaphore` | recurso escasso do restaurante |
| Ticket completo | `asyncio.TaskGroup` | sai tudo ou cancela tudo |
| "15 min e não saiu, refaz" | `asyncio.timeout` | prato travado ≠ cozinheiro travado |
| Ajudante pra descascar batata | `asyncio.to_thread` | I/O bloqueante fora do loop |
| Bancada extra com cozinheiro | `ProcessPoolExecutor` | CPU real, outro core |
| Tábua de corte única | GIL | por isso thread não resolve CPU |
| Mise en place | connection pool / client reusado | não ir ao mercado por pedido |
| Praça independente (bar) | fila + recursos próprios | drink na espera sai de graça |

---

## 3. Estado atual — o índice das aulas

O detalhe de cada aula mora em `docs/aulas/` (uma página por aula, permanente em `main`).
Aqui fica só o índice, para este documento não virar uma segunda fonte de verdade.

| # | Aula | Rodar | Ensina |
|---|---|---|---|
| 01 | [Fundamentos](../aulas/001-fundamentos.md) | `python3 ex1.py` | espera × esforço · `gather` × `TaskGroup` · fila, semáforo, timeout, fim de turno |
| 02 | [POO e geradores](../aulas/002-poo-e-geradores.md) | `python3 ex2.py` | organograma de responsabilidades · receita como `Iterator[Step]` · `@asynccontextmanager` · armadilhas de gerador |
| 03 | [Restaurante completo](../aulas/003-restaurante-completo.md) | `python3 -m ex3` | comanda com cursos · EDF sem starvation · praças independentes · validador de fronteira |
| 04 | [Salão vivo](../aulas/004-salao-vivo.md) | `python3 -m ex4` | porta declarada pelo consumidor · chegadas de Poisson · drink como task paralela · desistência |
| 05 | [Medir antes de otimizar](../aulas/005-medir-antes-de-otimizar.md) | `python3 -m ex5` | instrumento errado mente · Teoria das Restrições · saturação não-linear |

## 4. O package `restaurante/` (a espinha, já construída no ex3)

> **Nota de histórico**: a reflexão de arquitetura recomendou "um package, três pontos
> de entrada". Foi **substituída** pela decisão do usuário de snapshot por aula (§1) e,
> na sequência, pela decisão de versionamento em git (§0). Fica registrado porque o
> argumento original — três cópias são três fontes de verdade — continua **correto**, e é
> exatamente por isso que a §0 existe: o git resolve as duas coisas ao mesmo tempo.

**Premissa que muda**: no `ex2` a unidade de trabalho é o `Pedido`. Agora é a
**comanda da mesa**, com cursos que têm dependência temporal entre si (entrada sai
primeiro, o principal só depois que a mesa comeu), enquanto os drinks correm por fora.

### Decisões já tomadas

1. **Prioridade ≠ sequência, e cada uma tem um dono diferente.** Três reflexões
   independentes divergiram aqui; a decisão registrada é:
   - a **mesa** manda na *sequência* (`await` a rodada → come → pede o próximo curso).
     `await` **é** a máquina de estados; o estado mora no program counter.
   - o **orquestrador** manda na *ordem entre mesas* (EDF, `PriorityQueue`) e não sabe
     o que é curso.
   - o **validador** manda no *invariante* ("principal antes da entrada" é recusa de
     fronteira, não regra de escalonamento).
   Se a sequência vazar pro orquestrador (`if curso == PRINCIPAL` no despacho), a
   cozinha passa a conhecer política de salão e vira God Object. **Não há gate.**

   **Chave de ordenação EDF** (starvation-free por construção — prazo é estático,
   calculado uma vez no `put`; um pedido velho só pode virar o de prazo mais próximo):
   ```python
   (prazo_min, curso, indice_na_rodada, sequencia_global)
   ```
   O `sequencia_global` (de um `itertools.count`) **não é enfeite**: sem ele o empate
   faz o heap comparar o payload → `TypeError` no 2º `put`. Medido sob sobrecarga:
   prioridade estrita ⇒ pedido comum **nunca servido**; EDF ⇒ pior caso 82 ticks.
   Aging teria pior caso um pouco melhor, mas exige *rekey* — e `PriorityQueue` não
   tem API de rekey (a chave congela no `put`), o que obrigaria a escrever um heap.
2. **O bar não tem gate**: praça própria, fila própria, recursos próprios ⇒ "drink
   durante a espera" cai de graça, sem um único `if curso == DRINK`.
3. **Um package, três pontos de entrada** (não três cópias — seriam três fontes de
   verdade). `ex3/ex4/ex5` são *composition roots* que ligam mais peças do mesmo código.
4. **Papéis novos**: `Validador` (parse-don't-validate na fronteira) e `Orquestrador`
   (único dono do sequenciamento: prioridade + gate + despacho).
5. **`clientela/` (a "IA") não conhece asyncio nem a cozinha.** A porta é um `Protocol`
   declarado no *consumidor* (DIP de verdade, não cerimônia), e os itens atravessam
   como `str` — a tradução é do adaptador, e é isso que dá causa real ao
   `PratoForaDoMenuError` ("a mesa pediu polenta").
6. **A mesa é uma coroutine, não um `while` + `Enum`.** Numa aula de asyncio, `await`
   *é* a máquina de estados — o estado mora no program counter. O `Enum` continua, mas
   como **dado observável** (gancho de log), não como controle de fluxo.
   Trade-off nomeado: gerador de intenções + `heapq` seria o certo para um DES
   determinístico (é o que o SimPy faz), mas aí a aula deixa de ser sobre asyncio.
7. **Drink é task paralela, não estado da mesa.**
8. **Garçom é fila + N workers, não `Semaphore`**: o semáforo daria "3 por vez" e
   perderia a *identidade* (sem ela não há ocupação por garçom nem "Ana atendeu 17
   chamados"). Reusar balcão/cozinheiro num segundo nível **é** a lição.
9. **Garçom como gargalo proposital**: 3 garçons para 10 mesas (ρ≈0.94) — gargalo
   visível sem colapsar. A lição que fecha a aula: *o gargalo pode não ser a cozinha*.
10. **Chegadas de Poisson** (`random.expovariate`, ~1 mesa/6min): intervalo uniforme
    esconderia a rajada, e é a rajada que satura o garçom.
11. **Tempo simulado com fator de escala**: `1 min = 0.05s`; **nenhum módulo chama
    `asyncio.sleep` — só o `Relogio`** (SSoT do fator). Log em `[HH:MM]` do
    restaurante, nunca em segundos: `[20:14] mesa 3` conta história, `7.42s` não.
12. **`random.Random` por mesa, derivado de um mestre.** Com asyncio o entrelaçamento
    pode variar entre máquinas; um `Random` compartilhado faria a aula sair diferente.
    Modo caótico permitido, mas **sempre imprimindo a semente sorteada**.

13. **Fila central priorizada, estação como `Semaphore` adquirido sob demanda** —
    e não uma fila por estação. Regra que sustenta: **o prato é a unidade de trabalho;
    a estação é recurso, não fila.** Prioridade só significa algo se houver *uma* fila.
    Trade-off nomeado: perde-se afinidade e batching por estação.
14. **Um passo ocupa UMA estação** ⇒ deadlock é impossível por construção. Se algum dia
    um passo precisar de duas (fogão *e* forno), a cura é ordem canônica global de
    aquisição via `AsyncExitStack` + `sorted(..., key=ORDEM_CANONICA.index)` — validado:
    sem ela, duas receitas em ordem oposta travam de verdade.
15. **`Barrier` é armadilha**: sozinho ele *deadlocka* silenciosamente se uma parte for
    cancelada antes de chegar (e `broken` continua `False`). `TaskGroup` por rodada
    resolve "sai junto" sem isso. Distinção da aula: `Barrier` sincroniza o *fim do
    cozimento*; `TaskGroup` sincroniza a *entrega*.
16. **`Queue.shutdown()` (novidade do 3.13) fecha a brigada sem um único `cancel()`** —
    o worker sai por `except asyncio.QueueShutDown`. É a evolução direta do padrão de
    `ex1`/`ex2`, e vira lição de "o que mudou no Python moderno".
17. **Coalescing só onde o recurso é capacidade de lote** (o forno assa 3 no mesmo
    ciclo), e a janela de coalescência **tem** de respeitar o prazo, senão o batching
    quebra a promessa do EDF:
    `janela = max(0, min(prazos do lote) - agora - duração_do_ciclo)`.
    Afinidade de estação fica de fora: num simulador não há custo de troca, então
    otimizar isso é otimizar um número inventado.
18. **`nucleo/contratos.py` não existe.** A reflexão de arquitetura propôs um módulo só
    de `Protocol`s para quebrar ciclo de import — mas o ciclo não se materializa:
    `Diario` mora em `observabilidade/` (folha) e `Atendimento` em `clientela/portas.py`
    (declarado por quem **consome**, que é o DIP de verdade). Módulo que existe só para
    resolver um problema que não aconteceu é YAGNI.

### Rejeitado por YAGNI/KISS (registrado para não voltar)

- **Event bus** neste estágio: as setas já são filas nomeadas; o bus trocaria 6 arestas
  visíveis por zero. (Volta como *tema* na aula de event-driven — ver §5.)
- **DI container**: o `__init__` do `Restaurante` é o composition root, ~25 linhas.
- **Repositório/persistência**: nada sobrevive ao turno.
- **State machine formal**: 3 estados e uma transição legal ⇒ `Enum` + guard clause.
- **Hierarquia `Trabalhador` → `Cozinheiro`/`Barman`**: o loop é idêntico; a diferença
  é *configuração* (praça, cardápio, recursos), não código. Mesma classe, dois nomes
  no vocabulário da aula.
- **`asyncio.Lock` em métricas / threads / processos "pra otimizar"**: loop
  single-thread; o trabalho aqui é espera simulada. Paralelizar ensinaria errado.

### Divisão (implementada nas aulas 3-5)

- **ex3 — o restaurante completo, determinístico.** Comandas roteirizadas, sem
  aleatoriedade. Ensina sequenciamento por curso (PriorityQueue + gate), `Receita.passos()`
  ocupando recurso por etapa, e praças independentes (bar).
- **ex4 — o salão vivo.** `clientela` (gerador infinito de chegadas), mesas, garçons,
  drink durante a espera. Ensina produtores independentes, backpressure real,
  `TaskGroup` aninhado por mesa e cancelamento (mesa desiste; bar fecha antes da cozinha).
- **ex5 — fechamento.** Timeline, métricas por praça, `debug=True`, e o experimento
  "tire um forno e meça". Ensina medir antes de otimizar.

---

## 5. O norte (leia isto antes de propor qualquer coisa)

Isto **não** é uma sequência de exemplos didáticos que termina no ex5. O alvo é um
**simulador overhaul** de operação de restaurante — **150+ aulas** — em que cada assunto
de engenharia entra quando o simulador precisa dele, não antes. O `ex1`–`ex5` é o
"por onde começar", não o escopo.

### As caixas (o que tem que ficar isolado, sem exceção)

Cada uma é um contexto com fronteira própria, porta própria e vocabulário próprio.
Nada atravessa a fronteira sem passar por uma porta declarada:

| Caixa | Do que ela é dona | O que ela NÃO pode saber |
|---|---|---|
| **Ambiente** | o estabelecimento: layout, praças, estações, inventário físico | que existe jogo, jogador ou IA |
| **Tempo** | o clock próprio: escala, pausa, velocidade, dia/turno | qualquer regra de negócio |
| **Recursos** | insumos, estoque, dinheiro, equipamento, energia | quem consome |
| **Pessoas** | staff (funções, habilidade, cansaço, turno) e clientes (comportamento) | como se cozinha / como se cobra |
| **Operação** | pedidos, comandas, filas, orquestração, expedição | de onde vem a demanda |
| **Jogo vivo** | a sessão em execução: estado, progressão, decisões do jogador | detalhes de execução das praças |
| **Interface** | terminal: render, input, narrativa | qualquer regra; ela só projeta estado |
| **Persistência** | save/load, log de eventos, replay | semântica do domínio |

**Regra de ouro do projeto**: o motor não recebe `if` novo. Personagem novo, prato novo,
estação nova, fase nova, upgrade novo = **dado novo + adaptador novo**. Se exigir mexer
no motor, a fronteira está no lugar errado. Essa é a prova prática do
mechanism-not-policy — e é também o que permite "adicionar macaco novo" (ver §5.3)
numa atualização sem tocar no núcleo.

### 5.1 Trilhas de assunto (cada uma vira várias aulas)

| # | Trilha | Assuntos previstos |
|---|---|---|
| **T1** | **Concorrência** | ✅ fundamentos, TaskGroup, filas, semáforo, timeout, cancelamento · EDF/aging/WFQ · `Condition`/`Barrier` · deadlock, starvation, backpressure · `Queue.shutdown` · supervisão e reinício de worker · graceful shutdown |
| **T1.5** | **Pydantic (núcleo do jogo)** | modelos de fronteira e `model_validate` · `Field` e constraints · validadores custom · **discriminated unions** (é o mecanismo dos tipos de cozinheiro) · `TypeAdapter` · serialização e save/load · `pydantic-settings` · **conteúdo como DADO validado** (personagem/upgrade/fase em YAML validado por modelo — é o que faz "dado novo, não `if` novo" ser seguro em vez de temerário) · custo de validação e onde NÃO validar |
| **T2** | **Python idiomático** | ✅ geradores, `yield from`, `asynccontextmanager` · `Protocol`, ABC, descritores, `__slots__` · pattern matching · `itertools`/`functools` · typing avançado (genéricos, variância, `Self`, `TypedDict`, overload) · metaclasses e `__init_subclass__` (registro de plugin) |
| **T3** | **Arquitetura** | SoC → **hexagonal (portas & adaptadores)** → **DDD** (agregado, invariante, linguagem ubíqua, contexto delimitado) → CQRS → **event-driven/event bus** → outbox, idempotência, saga → event sourcing + replay |
| **T4** | **Tempo & simulação** | escala vs **clock virtual** · DES com heap de eventos · determinismo e reprodutibilidade · pausa/velocidade/turno · replay e snapshot |
| **T5** | **Recursos & escalonamento** | teoria de filas (Little, ρ, M/M/c) · políticas de scheduling · **autoscaling** (contratar garçom quando a demanda sobe) · capacity planning · gargalo móvel |
| **T6** | **Pessoas & IA** | perfis e utility AI · **behavior tree** · comportamento previsível e legível (o pedido explícito: menos sorteio, mais regra testável) · habilidade, cansaço, aprendizado · fila de espera e desistência |
| **T7** | **Testes** | unidade em async · **property-based com Hypothesis** · `RuleBasedStateMachine` sobre a cozinha · simulação determinística como teste de regressão · fuzz de concorrência · benchmark e teste de carga |
| **T8** | **Observabilidade** (7 aulas — ver §5.1.1) | conceito antes de ferramenta · eventos estruturados · métricas e percentis · tracing e contexto · timeline no terminal · SLI/SLO/error budget · custo da instrumentação |
| **T8.5** | **Interface no terminal** | `rich` primeiro (Console, Table, Live, Progress) para o jogo narrado · `textual` só quando precisar de widget/input de verdade — KISS/YAGNI mandam começar pelo menor · separar RENDER de ESTADO (a interface só projeta; nenhuma regra mora nela) · acessibilidade do texto e legibilidade do log |
| **T9** | **O jogo (tycoon)** | game loop separado do domínio · economia (CMV, preço, desperdício) · progressão e upgrades · ondas de demanda · UI de terminal · save/load · **mods via entry points** |
| **T10** | **Desempenho** | medir antes · uvloop · batching/coalescing · processos vs free-threading · onde async não ajuda |

### 5.1.1 Trilha T8 — Observabilidade em 7 aulas

Merece trilha própria porque **é a única matéria que já provou seu valor dentro do
curso**: na aula 5 o instrumento errado (medir estações em vez de cozinheiros) produziu
uma conclusão errada com números convincentes. Observabilidade não é enfeite de
produção — é o que separa engenharia de chute com gráfico.

E há uma vantagem didática rara aqui: o simulador **já tem** o pipeline
(`Evento` → `Diario` → `Metricas`), então cada aula evolui um código vivo em vez de
montar exemplo de brinquedo.

| # | Aula | O que ensina |
|---|---|---|
| **8.1** | **Conceito**: observabilidade ≠ monitoramento | monitoramento responde pergunta **conhecida** (dashboard pronto); observabilidade responde pergunta **nova** (alta cardinalidade). Os "três pilares" (log/métrica/trace) e por que a divisão é incompleta: o **evento largo** (canonical log line) como fonte única, de onde log, métrica e trace são *derivados* — SSoT aplicado a telemetria |
| **8.2** | **Eventos estruturados em Python** | o `logging` da stdlib de verdade (hierarquia de logger, handler, filter, `extra`, `LogRecord`) · `structlog` · **`contextvars`**: como o "id do pedido" se propaga por toda a árvore de tasks do asyncio **sem passar parâmetro** — e por que isso é possível em async e não em thread pool ingênuo |
| **8.3** | **Métricas e a mentira da média** | contador, gauge, histograma · por que média esconde o problema e **percentis (p50/p95/p99)** o revelam · **RED** (Rate/Errors/Duration) e **USE** (Utilization/Saturation/Errors) · **Little's Law** ligando fila, vazão e espera · e a lição da aula 5: *medir o recurso certo* |
| **8.4** | **Tracing: um pedido ponta a ponta** | span, trace, parent/child, propagação de contexto · OpenTelemetry em Python · o que um trace do pedido mostra e o relatório não: **quanto do tempo foi FILA e quanto foi FOGO** — a distinção que decide se você contrata ou compra equipamento |
| **8.5** | **Timeline no terminal** | desenhar o gantt do pedido com `rich`, correlacionado com a narrativa do jogo · uma linha por mesa, uma faixa por curso · quando visualização revela o que tabela nenhuma revelou |
| **8.6** | **SLI, SLO e error budget** | o `PROMESSA_MIN` do cardápio **é literalmente um SLO** ("principal em 20 min") · medir cumprimento em vez de média · error budget · alerta por **burn rate** em vez de threshold · e a decisão de negócio que sai daí: baixar a promessa ou aumentar a capacidade |
| **8.7** | **O custo de observar** | overhead da instrumentação · sampling · **explosão de cardinalidade** · `asyncio` debug mode e `slow_callback_duration` · `cProfile`/`py-spy` · e o efeito observador: **medir altera o timing** — em simulação isso é armadilha de verdade, não filosofia |

### 5.2 Trilha de pesquisa (specs do estabelecimento real)

Cada parte da operação real merece uma **spec própria** antes de virar código —
é o que vai dar densidade ao simulador em vez de vira-lata de suposição minha.
Ordem sugerida de pesquisa (`specs/<assunto>.md`), a fazer com pesquisa de verdade:

1. **Brigada de cozinha real** (Escoffier e o que sobrou dela): chef de partie, saucier,
   entremetier, garde manger, pâtissier, aboyeur/expedidor, plongeur — quem grita o quê.
2. **Mise en place e prep**: o que é feito antes do serviço, e como isso muda a fila.
3. **Fluxo de serviço**: sequência de cursos, *firing* do próximo curso, tempo de mesa
   (dwell), rodízio de mesa (turnover), *coursing* e *pacing*.
4. **Expedição e o pass**: como uma rodada "sai junta" de verdade, janela de calor,
   *all-day* (contagem agregada de itens iguais na fila).
5. **Front of house**: hostess, fila de espera, reservas, no-show, walk-in, sections
   por garçom, *bussing*.
6. **Bar**: fila própria, batching de drinks, garnish prep, *well drinks* vs autorais.
7. **POS e comanda**: como o pedido entra, modificadores ("sem cebola"), *voids*,
   split de conta, gorjeta.
8. **Estoque e custo**: CMV/food cost, *par levels*, quebra, validade, compras.
9. **Escala de pessoal**: turnos, hora extra, absenteísmo, produtividade por posição,
   custo por hora — a matéria-prima do autoscaling do jogo.
10. **Métricas do setor**: ticket médio, tempo de mesa, *covers* por hora, RevPASH,
    tempo de ticket por estação.
11. **Segurança alimentar e regulatório** (o que couber): temperatura, HACCP, checklists.
12. **Delivery/takeout**: uma segunda demanda concorrente com prioridade diferente.

### 5.3 O jogo, especificamente

Referências declaradas pelo usuário: **simulador de sistema do Lucas Montano** (a ideia
de simular um sistema real com regência de parâmetros) e **Bloons TD** (ondas de
demanda, torres/trabalhadores, upgrades, e conteúdo novo entrando por atualização).

O que isso implica em engenharia, e que é o motivo de a hexagonal aparecer aqui:

- **Ondas de demanda** = o `clientela`/gerador de chegadas com taxa variável por
  fase/horário. A "onda 12" é dado, não código.
- **Trabalhadores e escalonamento** = contratar/demitir garçom, cozinheiro, barman em
  tempo de jogo; ver o gargalo se mover; pagar por isso.
- **Upgrades** = comprar mais uma boca de fogão, um forno melhor, treinar staff. Cada
  upgrade é um **efeito declarado** sobre um recurso — nunca um `if` no motor.
- **Conteúdo novo por atualização** ("macaco novo") = personagem/estação/prato/fase novos
  entram como **plugin registrado numa porta**, sem recompilar o núcleo. É o teste final
  da arquitetura: se dá pra adicionar um cargo novo sem tocar em `servico/`, a fronteira
  está certa.
- **Decisão do jogador** = a única política que vem de fora do sistema em tempo real;
  ela entra por uma porta de comandos, e o jogo vivo é o único que a conhece.

### 5.3.1 Referências de boas práticas a estudar

- **Projetos abertos do Fabio Akita** (indicação do usuário): levantar quais repos ele
  mantém públicos e extrair o que dá pra adotar aqui — organização de projeto, higiene
  de commit/PR, README/documentação, setup reproduzível, postura sobre engenharia. **A
  fazer com pesquisa de verdade** (não de memória) antes de virar convenção do curso.
- Bibliotecas SOTA a avaliar quando o problema aparecer, e só então: `structlog`
  (eventos estruturados), `tenacity` (retry declarativo), `cyclopts`/`typer` (CLI),
  `whenever` (tempo correto), `msgspec` (serde rápido, se o pydantic pesar),
  `simpy` (comparação honesta na trilha T4: como um DES de verdade faria).
  Regra: biblioteca entra quando o problema existe e dói — não porque é SOTA.

### 5.4 Como cada aula deve terminar

Toda aula precisa deixar (1) código que **roda** e imprime algo legível, (2) um bloco de
lições no rodapé do arquivo, (3) uma entrada neste documento com a decisão e o *porquê*,
e (4) — a partir da trilha T7 — teste que prove a invariante que a aula introduziu.

## 5.5 Achados de linguagem (verificados na construção, viram aula)

- **`asyncio.Queue.shutdown()`** (3.13) + `except asyncio.QueueShutDown` fecha a brigada
  **sem um único `cancel()`**: o worker sai pela porta da frente em vez de ser
  interrompido no meio de um prato. É a evolução direta do padrão do `ex1`/`ex2`.
- **`return`, `break` e `continue` são SyntaxError dentro de `except*`** (verificado com
  `compile()` — `ast.parse` NÃO acusa). O motivo: o bloco pode rodar mais de uma vez,
  uma por tipo de exceção do grupo. Resultado sai por variável, não por `return`.
- **`contextlib.aclosing` exige `AsyncGenerator`, não `AsyncIterator`.** Os dois
  funcionam em `async for`, mas só o primeiro declara `aclose()`. Regra: `AsyncGenerator`
  no **retorno** de quem produz, `AsyncIterator` no **parâmetro** de quem consome (ISP).
- **`PriorityQueue` sem tiebreaker estoura** `TypeError` no 2º `put` (o heap tenta
  comparar o payload). Daí o `sequencia` de um `itertools.count` na chave — que também
  torna o desempate FIFO-estável.
- **`PriorityQueue` não tem rekey**: a chave congela no `put`. É o que descarta *aging*
  como política sem escrever um heap próprio — e o que faz o EDF (prazo estático) ser a
  escolha certa aqui.
- **`Barrier` sozinho deadlocka em silêncio** se uma parte for cancelada antes de chegar
  (e `broken` continua `False`). Dentro de `TaskGroup`, não.
- **`Condition.wait_for(predicado)`** é o primitivo do estado COMPOSTO ("existe mesa
  livre **e** que caiba o grupo"). `Event` é broadcast sem estado; `Queue` modela
  trabalho, não recurso com atributo.

---

## 6. Dívidas conhecidas

- `ex1.py`/`ex2.py` usam `random.seed()` global. É uma **segunda fonte de verdade**:
  qualquer código que chame `random.*` rouba números da sequência e a aula deixa de
  sair igual. Correto é `random.Random(semente)` injetado. Mantido nos dois primeiros
  arquivos por simplicidade didática; **o package usa `Random` instanciado**.
- **Duplicação entre snapshots (a dívida estrutural do curso).** `ex3`, `ex4` e `ex5`
  carregam cópias do package `restaurante/`. É SSoT violado de propósito: um bug
  encontrado no `ex5` não se propaga sozinho para o `ex3`. O ganho é pedagógico (cada
  aula roda para sempre; o diff entre pastas é a aula) e foi escolha explícita do
  usuário. **A alternativa que dá as duas coisas é git**: um repositório com uma
  tag/branch por aula entrega "snapshot completo" sem N cópias no disco, ao custo de
  não dar mais para abrir duas aulas lado a lado no editor. Decisão pendente — e ela
  fica mais caras de reverter a cada aula nova, então vale resolver cedo.
- **`Restaurant.__init__` tem 9 argumentos** e ganhou exceção de lint por arquivo (em vez
  de afrouxar `max-args` global). É defensável — o composition root reúne colaboradores
  por definição — mas é o lint apontando para uma evolução real: quando a configuração
  do estabelecimento crescer (T9: escala de turno, inventário, upgrades), esses
  argumentos viram um **modelo de configuração**. E é exatamente ali que o Pydantic
  entra: config validada, serializável e salvável, em vez de nove parâmetros soltos.
- `ex2.Kitchen.__aenter__` entra no `TaskGroup` manualmente: exige que entrada e saída
  ocorram na **mesma task** (é o caso no `async with` e no lifespan do FastAPI). Se um
  dia `abrir()`/`fechar()` vierem de tasks diferentes, o padrão é outro (task supervisora).

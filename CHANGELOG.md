# Changelog

Uma entrada por aula. Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/);
cada aula tem uma tag `aula-NN` apontando para o commit correspondente.

## [aula-05] Medir antes de otimizar: onde está o gargalo

### Adicionado
- `ex5/`: a mesma noite rodada em seis cenários, mudando uma coisa por vez, com relógio acelerado (`minute_s = 0.01`).
- Instrumentação do preparador: ocupação e itens por cozinheiro.

### Corrigido
- **O instrumento.** A aula 4 media a ocupação das estações e não a dos cozinheiros — e com isso o forno (40%) parecia o gargalo, quando o cozinheiro estava em 83%. O erro fica documentado no material: instrumento errado produz conclusão errada com números convincentes.

### Mudado
- O inventário de cada praça virou parâmetro do `Restaurant`: agora é o objeto do experimento.

## [aula-04] O salão vivo: a clientela chega sozinha

### Adicionado
- Package `ex4/guests/` com o `Protocol FrontOfHouse` declarado **no consumidor**: o `Restaurant` satisfaz o contrato estruturalmente, sem herdar e sem importar nada da clientela.
- Chegadas de Poisson em duas camadas: gerador síncrono puro para os instantes, async generator para entregar as mesas (consumido com `aclosing`).
- Quatro perfis de cliente, drink como task paralela ao jantar, e desistência na porta via `asyncio.timeout` com a paciência do perfil.
- `Random` por mesa derivado de um mestre, para a aula sair igual independente do escalonamento.

### Não mudado
- O package `restaurant/` — nenhuma linha. Demanda nova não mexe em quem serve, e provar isso É a aula.

## [aula-03] O restaurante completo (determinístico)

### Adicionado
- Package `ex3/restaurant/` com seis subpackages: `core` (erros, relógio), `menu` (cursos, receitas, cardápio de 14 itens), `orders` (comanda, validador), `service` (praça, preparador, expediter), `dining` (mesas, garçons) e `observability` (eventos, diário, métricas).
- Bar como praça independente: fila, estações e brigada próprias — o drink chega no meio da espera sem nenhum `if course == DRINK`.
- Expediter com EDF: chave `(deadline, course, index, sequence)`, starvation-free por construção.
- Validador de fronteira com regras injetadas, cada uma escolhendo a própria consequência.
- `Queue.shutdown()` (3.13) fechando a brigada sem um único `cancel()`.

### Decidido
- A **sequência** dos cursos mora na mesa (`await` é a máquina de estados); a **ordem entre mesas** mora no expediter; o **invariante** mora no validador. Sem gate no orquestrador.

## [aula-02] A cozinha em POO, e onde o `yield` ganha o lugar dele

### Adicionado
- `ex2.py`: organograma de responsabilidades (política × mecanismo × ciclo de vida × observabilidade), receita como `Iterator[Step]`, `yield from` para guarnição reaproveitada, `@asynccontextmanager` liberando estação sob cancelamento, e a armadilha "gerador é consumido uma vez só" demonstrada ao vivo.

### Mudado
- O `usa_fritadeira: bool` + ternário com `nullcontext` saiu: era política vazando para o mecanismo. A estação virou dado do passo, e o recurso passou a ser ocupado por etapa em vez de pelo prato inteiro.

## [aula-01] Fundamentos: a espera é aproveitável

### Adicionado
- `ex1.py`: três cenas rodáveis — a espera aproveitada (1.8s → 1.2s), `gather` × `TaskGroup` com o prato órfão, e a brigada (fila + N cozinheiros + semáforo + timeout).
- Rodapé com as quatro lições: `get()` fora do `try`, `CancelledError` é `BaseException`, `maxsize` como backpressure, e por que `timeout` existe.


## Aula 06 — Evoluir com segurança

Migração de ex5 para src/mise_en_place; snapshots anteriores preservados nas tags; quatro testes de caracterização. Plano atualizado com Cities: Skylines II como referência de pesquisa.


## Aula 07 — Relatório sem intimidade

Papel explícito dos preparadores e fotografia Measurement; relatório deixa de inspecionar workers. Seis testes passando.


## Aula 08 — Cenários como dados

Pydantic valida o documento inteiro antes da execução; entrada JSON com exemplo e testes de capacidades e inventário.


## Aula 09 — Montar e operar

Composition root extraído para bootstrap; operação recebe colaboradores. Os 13 testes anteriores continuam passando.


## Aula 10 — Várias saídas

Adaptadores em memória e JSONL; testes de ordem e falha explícita no fan-out. Quinze testes passando.


## Aula 11 — Executar um turno

Caso de uso independente da CLI, fontes de demanda roteirizada e populacional, apresentação extraída. Dezessete testes passando.


## Aula 12 — Portas e adaptadores

Contratos explícitos e scaffold de demanda para futura IA; Cities: Skylines II registrado como inspiração, sem alegar implementação. Dezoito testes e pyright passando.


## Aula 13 — Invariantes

Duração como valor e proteção da comanda independentemente da entrada. Vinte e três testes e pyright passando.


## Aula 14 — Políticas de atendimento

EDF e FIFO selecionáveis por cenário; teste da fila real e desempate estável. Vinte e cinco testes e pyright passando.


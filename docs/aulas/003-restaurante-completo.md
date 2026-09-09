# Aula 3 — O restaurante completo (determinístico)

`python3 -m ex3` · tag `aula-03`

## A premissa que muda

Na aula 2 a unidade de trabalho era o **pedido**. Agora é a **comanda da mesa**, que tem
cursos com dependência temporal entre si — a entrada sai primeiro, o principal só depois
que a mesa comeu — enquanto os drinks correm por fora.

## Quem manda em quê (a decisão estruturante)

| Quem | Manda em | Não sabe |
|---|---|---|
| **a mesa** (coroutine) | a **sequência** dos cursos | como se cozinha |
| **`Expediter`** | a **ordem entre mesas** (EDF) | o que é curso |
| **`Validator`** | o **invariante** de fronteira | escalonamento |

`await` **é** a máquina de estados da mesa: o estado mora no program counter, e a
sequência se lê de cima para baixo. Se ela vazasse para o expediter (um
`if course == MAIN` no despacho), a cozinha passaria a conhecer política de salão.

## A árvore

```
ex3/restaurant/
├── core/         errors.py, clock.py          — vocabulário comum
├── menu/         courses.py, recipe.py, catalog.py  — POLÍTICA
├── orders/       ticket.py, validator.py      — a fronteira
├── service/      line.py, preparer.py, expediter.py — MECANISMO
├── dining/       seating.py, waiter.py        — salão
├── observability/ events.py, journal.py, metrics.py
└── restaurant.py                              — composition root
```

## O que a aula prova rodando

- **A entrada sai primeiro e a cozinha não para**: a mesa come enquanto os outros pratos
  seguem sendo produzidos.
- **O drink chega no meio da espera** — e não existe `if course == DRINK` em lugar
  nenhum: o bar é outra `Line`, com fila, estações e brigada próprias.
- **A fronteira recusa e explica**: "não servimos polenta frita", "chopp é drink",
  "chamou o garçom e não pediu nada".
- **Recurso ocupado por etapa**, não pelo prato inteiro.

Saída medida: `drink 5.5min · entrada 5.8min · principal 30.7min` — contra uma promessa
de 20min no principal. O restaurante já falha, e isso é o gancho da aula 5.

## Peças de concorrência e o porquê de cada escolha

- **Fila central priorizada + estação como `Semaphore`** (e não uma fila por estação):
  *o prato é a unidade de trabalho; a estação é recurso, não fila.* Prioridade só
  significa algo se existir **uma** fila. Trade-off: perde-se batching por estação.
- **EDF** com chave `(deadline, course, index, sequence)`. Prazo absoluto e estático ⇒
  starvation-free por construção. `sequence` não é enfeite: sem desempate único o heap
  compara o payload e estoura `TypeError` no segundo `put`.
- **`TaskGroup` por rodada** (e não `Barrier`): a rodada sai junta, e se um item queima
  de vez os irmãos são cancelados. `Barrier` sozinho *deadlocka em silêncio* se uma parte
  for cancelada antes de chegar nele.
- **`Queue.shutdown()`** (3.13) fecha a brigada sem um único `cancel()`.
- **Um passo ocupa uma estação** ⇒ deadlock impossível por construção.

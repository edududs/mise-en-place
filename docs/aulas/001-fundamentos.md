# Aula 1 — Fundamentos: a espera é aproveitável

`python3 ex1.py` · tag `aula-01`

## A ideia central

Async **não deixa nada mais rápido**. Ele deixa o *tempo de espera* aproveitável. Um
cozinheiro que fica olhando a água ferver para a cozinha; o mesmo cozinheiro que põe a
água no fogo e vai cortar cebola faz três vezes mais pratos — mesma mão, mesma
velocidade. E se o trabalho for *sovar 10kg de massa*, não existe "enquanto isso": não é
espera, é esforço, e aí async não ajuda em nada.

**A régua**: async serve para espera (I/O), não para esforço (CPU).

## As três cenas

1. **A espera aproveitada** — sequencial 1.8s → concorrente 1.2s. Trocar
   `await asyncio.sleep` por `time.sleep` desfaz o ganho: é o cozinheiro parado olhando
   a panela, e é a diferença entre as duas linhas.
2. **`gather` × `TaskGroup`** — um prato queima aos 0.2s. Com `gather`, a guarnição fica
   pronta **depois** do erro: ninguém a cancelou, é um prato órfão esfriando na bancada.
   Com `TaskGroup`, ela é descartada junto. Mostra `except*` e `ExceptionGroup`.
3. **A brigada** — `Queue` + 4 cozinheiros + `Semaphore` + `timeout` + fim de turno.

## As quatro lições do rodapé

1. `await queue.get()` fica **fora** do `try` — senão o `finally` chama `task_done()`
   para um pedido que nunca existiu.
2. `except Exception` não engole cancelamento: `CancelledError` herda de `BaseException`.
   "Fim do turno" não é "prato queimado".
3. `Queue(maxsize=...)` é a linha mais importante do arquivo. Fila infinita não quebra —
   ela **mente**: aceita 300 pedidos e todo mundo come frio.
4. `timeout` existe para que um prato travado não vire um cozinheiro travado.

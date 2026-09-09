# Changelog

Uma entrada por aula. Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/);
cada aula tem uma tag `aula-NN` apontando para o commit correspondente.

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


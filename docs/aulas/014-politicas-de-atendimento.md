# Aula 14 — Trocar a política, preservar a execução

## O pedido

Queremos comparar ordem de chegada e prazo prometido. A chave EDF estava embutida
no objeto da fila. Copiar o worker para cada estratégia duplicaria execução, recursos
e encerramento, embora apenas a ordem varie.

## Passo a passo

1. Declare `SchedulingPolicy.key(item, deadline, sequence)`.
2. Extraia a chave atual para `EarliestDeadline` e acrescente `FirstInFirstOut`.
3. Guarde a chave no `Dispatch`; payload não participa da comparação.
4. Selecione a política na montagem, inclusive por configuração JSON.

```bash
uv run pytest tests/test_scheduling.py
uv run python -m mise_en_place --config examples/scheduling.json
git diff aula-13 aula-14 -- src
```

## Experimente

Enfileire três pratos com prazos 20, 10, 10. EDF devolve 2, 3, 1; FIFO devolve 1, 2, 3.
A sequência única desempata sem comparar Futures. Observe o experimento completo,
mas não conclua superioridade universal por uma execução ou pela média apenas.

## O nome e o custo

Strategy separa a regra variável do mecanismo. As chaves são calculadas na entrada;
aging exigiria reordenar prioridades e não cabe neste contrato estático. EDF favorece
prazos próximos, mas não cria capacidade nem garante ausência universal de starvation
sem hipóteses sobre chegadas. O mesmo cozinheiro executa ambas as políticas.

Conclusão: mudar `scheduling` altera a ordem da fila sem modificar `Preparer`.

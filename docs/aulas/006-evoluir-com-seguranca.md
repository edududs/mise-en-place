# Aula 6 — Evoluir sem perder o que funciona

## O pedido

Precisamos continuar a aula 5 sem carregar três cópias do restaurante. Corrigir uma
delas não corrige as outras. Antes de mudar responsabilidades, protegemos os efeitos
observáveis: servir uma rodada, recusar entrada inválida, ordenar a fila e fechar workers.

## A menor mudança

`ex5/` passa a `src/mise_en_place/`, instalado como package pelo `uv sync`. As aulas
3–5 continuam completas nas tags antigas. `ex1.py` e `ex2.py` permanecem como introdução.
O teste usa relógio com escala zero apenas para exercitar o protocolo; isso não é um
simulador de tempo virtual e não serve para comparar desempenho.

## Execute e leia

```bash
uv sync
uv run python -m mise_en_place
uv run pytest tests/test_characterization.py
git diff aula-05 aula-06 --stat
git worktree add ../curso-aula-05 aula-05
```

Leia `tests/test_characterization.py`, depois `src/mise_en_place/restaurant/restaurant.py`.
O timeout externo detecta encerramentos travados. Não exigimos números idênticos aos
da tabela antiga: sementes não controlam o escalonador do sistema operacional.

## Experimento e critério de conclusão

Remova temporariamente `line.complete()` do teste de fila e observe que `drain` depende
da confirmação dos itens; interrompa a execução e restaure. Em código real, mantenha
um timeout externo nesse experimento. Faça o teste de casa fechada falhar removendo a
guard clause, depois restaure-a. A aula termina com a suíte verde e as tags antigas intactas.

## O nome e o custo

Testes de caracterização protegem o comportamento conhecido, inclusive limitações.
Não provam que toda regra existente está correta. A migração de layout é separada das
refatorações seguintes para que cada diff tenha uma causa compreensível.

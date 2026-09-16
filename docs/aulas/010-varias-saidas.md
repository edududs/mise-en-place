# Aula 10 — A mesma noite, várias saídas

## O pedido

Queremos capturar eventos para testes e exportá-los para análise, mantendo a narrativa
do terminal. `Journal` e `CompositeJournal` já existem: a necessidade pede explorar
essa boa fronteira, sem redesenhar a cozinha.

## Passo a passo

1. Leia o contrato `Journal.record(Event)` e o fan-out de `CompositeJournal`.
2. Implemente `MemoryJournal`, que devolve uma fotografia dos eventos capturados.
3. Implemente `JsonLinesJournal`, que traduz cada evento para uma linha JSON.
4. Execute o mesmo fluxo nos dois. Nenhum precisa herdar de `Journal`.

```bash
uv run pytest tests/test_journals.py
git diff aula-09 aula-10 -- src tests
```

Para usar na montagem: abra um arquivo UTF-8 com `with`, crie
`JsonLinesJournal(stream)` e passe em `build_restaurant(..., journal=...)`. O stream
deve permanecer aberto durante todo o `async with house`. O adaptador não o fecha.

## Experimente

Inverta a ordem dos consumidores no teste de stream fechado. Agora a memória recebe
o evento antes da falha. Isso mostra que a entrega é ordenada e fail-fast, sem rollback.
Conclusão: dois destinos recebem os mesmos eventos e a política de falha é explícita.

## O custo

O contrato síncrono é suficiente para streams pequenos. Disco lento pode bloquear o
event loop; produção em alto volume pediria buffer/worker, limite de fila e política
de perda ou backpressure. Essa seria outra aula. Não chamar este exportador de
mensageria confiável ou entrega exatamente uma vez.

# Changelog

Uma entrada por aula. Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/);
cada aula tem uma tag `aula-NN` apontando para o commit correspondente.

## [aula-01] Fundamentos: a espera é aproveitável

### Adicionado
- `ex1.py`: três cenas rodáveis — a espera aproveitada (1.8s → 1.2s), `gather` × `TaskGroup` com o prato órfão, e a brigada (fila + N cozinheiros + semáforo + timeout).
- Rodapé com as quatro lições: `get()` fora do `try`, `CancelledError` é `BaseException`, `maxsize` como backpressure, e por que `timeout` existe.


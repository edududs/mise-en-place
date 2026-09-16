# Aula 11 — Quem comanda o turno?

## O pedido

Um teste e um script querem executar a noite sem importar parsing de argumentos nem
imprimir tabelas. A função `measure` do executável mistura montagem e coordenação.

## Passo a passo

1. Extraia `application/run_shift.py`: pedido `RunShift`, porta `DemandSource` e função
   `execute`. A função abre, executa demanda, fecha e entrega `Measurement`.
2. Encapsule a clientela existente em `PopulationDemand`.
3. Crie `ScriptedDemand` com pedidos finitos para testar o mesmo fluxo.
4. Mova a apresentação para `adapters/report.py`; CLI continua montando as peças.

```bash
uv run pytest tests/test_run_shift.py
uv run python -m mise_en_place --config examples/scenarios.json
git diff aula-10 aula-11 -- src tests
```

## Experimente

Use um roteiro vazio: a casa abre, fecha e entrega zero rodadas. Use rodada vazia:
ela deve ser recusada, e a casa deve fechar mesmo com falha. Leia a diferença entre
fim normal (drenar) e exceção (cancelamento estruturado) no runtime.

## Padrão e limite

O caso de uso é uma função assíncrona. `RunShift` é um pedido, não estado da sessão.
`ScriptedDemand` exerce pedidos diretamente: não representa ocupação e consumo de uma
mesa. A fonte precisa terminar os clientes iniciados antes de retornar. Esta primeira
extração ainda tipa a casa concreta; a próxima aula revisa a fronteira.

Conclusão: a suíte executa o restaurante completo sem CLI, arquivo ou saída no terminal.

# Aula 16 — Uma ocorrência, vários interessados

## O pedido

O jogo quer uma meta de rodadas servidas. Colocar `if meta...` na cozinha acoplaria a
operação à progressão. Ler o texto do log seria frágil: apresentação pode mudar.

## Passo a passo

1. Declare `RoundServed`, com mesa, curso, quantidade e instante.
2. A operação publica o fato depois da entrega. `RoundPublisher` é sua porta de saída.
3. `RoundDispatcher` chama uma lista explícita de consumidores, em ordem.
4. `game.ServiceGoal` reage ao fato. A montagem conecta sua função ao dispatcher;
   o restaurante não importa o jogo. Telemetria mantém seu contrato existente.

```bash
uv run pytest tests/test_domain_events.py
git diff aula-15 aula-16 -- src tests
```

## Experimente

Mude a meta no teste de uma para duas rodadas: o prato continua servido, mas a meta
não é atingida. Coloque um consumidor que falha entre dois outros e observe que só
o primeiro recebe o fato. Nenhum efeito anterior é revertido.

## O nome e o limite

Evento de domínio representa um fato relevante para outras regras. Log é uma projeção
para observação. O dispatcher local é síncrono e fail-fast: se falhar, o pedido já foi
servido e não deve ser reexecutado cegamente. Não há entrega durável, deduplicação,
outbox ou transação. Isso seria necessário antes de distribuir os consumidores.

Conclusão: uma regra nova do jogo reage à operação sem entrar no worker ou no escalonador.

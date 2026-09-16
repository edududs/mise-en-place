# Aula 12 — Reconhecer a arquitetura que surgiu

## O pedido

A aplicação ainda importa `Restaurant`, e a porta da clientela importa `Clock`
concreto. Uma futura IA deveria conversar com atendimento sem conhecer a cozinha.

## Passo a passo

1. Reúna apenas o vocabulário que realmente cruza fronteiras em `contracts/`:
   pedido bruto, mesa, enums e resultado. Módulos antigos reexportam os mesmos tipos.
2. Expresse `WaitingClock`, `FrontOfHouse`, `ShiftOperation` e `DemandSource`.
3. Faça `execute` depender do contrato de operação, não de `Restaurant`.
4. Acrescente `ai/PlannedDemand`: recebe um planejador que emite intenções. O mesmo
   caso de uso integra essa fonte sem saber que se trata de IA.

```bash
uv run pytest tests/test_ai_scaffold.py tests/test_run_shift.py
uv run pyright src tests
git diff aula-11 aula-12 -- src
```

Fluxo: CLI → composição → caso de uso → porta de operação → restaurante.
Fonte de demanda → porta de atendimento → restaurante. Eventos → observadores.
Essas setas descrevem chamadas; imports apontam para os contratos compartilhados.

## Experimente

Substitua o planejador fixo por outro que devolva duas rodadas. Não modifique
`Restaurant`, `Preparer` nem `execute`. Envie item inexistente e observe que a operação
continua validando: uma intenção da IA não é uma ordem já autorizada.

## Referência e limite

Cities: Skylines II é referência para estudar agentes, demanda e computação da
simulação. Aqui há somente scaffold, sem reproduzir algoritmos internos do jogo.
Um plano finito ainda não é IA reativa: percepção, feedback e orçamento por tick
precisarão de contratos futuros. `guests/` mantém a clientela legada; `ai/` já nasce
isolado do runtime. Compartilhar contratos implica coordenar sua evolução.

Portas e adaptadores dão nome ao isolamento demonstrado. DDD e Clean Architecture
não precisam ser adotados integralmente. Conclusão: o scaffold importa só contratos,
e uma intenção percorre a cozinha real no teste de integração.

# Aula 13 — Dados válidos, operação inválida

## O pedido

Outra entrada consegue construir tipos internos diretamente. Um `Ticket` com campos
tipados pode conter itens de outro curso, prazo anterior ao pedido ou nenhum item.
Uma receita pode conter duração negativa ou infinita. Pydantic na configuração não
protege esses caminhos.

## Passo a passo

1. Introduza `Duration`, com unidade explícita, igualdade por valor e validação de
   finitude e sinal. `Recipe.duration()` oferece esse tipo sem quebrar a API anterior.
2. Proteja a construção de `Step` e `Ticket`. O agregado mínimo da rodada não pode
   misturar mesa ou curso; validação do cardápio continua no `Validator`.
3. Recuse abertura duplicada do turno, preservando o dono das tasks existentes.
4. Teste o domínio diretamente, sem JSON ou Pydantic.

```bash
uv run pytest tests/test_invariants.py
git diff aula-12 aula-13 -- src tests
```

## Experimente

Use `dataclasses.replace` numa comanda válida e altere só seu curso. Cada campo tem
tipo correto, mas a combinação é inválida. Observe a recusa. Faça o mesmo com prazo
anterior ao início. Compare `Duration(5) == Duration(5)` com identidade de uma mesa.

## O nome e o custo

Objeto de valor reúne unidade e invariantes; não exige herdar de BaseModel. A comanda
protege suas relações internas. Não criamos um agregado do restaurante inteiro.
O valor numérico ainda aparece na API legada: uma migração completa de unidades é
outra decisão, não requisito para demonstrar a proteção.

Conclusão: construir uma comanda por outra entrada não permite burlar essas regras.
Verificação de existência no cardápio continua sendo trabalho da fronteira de pedidos.

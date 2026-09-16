# Aula 9 — Montar e operar mudam por motivos diferentes

## O pedido

Queremos montar várias equipes e observar seus turnos. O construtor de `Restaurant`
escolhe terminal, inventário, equipe e métricas, além de a classe executar atendimento.
Testar uma montagem alternativa exige conhecer essa escolha embutida.

## Passo a passo

1. Extraia os dados iniciais para `restaurant/layout.py`.
2. Mova a criação dos colaboradores para `bootstrap.build_restaurant`.
3. Faça `Restaurant` receber as peças. Seus métodos de atendimento não mudam.
4. Atualize os chamadores e execute os mesmos testes de caracterização.

```bash
uv run pytest tests/test_characterization.py tests/test_results.py
uv run python -m mise_en_place --config examples/scenarios.json
git diff aula-08 aula-09 -- src
```

## Experimente

Monte uma casa com um cozinheiro e outra com seis pela função de montagem. Compare
o relatório. Em seguida procure `TerminalJournal` em `restaurant/restaurant.py`: a
operação não deve mais escolher essa implementação.

## O nome e o limite

Composition root é o lugar onde dependências concretas se encontram. Injeção é
passá-las explicitamente; não exige container. O construtor da operação ainda conhece
colaboradores internos concretos que não precisam variar: interface por classe seria
trabalho sem evidência. O número de argumentos na montagem é uma escolha documentada,
não motivo para esconder tudo num dicionário sem tipo.

Conclusão: mudanças de equipe e destino de observação ficam na montagem, enquanto os
testes de pedido servido e fechamento continuam verdes.

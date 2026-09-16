# Aula 8 — Cenários querem sair do código

## O pedido

Outra pessoa quer comparar equipes sem editar Python. Um arquivo com `cooks: 0`
poderia criar trabalho sem consumidor; uma estação faltando falharia no meio do turno.
Precisamos recusar esses cenários antes de criar tasks.

## Passo a passo

1. Extraia `Scenario` para um módulo independente do ponto de entrada.
2. Modele a entrada em `configuration.py`: capacidades inteiras positivas, nome e
   inventário compatível com o cardápio. Campos desconhecidos são erros de digitação.
3. Valide o documento completo e traduza para `Scenario`. O restante da operação
   continua recebendo Python comum.
4. Acrescente `--config` ao executável existente.

```bash
uv sync
uv run python -m mise_en_place --config examples/scenarios.json
uv run pytest tests/test_configuration.py
git diff aula-07 aula-08 -- src examples tests
```

## Experimente

Copie o JSON e troque `cooks` por `cook`, depois use zero e finalmente `"3"`.
Observe três erros úteis antes da abertura. Restaure um inteiro positivo. Retire uma
estação de um inventário explícito: validar cada campo não substitui validar relações.

## Padrão, custo e conclusão

É validação de fronteira, seguida de tradução. Pydantic é dependência de runtime pela
primeira vez. `frozen=True` não congela profundamente o dicionário; fazemos cópia na
tradução para não compartilhar o inventário com o modelo de entrada. Regras internas
continuam precisando de proteção quando o domínio é chamado por outra entrada.
Conclusão: todos os cenários são validados antes da primeira noite começar.

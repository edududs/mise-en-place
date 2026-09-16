# mise-en-place

Um curso de engenharia de software em Python que evolui uma cozinha de restaurante
até um simulador/jogo no terminal. Cada técnica entra quando uma necessidade concreta
justifica seu custo. Código em inglês; narrativa e comentários em português.

O norte está em [CURSO.md](CURSO.md). A [trilha de arquitetura pela necessidade](docs/TRILHA-ARQUITETURA.md)
continua as cinco aulas iniciais com **12 aulas implementadas, de 6 a 17**.

## Começar

Python 3.13+ e `uv`:

```bash
uv sync --locked
uv run python -m mise_en_place.demo
uv run python -m mise_en_place --config examples/scenarios.json
uv run python -m mise_en_place --config examples/scheduling.json --results-dir results
uv run python -m mise_en_place --results-dir results --show scenario-1
```

A demo finita liga um planejador simples, a cozinha real, uma meta de jogo, eventos CSV
e armazenamento em memória. O executável principal mantém a clientela da aula 5; sem
`--config`, compara os seis cenários originais. IDs `scenario-1`, `scenario-2` etc.
são substituídos em novas execuções no mesmo diretório.

Os cenários compartilham sementes, mas tempos e escalonamento podem variar. A saída
da CLI usa UTF-8, inclusive quando redirecionada no Windows.

## Aulas

| Aula | Leitura |
|---|---|
| 01 | [Fundamentos](docs/aulas/001-fundamentos.md) |
| 02 | [POO e geradores](docs/aulas/002-poo-e-geradores.md) |
| 03 | [Restaurante completo](docs/aulas/003-restaurante-completo.md) |
| 04 | [Salão vivo](docs/aulas/004-salao-vivo.md) |
| 05 | [Medir antes de otimizar](docs/aulas/005-medir-antes-de-otimizar.md) |
| 06 | [Evoluir com segurança](docs/aulas/006-evoluir-com-seguranca.md) |
| 07 | [Relatório sem intimidade](docs/aulas/007-relatorio-sem-intimidade.md) |
| 08 | [Cenários como dados — Pydantic](docs/aulas/008-cenarios-como-dados.md) |
| 09 | [Montar e operar](docs/aulas/009-montar-e-operar.md) |
| 10 | [Várias saídas](docs/aulas/010-varias-saidas.md) |
| 11 | [Executar um turno](docs/aulas/011-executar-um-turno.md) |
| 12 | [Portas e adaptadores; scaffold de IA](docs/aulas/012-portas-e-adaptadores.md) |
| 13 | [Invariantes](docs/aulas/013-invariantes.md) |
| 14 | [Políticas de atendimento](docs/aulas/014-politicas-de-atendimento.md) |
| 15 | [Guardar resultados](docs/aulas/015-guardar-resultados.md) |
| 16 | [Fatos e reações](docs/aulas/016-fatos-e-reacoes.md) |
| 17 | [Provar intercâmbio](docs/aulas/017-provar-intercambio.md) |

## Estudar a evolução

Uma aula é um commit, uma tag e uma página. O snapshot contém o sistema inteiro.

```bash
git worktree add ../curso-aula-08 aula-08
git diff aula-07 aula-08 -- src tests
```

Execute `uv sync --locked` dentro do worktree escolhido. Aulas 3–5 rodam com
`python -m exN` em suas tags; a partir da 6, com `python -m mise_en_place`.
Documentação acumula; código evolui em `src/mise_en_place`.

## Verificar

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run pyright
uv run mypy --strict -p mise_en_place
uv run mypy --strict ex1.py ex2.py
```

Os testes cobrem operação, configuração, políticas, contratos, falhas/cancelamento,
dependências arquiteturais e combinações de adaptadores. Escala zero verifica
integração rápida, não simulação determinística de tempo.

## Próximas pesquisas

**Cities: Skylines II** entra como referência para demanda, agentes e custo de simulação.
Ver [escopo da pesquisa](docs/specs/ia-demanda-simulacao.md). O contexto `ai/` tem
somente scaffold de planejamento finito; IA reativa, pathfinding, orçamento por tick
e tempo virtual ainda não estão implementados.

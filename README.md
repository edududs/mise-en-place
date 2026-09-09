# mise-en-place

> *Mise en place*: na cozinha, é ter tudo preparado e **cada coisa no seu lugar** antes
> do serviço começar. É também, literalmente, o princípio de arquitetura deste projeto.

Um curso de engenharia de software em Python construído sobre uma analogia só — uma
cozinha de restaurante — que vai de `async def` até um simulador/jogo de administração
de cozinha no terminal. Concorrência, arquitetura hexagonal, DDD, event-driven,
observabilidade, testes de propriedade e Pydantic entram **quando o simulador precisa
deles**, não antes.

O documento que manda é [`CURSO.md`](CURSO.md): o norte, as caixas que precisam ficar
isoladas, as trilhas de assunto e as decisões já tomadas (com o *porquê* de cada uma).

## Rodando

```bash
uv sync                    # ambiente
python3 ex1.py             # aula 1 — fundamentos
python3 ex2.py             # aula 2 — POO + geradores
python3 -m ex3             # aula 3 — o restaurante completo, determinístico
python3 -m ex4             # aula 4 — o salão vivo (a clientela chega sozinha)
python3 -m ex5             # aula 5 — medir antes de otimizar
```

## Como o curso é versionado

Cada aula é **o todo naquele ponto da evolução**, não um trecho. Uma aula = um commit +
uma tag + uma entrada no [`CHANGELOG.md`](CHANGELOG.md) + uma página em
[`docs/aulas/`](docs/aulas).

```bash
git checkout aula-04                      # o mundo inteiro como estava na aula 4
git diff aula-03 aula-04                  # A AULA é o diff
git worktree add ../aula-03 aula-03       # duas aulas lado a lado, sem cópia manual
```

O princípio: **doc acumula, código evolui.** A narrativa de toda aula fica em `main`
para sempre; o código daquela aula vive na tag.

## Convenções

- **Código em inglês; comentários, docstrings e narrativa em pt-BR.** A fronteira é
  explícita: em `StrEnum` o *identificador* é código (`Station.COLD_LINE`) e o *value*
  é rótulo (`"bancada fria"`); em `IntEnum` — onde o valor já é a ordem — existe um mapa
  de rótulos (`COURSE_LABELS`).
- `from __future__ import annotations`, tipagem em tudo, `X | None`.
- Zero magic number: constante `Final` nomeada ou `Enum`. (Exceção registrada: dentro de
  literal de `dataclass` congelada, o nome do campo já nomeia o número.)
- Guard clauses, SRP, sem God Object, sem primitive obsession.
- **O código é a aula**: comentário explica o *porquê*, e cada arquivo fecha com um
  bloco de lições.

## Qualidade

```bash
uvx ruff format . && uvx ruff check .     # select = ["ALL"], ignores por nome de regra
uvx mypy --strict ex1.py ex2.py
uvx mypy --strict -p ex3                  # (um alvo por vez)
uv run pyright                            # typeCheckingMode = "strict"
```

Os dois checadores rodam de propósito: quando `mypy` e `pyright` discordam, a
discordância é matéria.

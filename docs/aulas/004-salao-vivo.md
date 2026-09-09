# Aula 4 — O salão vivo: a clientela chega sozinha

`python3 -m ex4` · tag `aula-04`

É a aula 3 **inteira, sem uma linha alterada**, mais o package `guests/`. Esse é o
resultado que a aula quer provar: demanda nova não mexe no restaurante.

## O ponto que vale a aula inteira

O `Protocol FrontOfHouse` está declarado **dentro de `guests/`** — no package de quem
CONSOME, não no de quem serve. Isso inverte a seta de dependência (DIP): a clientela não
depende de uma implementação, ela **declara o que precisa**.

E porque `Protocol` é estrutural, o `Restaurant` satisfaz o contrato **sem herdar de
nada e sem importar aquele arquivo** — ele nem sabe que a clientela existe. A costura é
conferida pelo type checker, numa função de uma linha:

```python
def confirm_port(house: Restaurant) -> FrontOfHouse:
    """Se as assinaturas divergirem, o erro aparece AQUI — no único ponto
    em que porta e adaptador se encontram."""
    return house
```

Hexagonal de graça: porta declarada pelo consumidor, adaptador conferido estaticamente,
zero framework.

## Acréscimos

- **Chegadas de Poisson** — um gerador síncrono e puro produz os instantes
  (`arrival_times`, testável sem event loop); um async generator dorme até cada um e
  entrega a mesa (`party_stream`), consumido com `contextlib.aclosing`. Intervalo
  uniforme esconderia a **rajada**, e é a rajada que satura o garçom.
- **4 perfis** (com pressa, casal, família, amigos) com paciência na porta, tempo de
  leitura de menu, tempo de comer por curso e rodadas de bebida.
- **Drink é task paralela**, não estado da mesa: corre ao lado da refeição inteira e é
  cancelado quando a comida acaba.
- **Desistência na porta** via `asyncio.timeout` com a paciência do perfil. A paciência é
  política do cliente (vem por parâmetro); aplicar o prazo e registrar é mecanismo da
  casa. `Seating.seat` segue sem saber o que é paciência.
- **`Random` por mesa, derivado de um mestre**: com asyncio o entrelaçamento varia entre
  máquinas, e num gerador compartilhado a aula sairia diferente a cada execução.

## Lição de tipagem que caiu no colo

`contextlib.aclosing` exige `AsyncGenerator`, não `AsyncIterator`: os dois funcionam em
`async for`, mas só o primeiro declara `aclose()`. Regra: `AsyncGenerator` no **retorno**
de quem produz, `AsyncIterator` no **parâmetro** de quem consome (ISP).

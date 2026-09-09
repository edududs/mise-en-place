# Aula 2 — A cozinha em POO, e onde o `yield` ganha o lugar dele

`python3 ex2.py` · tag `aula-02`

## O organograma

Cada classe é um cargo com **uma** razão para mudar:

| Papel | Classe | Natureza |
|---|---|---|
| menu / etapa / receita | `Dish`, `Station`, `Step`, `Recipe` | **política** |
| ticket do garçom | `Order` | dado de fronteira |
| inventário físico e vagas | `Stations` | recurso escasso |
| operar: puxar, ocupar, cronometrar | `Cook` | **mecanismo** |
| abrir/fechar, escalar a brigada | `Kitchen` | ciclo de vida (`async with`) |
| fechamento do caixa | `Metrics` | observabilidade |

O que ensina mais é o que **não** existe: um `Cook` que soubesse a receita seria God
Object (trocar o menu passaria a mexer em quem opera a cozinha); as estações são do
restaurante, e um `Semaphore` por cozinheiro não limitaria nada.

## O que o `yield` comprou

O `usa_fritadeira: bool` + ternário com `nullcontext` era **política vazando para o
mecanismo** — com cinco estações viraria cinco flags e um `if` crescente. Com a receita
como gerador de passos:

1. `Recipe` virou política **pura e síncrona** — nenhum `await`, testável sem event loop
   (`list(steak_steps())`).
2. A estação virou **dado do passo**. Estação nova não mexe em receita; receita nova não
   mexe no cozinheiro.
3. O recurso é ocupado **por etapa**: o bife solta a chapa quando vai descansar, e outro
   prato entra nela. É aqui que "otimizar dados os recursos" acontece de verdade.
4. `yield from` deu fonte única aos passos: a batata do "bife com fritas" é a do menu.

Mais: `@asynccontextmanager` em `Stations.occupy` (libera a estação mesmo sob
cancelamento), `itertools.count`/`islice` na fonte preguiçosa de pedidos, e a armadilha
"gerador é consumido uma vez só" demonstrada ao vivo no `main`.

## O detalhe que passa batido

`self.delivered += 1` é seguro **sem `Lock`**: o event loop nunca troca de task no meio
de uma linha, só num `await`. Com threads, o mesmo `+= 1` precisaria de mutex. É a
vantagem escondida do async — concorrência sem corrida de dados, desde que você não
bloqueie o expedidor.

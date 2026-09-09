# Aula 5 — Medir antes de otimizar: onde está o gargalo

`python3 -m ex5` · tag `aula-05`

É a aula 4 mais **uma** mudança no package: o inventário de cada praça virou parâmetro,
porque agora ele é o objeto do experimento. A mesma noite (mesma semente, mesmas
chegadas, mesmas escolhas) roda seis vezes, mudando uma coisa por vez.

## A aula é um erro real, mantido de propósito

O relatório da aula 4 media a ocupação das **estações** (forno, chapa, fogão) e não a
dos **cozinheiros**. Com esse instrumento, o forno aparecia como suspeito (40%) e o
experimento apontava para o lugar errado — nenhum cenário resolvia nada.

O cozinheiro fica com o item do início ao fim, **inclusive enquanto espera vaga na
estação**. Instrumentando ele: **83%**.

> **Instrumento errado produz conclusão errada com números convincentes** — e isso é
> pior que não medir.

## A tabela

| cenário | entrada | principal | chef | forno | garçom |
|---|---|---|---|---|---|
| como está | 22.3m | 58.4m | **83%** | 40% | 19% |
| +1 cozinheiro | 19.5m | 49.6m | 80% | 47% | 22% |
| +1 vaga no forno | 25.2m | 52.7m | 83% | 28% | 20% |
| +1 garçom | 25.4m | 54.3m | 84% | 41% | 15% |
| +3 cozinheiros | 11.3m | **30.7m** | 73% | 56% | 26% |
| +3 cozinheiros e +1 forno | 10.6m | **30.3m** | 71% | 40% | 26% |

## As três lições, todas visíveis na tabela

1. **Meça o recurso certo.** Se o que segura o trabalho é a pessoa e você instrumentou a
   máquina, todo o resto da análise é ficção.
2. **O gargalo é um lugar só.** Melhorar qualquer outro ponto muda o número *daquele*
   ponto e não move o resultado (Teoria das Restrições). "+1 garçom" chega a piorar.
3. **Fila satura de forma não-linear.** Perto de 100% de utilização, um pouco de
   capacidade derruba a espera; longe da saturação, a mesma capacidade não compra nada.

## Detalhes de método

- **Utilização = ocupado / (tempo × vagas)**. Sem dividir pelas vagas, dobrar o forno
  "melhoraria" o número sem melhorar nada.
- **Mesma semente em todos os cenários**, senão a comparação é ruído passando por
  resultado.
- **Relógio injetável**: as medições rodam com `minute_s = 0.01` e a noite inteira cabe
  em ~3s, sem tocar uma linha do restaurante.
- **A ferramenta antes da técnica**: `asyncio.run(main(), debug=True)` grita quando algo
  segura o expedidor por mais de 100ms. Rode isso *antes* de otimizar qualquer coisa.

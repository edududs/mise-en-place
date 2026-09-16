# Curso: engenharia de software pela analogia da cozinha

Documento principal, atualizado na aula 17. O alvo continua sendo um simulador/jogo
de operação de restaurante, com horizonte de **150+ aulas**. Cada assunto entra quando
o simulador precisa dele.

## Estado atual e decisões

- Aulas 1–5: concorrência, POO/geradores, restaurante, clientela e medição.
- Aulas 6–17: [arquitetura pela necessidade](docs/TRILHA-ARQUITETURA.md), implementada.
- Código vivo em `src/mise_en_place/`; `ex3`–`ex5` preservados nas tags históricas.
- Cada aula tem página, commit, tag e entrada no changelog. A tag é o snapshot completo.
- Python 3.13+, `uv`, lockfile; desde a aula 8, Pydantic na configuração e nos arquivos
  de resultados. Sem FastAPI, Django, ORM ou container de DI.
- Testes básicos foram antecipados da T7 para proteger as refatorações.
- Eventos locais têm entrega síncrona, ordenada e fail-fast. Não há barramento global.
- Uma instância da operação representa um turno. Nova execução usa nova montagem:
  filas encerradas não reabrem.

O [índice no README](README.md#aulas) reúne as leituras. O [documento original até a
aula 5](docs/history/CURSO-ate-aula-05.md) preserva pesquisas e decisões anteriores,
inclusive contradições históricas. Este arquivo e a trilha atual prevalecem sobre
planos antigos, especialmente layout, idioma, testes e estado de implementação.

## Contrato didático

Necessidade → dificuldade observável → menor alteração útil → evidência → padrão e
seu custo. Toda aula termina com código executável, leitura do diff, exercício e
critério verificável. Código em inglês; comentários e narrativa em pt-BR.

Tipagem estrita, `from __future__ import annotations`, `X | None`, guard clauses e
responsabilidades pequenas. Constantes nomeadas ou campos que expliquem valores.
Comentários explicam decisões. `ruff`, `pyright` e `mypy` verificam o projeto.

Arquitetura não garante aceleração. Avaliamos alcance da mudança, clareza de contratos
e preservação de comportamento. Desempenho exige medição própria.

## Fronteiras do simulador

| Contexto | Responsabilidade | Situação |
|---|---|---|
| Ambiente | Layout, praças e estações | Parcialmente implementado na operação |
| Tempo | Clock, escala e espera | Parede escalada; virtual e pausa futuros |
| Recursos | Insumos, dinheiro e equipamentos | Capacidade de estações; economia futura |
| Pessoas e demanda | Perfis, chegadas e decisões | Clientela + fontes substituíveis; IA scaffold |
| Operação | Pedidos, filas, preparo e entrega | Restaurante executável |
| Jogo | Metas, progressão e comandos | Meta por evento; progressão futura |
| Interface | Entrada, renderização e narrativa | CLI, terminal, JSONL e CSV |
| Persistência | Resultados; depois sessão e replay | Resultados em memória/JSON |

`contracts/` guarda vocabulário compartilhado e interfaces. `application/` coordena;
`bootstrap.py` monta implementações; `adapters/` traduz meios; `restaurant/` executa;
`game/` reage a fatos; `ai/` conhece apenas contratos. Testes verificam imports estáticos.

Novo formato ou fonte de demanda não altera workers. Regra nova do negócio pode
alterar o domínio. Não prometemos que todo conteúdo futuro caberá em dados sem rever
contratos. O objetivo é localizar mudanças e tornar suas consequências explícitas.

## Analogia que orienta as aulas

| Restaurante | Conceito |
|---|---|
| Expedidor | Event loop e coordenação |
| Pedido em andamento | Task |
| Receita | Política e plano de passos |
| Esperar forno | Await sem bloquear o loop |
| Balcão limitado | Queue e backpressure |
| Vagas de estação | Semaphore |
| Rodada entregue junta | TaskGroup |
| Prazo do prato | Timeout e promessa de serviço |
| Escala/equipamentos | Capacity planning |
| Quem chega | Fonte de demanda substituível |
| Quem vê o turno | Adaptador de observação |

## Trilhas restantes

| Trilha | Desenvolvimento previsto |
|---|---|
| T1 Concorrência | Supervisão, shutdown, contenção e políticas avançadas |
| T1.5 Pydantic | Unions discriminadas, configuração composta e custo de validação |
| T2 Python | Typing avançado, geradores, descritores e registros quando necessários |
| T3 Arquitetura | Agregados maiores, transações, CQRS, outbox e eventos duráveis |
| T4 Simulação | Clock virtual, DES, pausa, velocidade, determinismo e replay |
| T5 Recursos | Teoria de filas, capacidade, contratação, estoque e gargalo móvel |
| T6 IA | Percepção, feedback, utility AI/behavior trees e orçamento de decisões |
| T7 Testes | Hypothesis, máquina de estados, fuzz, carga e regressão determinística |
| T8 Observabilidade | Eventos, percentis, tracing, timeline, SLO e custo de observar |
| T8.5 Interface | Rich e, quando necessário, Textual; render separado de estado |
| T9 Jogo | Economia, upgrades, ondas, progressão, save/load e mods |
| T10 Desempenho | Profiling, batching, processos e free-threading quando justificados |

O roteiro original de sete aulas de observabilidade e as doze pesquisas de operação
real estão preservados no documento histórico: são planejamento, não entregas concluídas.

## Referências de jogo

O simulador de sistemas do Lucas Montano inspira regência de parâmetros; Bloons TD
inspira ondas e upgrades. **Cities: Skylines II**, solicitado em 16/09/2026, acrescenta
interesse por agentes, demanda e custo computacional. Não afirmamos que seu código
interno usa nossas técnicas. Ver [pesquisa de IA](docs/specs/ia-demanda-simulacao.md).

## Limites conhecidos

- Sementes não garantem replay idêntico com asyncio e relógio de parede.
- Scaffold de IA produz plano finito; percepção e feedback precisam de contrato futuro.
- Demanda roteirizada aciona rodadas, sem simular a jornada completa da mesa.
- Eventos locais não oferecem idempotência, durabilidade ou rollback.
- Resultados persistidos não são save/load de sessão viva.
- Clientela legada conhece catálogo e tipos do restaurante; a nova IA nasce isolada.
- Exemplos iniciais mantêm escolhas históricas: consultar suas tags para estudar o antes.

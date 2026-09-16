# Pesquisa futura — IA, demanda e custo de simulação

Referência solicitada: **Cities: Skylines II**. Estado: pesquisa pendente; scaffold
de integração implementado na aula 12. Não há afirmações sobre algoritmos internos
do jogo neste documento. Distinguir fonte oficial, comportamento observado e hipótese.

## Perguntas

1. Quais comportamentos emergem de decisões individuais e quais são agregados?
2. Que observações um agente recebe para decidir sem conhecer o runtime?
3. Como demanda, capacidade, espera, preço e desistência se realimentam?
4. Com que frequência recalcular decisões? Como limitar custo por tick?
5. Quais partes exigem agentes individuais e quais aceitam aproximações?
6. Como separar custo de pathfinding, decisão, execução e renderização?
7. Como usar sementes independentes e clock virtual para reprodutibilidade?
8. Como comparar fidelidade da simulação e tempo de CPU por cenário?

## Hipóteses para o restaurante

- Perfis e intenção separados da operação da mesa.
- Ondas versus chegadas contínuas, com igual volume total.
- Menor frequência de decisão, medindo espera e desistência.
- Utility AI e behavior trees comparadas a uma regra simples.
- Percepção por snapshot imutável, sem referências a workers.
- Tempo virtual antes de alegar comparações determinísticas.

Cada hipótese precisa de cenário, métrica de fidelidade, orçamento de CPU e limite
de validade. Não adotar uma técnica só porque é comum em city builders.

## Fronteira preparada

`DemandSource.run(FrontOfHouse)` liga uma fonte ao caso de uso. `ai.PlannedDemand`
traduz um `DemandPlanner` em pedidos. A operação valida e executa; o planejador não
altera filas, estoque ou workers. O teste percorre a operação real.

O contrato inicial é finito e sequencial. IA reativa deverá receber percepção e
orçamento explícitos. Nenhuma biblioteca de IA, LLM ou serviço externo é necessária.

## Critério de conclusão da pesquisa

Registrar fontes primárias com datas, distinguir documentação de inferência e
construir um experimento mínimo comparável. Só então propor aulas novas.

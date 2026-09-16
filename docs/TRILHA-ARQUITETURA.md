# Arquitetura pela necessidade — aulas 6 a 17

Proposta aprovada em 16/09/2026. Esta trilha continua o restaurante da aula 5:
preserva sua operação enquanto torna configuração, montagem, execução e observação
mais fáceis de evoluir. Não usa FastAPI, Django, ORM ou container de DI.

## Contrato pedagógico

Cada aula apresenta um pedido novo, localiza a dificuldade no código existente,
faz a menor alteração útil, demonstra o comportamento e só então nomeia o padrão.
O aluno deve comparar o diff entre tags e responder: quais peças precisaram mudar?
Toda página contém execução, leitura guiada, exercício e critério de conclusão.
Cada aula tem commit e tag próprios. Documentação acumula; implementação evolui.

Testes básicos são antecipados da T7: fornecem evidência de preservação durante as
refatorações. Não se promete igualdade exata de tempos de parede: mesma semente não
torna o escalonamento do asyncio determinístico. Usamos invariantes, cenários finitos
e testes de contrato. Clock virtual e replay determinístico continuam na T4.

## Sequência

| Aula | Necessidade | Mudança | Evidência |
|---|---|---|---|
| 06 | Evoluir uma implementação sem perder aulas antigas | `ex5` → `src/mise_en_place`, testes de caracterização | Pedido servido, recusa e encerramento preservados; tags antigas intactas |
| 07 | Relatório depende da organização e do nome de funcionários | Resultado estruturado; papel explícito | Renomear cozinheiro não muda sua classificação |
| 08 | Cenários exigem editar Python | JSON + Pydantic na borda | Configuração inválida falha antes de iniciar tasks |
| 09 | Montagem e operação mudam por motivos diferentes | Composition root fora de Restaurant | Variação de equipe sem mudar atendimento |
| 10 | Precisamos observar a mesma noite de maneiras diferentes | Adaptadores terminal, memória e JSONL | Mesmo contrato, mesmos eventos; erros explícitos |
| 11 | Script, CLI e teste querem executar um turno | Caso de uso com pedido e resultado | As entradas acionam o mesmo fluxo |
| 12 | Interfaces ainda deixam detalhes atravessarem fronteiras | Revisão de contratos e dependências | Teste aciona aplicação sem terminal ou filesystem |
| 13 | Campos válidos não garantem operação válida | Objetos de valor e invariantes | Violação recusada mesmo sem Pydantic |
| 14 | Precisamos comparar FIFO e EDF | Política de ordenação injetada | Fila real obedece ambas; desempate estável |
| 15 | Resultado desaparece ao terminar o processo | Porta de armazenamento: memória e JSON | Round-trip, ausência e corrupção verificáveis |
| 16 | Um fato interessa a diferentes consumidores | Evento de domínio + despacho explícito | Meta reage a rodada servida; telemetria continua separada |
| 17 | Precisamos provar intercâmbio e isolamento | Novo adaptador e testes arquiteturais | Mesmos contratos, combinações reais, import proibido detectado |

## Limites e decisões

- Pydantic começa nos arquivos de entrada e persistência. Domínio usa Python e
  dataclasses; isso é uma escolha didática, não proibição universal de bibliotecas.
- Protocol descreve forma. Testes de contrato verificam semântica: resultados, erros,
  ordem e efeitos. A troca só é transparente enquanto esse contrato for respeitado.
- Portas aparecem onde existe variação ou necessidade de isolamento demonstrável.
  Não se cria uma interface por classe, nem se copia uma árvore de pastas ideal.
- A aula 15 guarda **resultados concluídos**, não Futures, semáforos ou tasks. Save/load
  de uma sessão viva exige outra modelagem e pertence à trilha de simulação.
- A aula 16 usa entrega síncrona em processo, ordenada e fail-fast. Não promete
  transação, entrega exatamente uma vez, replay ou mensageria distribuída.
- Política de ordenação não elimina sobrecarga. EDF não promete prazos cumpridos ou
  ausência universal de starvation sem hipóteses sobre chegadas e prazos.
- Nova regra de negócio pode exigir mudar o domínio. O objetivo é localizar mudança,
  não declarar o núcleo eternamente fechado a qualquer evolução.

## Leitura crítica das pesquisas fornecidas

Os arquivos hexagonal1–4 motivam portas, adapters, casos de uso e objetos de valor.
Adaptamos as ideias ao restaurante sem transportar os exemplos HTTP/ORM. Hexagonal,
Clean Architecture e DDD são abordagens relacionadas com objetivos próprios; não
um pacote obrigatório. Pydantic valida em runtime, não substitui o type checker;
`frozen=True` não congela profundamente coleções mutáveis. Unicidade sob concorrência
não é garantida apenas por consultar antes de inserir.

Referências: [Cockburn, portas e adaptadores](https://alistair.cockburn.us/hexagonal-architecture),
[Pydantic, modelos](https://pydantic.dev/docs/validation/latest/concepts/models/).

## Trabalho depois da trilha

### Referência adicional: Cities: Skylines II

Pedido do autor em 16/09/2026: estudar comportamento dos agentes, dinâmica de demanda
e custo computacional de Cities: Skylines II. É inspiração de experiência, não uma
afirmação de como seu código interno funciona. Uma pesquisa posterior deve separar
documentação oficial, comportamento observado e hipóteses.

A IA será um contexto separado. Nesta trilha preparamos somente a integração:
uma fonte de demanda substituível, com cenários roteirizados para testes e a clientela
atual como implementação. A futura IA produz intenções; a operação continua dona da
validação e da execução. Não pode acessar filas, semáforos ou workers internos.

Pesquisa futura: agentes individuais versus agregados; frequência de decisão e
orçamento por tick; demanda emergente e retroalimentação; filas, capacidade e trajetos;
reprodutibilidade e sementes independentes; LOD de simulação; distinguir animação,
decisão e execução. Avaliar as técnicas conforme evidências e necessidades do curso.
O scaffold não simula a IA do jogo nem implementa esses algoritmos.

Clock virtual, pausas e replay; economia e agregados com transações; observabilidade
avançada; interface interativa; plugins; eventos duráveis. Entram quando a evolução
do jogo trouxer a necessidade, sem comprimir todos esses assuntos nesta trilha.

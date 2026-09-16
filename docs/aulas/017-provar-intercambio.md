# Aula 17 — Provar que as peças são intercambiáveis

## O pedido

Queremos exportar CSV e conectar o planejador futuro sem alterar a cozinha. Também
queremos saber se trocar uma implementação pode abandonar tasks em caso de falha.

## Passo a passo

1. Acrescente `CsvJournal`, obedecendo ao contrato de stream e eventos da aula 10.
2. Combine três observadores, duas fontes de demanda e dois armazenamentos. Execute
   o restaurante real em todas as doze combinações; confira resultado, meta e tasks.
3. Acrescente testes de dependências por AST, incluindo um import proibido de exemplo
   que prova que o verificador detecta a violação.
4. Injete observador que falha na abertura e no fechamento. A nova prova revela uma
   lacuna: exceção nesses pontos podia pular o encerramento do TaskGroup. Proteja-o.
5. Recuse reutilizar uma operação cujas filas já foram fechadas; crie outra por turno.

```bash
uv run python -m mise_en_place.demo
uv run pytest tests/test_interchange.py tests/test_architecture.py tests/test_lifecycle.py
uv run ruff check .
uv run pyright
uv run mypy --strict -p mise_en_place
git diff aula-16 aula-17 -- src tests
```

## Experimente

Adicione temporariamente `from ..adapters import storage` em `ai/scaffold.py`: o teste
arquitetural deve falhar. Restaure. Troque o CSV por memória na demo: a meta e o resultado
continuam iguais. O teste de CSV inclui vírgula, aspas e acento para provar a tradução.

## O que a evidência permite afirmar

As combinações testadas preservam o comportamento escolhido; interfaces tipadas e
testes de contrato atuam juntos. Um adaptador com outra semântica de erro ainda exige
análise. O check de imports cobre imports estáticos, não carregamentos dinâmicos.
Testes com escala zero verificam integração, não fidelidade temporal ou desempenho.

## Encerramento da trilha

Agora configuração, montagem, execução, demanda, observação e armazenamento têm donos
visíveis. O novo formato não exige mudar o worker; a futura IA conhece contratos; o jogo
reage a fatos. As falhas descobertas na prova final fazem parte da aula: isolamento não
elimina a necessidade de um ciclo de vida correto. A evolução seguinte pode estudar
tempo virtual, demanda reativa e orçamento de simulação, usando Cities: Skylines II como
referência de pesquisa — sem atribuir a ele algoritmos que ainda não verificamos.

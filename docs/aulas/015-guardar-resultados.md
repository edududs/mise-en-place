# Aula 15 — O turno acabou; o resultado precisa continuar

## O pedido

Queremos consultar amanhã o resultado de hoje. Até agora ele desaparece junto com o
processo. Salvar o restaurante inteiro tentaria serializar tasks, filas e semáforos.
O que precisamos agora é apenas a fotografia concluída.

## Passo a passo

1. Defina `ResultStore.save/load`: substituição por identificador, ausência como `None`,
   corrupção como erro, falhas de I/O propagadas.
2. Implemente memória e JSON versionado. Pydantic valida o arquivo lido.
3. Grave em arquivo temporário no mesmo diretório e substitua o destino, evitando
   expor um JSON parcialmente escrito.
4. Arquive após fechar o turno; conecte `--results-dir` à CLI.

```bash
uv run pytest tests/test_storage.py
uv run python -m mise_en_place --config examples/scenarios.json --results-dir results
uv run python -m mise_en_place --results-dir results --show scenario-1
git diff aula-14 aula-15 -- src tests
```

## Experimente

Carregue um ID inexistente e depois corrompa uma cópia de um arquivo válido. Ausência
e corrupção não podem produzir a mesma resposta. Execute novamente com os mesmos IDs:
os resultados são substituídos, conforme contrato. Use outro diretório para preservar
rodadas anteriores do experimento.

## Padrão e limite

A porta de armazenamento isola a aplicação do meio. O arquivo tem versão explícita;
migração de schema será necessária quando seu formato mudar. `replace` não promete
durabilidade contra falta de energia nem transação entre múltiplos arquivos. A escrita
é síncrona após o turno. Save/load de uma sessão viva permanece na trilha de simulação.

Conclusão: o mesmo teste passa em memória e em arquivo, e um novo adaptador lê o salvo.

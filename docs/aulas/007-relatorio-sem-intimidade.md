# Aula 7 — O relatório conhece demais

## O pedido

Queremos chamar uma cozinheira de Maria. A aula 5 identifica cozinheiros por
`name.startswith("chef")`: mudar um rótulo muda o cálculo. O relatório também atravessa
praças, garçons e workers para descobrir como a casa funciona.

## Passo a passo

1. Leia a coleta antiga no `__main__.py` da tag `aula-06`.
2. Registre `section` em `Preparer`: a praça já conhece o papel, sem inferência textual.
3. Extraia `Measurement` como fotografia imutável e `Restaurant.measurement` como
   ponto de consulta. A operação coleta seus próprios dados.
4. Faça o experimento consumir só a fotografia. A apresentação continua separada.

```bash
uv run pytest tests/test_results.py
uv run python -m mise_en_place
git diff aula-06 aula-07 -- src tests
```

## Experimente

Troque o nome no teste para qualquer nome sem `chef`. A ocupação continua sendo de
cozinha. Trocar o papel para bar deve mudar a classificação. Com escala zero,
utilização é zero por convenção: divisão por zero não produz métrica útil.

## O que ganhamos e o limite

Encapsulamento reduz o conhecimento necessário ao consumidor. A fotografia ainda é
específica deste relatório: não criamos um query engine. A operação continua sabendo
coletar os dados; separar isso em um serviço só se justifica quando houver outra razão.
Conclusão: nenhuma consulta no experimento deve identificar funcionário pelo nome.

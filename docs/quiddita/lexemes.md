# Lexemes

`client.lexemes` reads lexemes through the WikibaseLexeme REST API at `/w/rest.php/wikibaselexeme/v0`. The same paths under `wikibase/v1` answer 404 (verified 2026-11-27).

## Get a lexeme

```python
lexeme = await client.lexemes.get("L2")
print(lexeme.lemmas["en"])  # 'first'
print(lexeme.lexical_category)  # 'Q1084', a bare item id
print(lexeme.forms[0].representations)  # {'en': 'firsts'}
print(lexeme.forms[0].grammatical_features)  # ['Q146786']
print(lexeme.senses[0].glosses["en"])
```

`get()` returns a `RestLexeme` with `lemmas`, `lexical_category`, `language`, `statements`, `forms`, and `senses`. `lexical_category` and `language` are bare item ids here, unlike the `wbgetentities` lexeme payload where they are nested objects. Each form carries `representations`, `grammatical_features`, and `statements`; each sense carries `glosses` and `statements`. The statement models are the same `RestStatement` shapes the item routes return.

There are no per-form or per-sense routes: `/entities/forms/{id}` and `/entities/senses/{id}` answer `rest-no-match` (verified 2026-11-27), so forms and senses come inside the lexeme payload. Lexemes, forms, and senses through `wbgetentities` stay available through `client.entities`.

# Members

`client.members` covers `/members` and `/members/{id}`. Member ids are plain integers.

```python
from stavrophora import MemberFilters

member = await client.members.get(297)
member.primary_name
member.prefix  # list of {name, value} prefix entries

page = await client.members.search(MemberFilters(prefix="10.1038"))
```

The route accepts `query` plus the member filters (`prefix`, `backfile-doi-count`, `current-doi-count`). `sort` and `select` raise `ConfigurationError` client-side.

`members.works(id)` returns a works client bound to `/members/{id}/works`; see [Works](works.md#scoped-works).

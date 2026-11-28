# GraphQL

The `graphql` resource sends queries to the public GraphQL API of DataCite
at `https://api.datacite.org/graphql`. Its schema covers the same records
as the REST routes (works, persons, organizations, repositories, funders,
prefixes, and events) and the connections between them, so one query can
fetch a work together with its creators, its repository, and its citing
works. Queries need no login.

```python
data = await client.graphql.query(
    """
    query($id: ID!) {
      work(id: $id) {
        doi
        titles { title }
        creators { name }
        publicationYear
        citationCount
        repository { uid name }
      }
    }
    """,
    {"id": "https://doi.org/10.5438/0012"},
)
work = data["work"]
print(work["doi"], work["citationCount"])
```

## The answer is plain data

The answer follows the query, so `query()` returns the `data` object as
plain dictionaries and lists. The client does not validate it. Ask for the
fields you need. The `id` argument of a work is its DOI as a URL
(`https://doi.org/10.5438/0012`).

An introspection query lists the schema: the 69 fields of the `Query` type
and their arguments, such as the `published`, `registrationAgency`,
`repositoryId`, and `userId` filters of the list fields.

```python
schema = await client.graphql.query(
    "{ __schema { queryType { fields { name args { name } } } } }"
)
```

## Errors

DataCite reports a rejected query (an unknown field, a wrong argument type)
with status 400. It reports a field that fails (a record that does not
exist) with status 200 and an `errors` list. Both raise `APIError`. Its
`body` holds the answer of DataCite with every error message and its
`path`.

## Mutations need a token

Mutations need a bearer token and are not part of this client. See the
deferred list in the roadmap for the condition that unblocks them.

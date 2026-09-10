def normalize_query(query):
    while query and query[0].isspace():
        query = query[1:]
    while query and query[-1].isspace():
        query = query[:-1]
    return query.lower()

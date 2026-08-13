"""
data_engine.relationships
─────────────────────────────
For multi-table input, looks for shared Identifier-role columns as candidate
join keys between tables. For a single-table dataset this simply returns an
empty list — there's nothing to relate.
"""


class RelationshipDiscoverer:
    def discover(self, dataframes: dict, roles_by_table: dict) -> list:
        rels = []
        tables = list(dataframes.keys())
        for i in range(len(tables)):
            for j in range(i + 1, len(tables)):
                t1, t2 = tables[i], tables[j]
                cols1 = set(dataframes[t1].columns)
                cols2 = set(dataframes[t2].columns)
                shared_ids = [
                    c for c in (cols1 & cols2)
                    if roles_by_table.get(t1, {}).get(c) == "Identifier"
                ]
                for c in shared_ids:
                    rels.append(dict(table_a=t1, column_a=c, table_b=t2, column_b=c, type="foreign_key_candidate"))
        return rels

from cat.plugins.cc_ComponentPicker.database import get_table_types, get_units_per_table, get_DB_tables_ddl

import json


def get_needed_tables(cat, query, db_path, index_table):
    db_structure, table_names = get_structure(db_path, index_table)

    cat_query = f"""Resoind with a JSON list containing the names of SQLite tables needed to extract requested electrical components from a database.
Tables only contain the specific components categorized by the title and not generic components related to that.
Use ONLY given tables in the structure to find data, if there doesn't exist any table where the request can be found return an empty JSON list.
REQUEST:
{query}
DATABASE STRUCTURE:
{db_structure}"""

    cat_response = cat.llm(cat_query)
    cat_response = cat_response.replace(
        "`", "").replace("json", "").replace("\n", "")

    return json.loads(cat_response), table_names, db_structure


def get_db_query(cat, query, db_structure, db_path, index_table, tables, unit_tables, use_units):

    units = ""
    if use_units:
        units = "MEASUREMENT UNITS:\n"
        units += get_units_for_tables(db_path,
                                      tables, index_table, unit_tables)

    cat_query = f"""Respond with an SQLite query to extract requested components from a database.
When searching for TEXT use the LIKE comparator instead of =
ALWAYS Use ID references to other tables indicated in the foreign keys when possible, and NEVER make the query return the ID itself but the value it points to unless specificately stated.
Use ONLY given tables in the structure to find data, if there is not what the user requestet make an SQLite query that returns no data.
Always include a 15 rows limit for the output and order by relevant data asked by the user.
REQUEST:
{query}
DATABASE STRUCTURE:
{db_structure}
{units}"""

    result = cat.llm(cat_query).replace("`", "").replace("sql", "")

    return result, units


def get_tables(db_path, index_table):
    table_types = get_table_types(db_path, index_table)

    data_tables = []
    advanced_tables = []

    unit_tables = [None for _ in range(3)]
    # 0: columns_metadata_table_name
    # 1: units_map_table_name
    # 2: units_table_name

    # Table types
    # |ID |Description                |
    # |---|---------------------------|
    # |0  |Main index table           |
    # |1  |Table function descriptions|
    # |2  |Columns index table        |
    # |3  |Measurement units mapping  |
    # |4  |Measurement units          |
    # |5  |Normal data table          |
    # |6  |Advanced search data table |

    for name, type in table_types:
        match type:
            case 2:
                unit_tables[0] = name
            case 3:
                unit_tables[1] = name
            case 4:
                unit_tables[2] = name
            case 5:
                data_tables.append(name)
            case 6:
                advanced_tables.append(name)

    use_units = all(name is not None for name in unit_tables)

    return data_tables, advanced_tables, unit_tables, use_units


def get_structure(db_path, index_table):
    data_tables, advanced_tables, unit_tables, use_units = get_tables(
        db_path, index_table)

    total_tables = data_tables + advanced_tables
    table_DDLs = get_DB_tables_ddl(db_path, total_tables)

    db_structure = "\n".join(ddl for _, ddl in table_DDLs.items())
    return db_structure, (data_tables, advanced_tables, unit_tables, use_units)


def get_units_for_tables(db_path, table_names, index_table, unit_tables):
    units_list = get_units_per_table(
        db_path, unit_tables[0], unit_tables[1], unit_tables[2], index_table)

    units = ""
    for table, t_units in units_list.items():
        if table in table_names:
            units += f"Table: {table}\n{t_units}\n"

    return units

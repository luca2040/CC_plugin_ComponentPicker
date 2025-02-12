## CheshireCat Component Picker Plugin

### Simple plugin for the CheshireCat AI framework to find a requested electrical component from a SQLite database.

---

#### Database:

The database [database.sqlite](https://github.com/luca2040/CC_plugin_ComponentPicker/blob/main/db/database.sqlite) contains all the data about the components, divided by table and indexed by an `index table`.

The `index table` sets the table type for every table in the DB.
<br/>**_Table types:_**

|Type |Description                |
|-----|---------------------------|
|0    |Index table                |
|1    |Table function descriptions|
|2    |Columns index table        |
|3    |Measurement units mapping  |
|4    |Measurement units          |
|5    |Normal data table          |
|6    |Advanced search data table |
|7    |Advanced table reference   |

_The `Table function descriptions` table is only needed to describe what every table does, and does not get used in the search process._

The table `Columns index table` is used to set an ID for each column in the tables, and to provide a complete list of the columns with the respective table to make some functions in the search process more intuitive.

The tables `Measurement units mapping` and `Measurement units` are used to set the measurement units for the data contained in other tables.

Then the tables that contain the list of componenets, are the ones with the type `Normal data table` and `Advanced search data table`.

The **normal tables** are tables containing a list of components relative to the table name, with a specific characteristic per column, stored in numbers or simple text that can be used to simply search using SQL queries.

The **advanced tables** (which actually seem simpler from the structure side) contain only data that cannot be used for simple search using SQL queries, saved as text. Those tables are loaded and stored in the `Elasticsearch` database during the cat setup, then when the user asks about one of that components or needs to see that data instead of the SQL query a simple `Elasticsearch` query is generated.

<details>
<summary>Index tables DDL</summary>

```sql
-- Tables_metadata definition

CREATE TABLE Tables_metadata (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Table_name TEXT UNIQUE NOT NULL,
    Table_type INTEGER NOT NULL,
    FOREIGN KEY (Table_type) REFERENCES Table_types(ID)
);

-- Table_types definition

CREATE TABLE "Table_types" (
	ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	Description TEXT NOT NULL
);

-- Columns_metadata definition

CREATE TABLE Columns_metadata (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Table_ID INTEGER NOT NULL,
    Column_name TEXT NOT NULL,
    FOREIGN KEY (Table_ID) REFERENCES Tables_metadata(ID) ON DELETE CASCADE,
    UNIQUE(Table_ID, Column_name)
);

-- Units_mapping definition

CREATE TABLE Units_mapping (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Unit_ID INTEGER NOT NULL,
    Table_ID INTEGER NOT NULL,
    Column_ID INTEGER NOT NULL,
    FOREIGN KEY (Table_ID) REFERENCES Tables_metadata(ID) ON DELETE CASCADE,
    FOREIGN KEY (Column_ID) REFERENCES Columns_metadata(ID) ON DELETE CASCADE,
    FOREIGN KEY (Unit_ID) REFERENCES Measurement_units(ID),
    UNIQUE(Table_ID, Column_ID, Unit_ID)
);

-- Measurement_units definition

CREATE TABLE Measurement_units (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Unit TEXT UNIQUE NOT NULL
);
```

</details>

---

#### Plugin:

This plugin uses a `tool` to get the user request, formatted in human language, then it passes it to a series of function that, using an LLM, check if the request needs data stored in **simple** or **advanced** tables, and respectly generates an SQL query or an Elasticsearch query.

The functions that classify the request and generate the respective queries, need to use an LLM. For efficiency and to not make too many requests to the model set in the cat, an `Ollama` local model is used.

[compose.yml](https://github.com/luca2040/CC_plugin_ComponentPicker/blob/main/compose.yml):
```yml
  ollama:
    container_name: ollama
    image: ollama/ollama:latest
    volumes:
      - ollama:/root/.ollama
    environment:
      - gpus=all
      ...
    ...
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [ gpu ]
    ...
  ...

volumes:
  ollama:
```

`Ollama` is set to run on a local GPU, and the model to use is set through the .env file from the cat.

[compose.yml](https://github.com/luca2040/CC_plugin_ComponentPicker/blob/main/compose.yml):
```yml
  cheshire-cat-core:
  ...
    environment:
      ...
      - OLLAMA_MODEL=${CAT_OLLAMA_MODEL}
      - OLLAMA_API=${OLLAMA_API}
      - OLLAMA_KEEP_ALIVE=${OLLAMA_KEEP_ALIVE}
    ...
```

<details>
<summary>Example .env config file</summary>

```.env
ES_LOCAL_VERSION=8.17.0
ES_LOCAL_CONTAINER_NAME=es-local-dev
ES_LOCAL_PASSWORD=example
ES_LOCAL_URL=http://localhost:9200
ES_LOCAL_PORT=9200
ES_LOCAL_HEAP_INIT=128m
ES_LOCAL_HEAP_MAX=2g
ES_LOCAL_DISK_SPACE_REQUIRED=1gb
ES_LOCAL_API_KEY=key
ES_CAT_KEY=key

KIBANA_LOCAL_CONTAINER_NAME=kibana-local-dev
KIBANA_LOCAL_PORT=5601
KIBANA_LOCAL_PASSWORD=example
KIBANA_ENCRYPTION_KEY=key

CCAT_LOG_LEVEL=INFO
CAT_DB_PATH=/app/cat/componentsDB/database.sqlite
CAT_INDEX_TABLE=Tables_metadata
ELASTIC_URL=http://elasticsearch:9200

CAT_OLLAMA_MODEL="gemma2:27b"
OLLAMA_API=http://ollama:11434/api
OLLAMA_KEEP_ALIVE=60m
```

</details>

To force the LLM to respond in a specific format, for example a JSON list used to classify tables, when the `Ollama API` is called also a `format` is passed, which limits the LLM output to only that specific format.

[ollama.py](https://github.com/luca2040/CC_plugin_ComponentPicker/blob/main/cat/plugins/cc_ComponentPicker/ollama.py)
```python
    def llm(self, query: str, format=None) -> str:

        request = {
            "model": self.model,
            "messages": [{"role": "user", "content": query}],
            "stream": False,
        }

        if format:
            request["format"] = format

        # ...
```
The `format` is an object formatted in JSON that specifies what should be the structure, for example:

```python
# JSON list:
format = {
          "type": "array",
          "items": {"type": "string"},
         }

# SQL query:
format = {
          "type": "object",
          "properties": {
              "SQL_query": {"type": "string"},
          },
          "required": ["SQL_query"],
         },
```

The functions that use the `format` are in the [data.py](https://github.com/luca2040/CC_plugin_ComponentPicker/blob/main/cat/plugins/cc_ComponentPicker/data.py) file:

<details>
<summary>get_needed_tables</summary>

```python
def get_needed_tables(
    llm, query: str, db_path: str, index_table: str
) -> Tuple[List[str], str, str]:
    """Returns the list of tables that need to be used to extract the data specified by the query from the DB."""

    db_structure, table_names = get_structure(db_path, index_table)

    llm_query = f"""Respond with a JSON list containing the names of SQLite tables needed to extract requested electrical components from a database.
Tables only contain components categorized by the title, except for general categories like microcontrollers or integrated circuits.
Use ONLY given tables in the structure to find data.
REQUEST:
{query}
DATABASE STRUCTURE:
{db_structure}"""

    llm_response = llm.llm(
        llm_query,
        format={
            "type": "array",
            "items": {"type": "string"},
        },
    )

    return json.loads(llm_response), table_names, db_structure
```

</details>

<details>
<summary>get_db_query</summary>

```python
def get_db_query(
    llm,
    query: str,
    db_structure: str,
    db_path: str,
    index_table: str,
    tables: List[str],
    unit_tables: List[str],
    use_units: bool,
) -> Tuple[str, str]:
    """Returns an SQLite query that extracts from the DB the data specified in the query.
    The database structure is needed to tell the LLM to generate the query based on that structure.
    """

    units = ""
    if use_units:
        units = "MEASUREMENT UNITS:\n"
        units += get_units_for_tables(db_path, tables, index_table, unit_tables)

    llm_query = f"""Respond with an SQLite query to extract requested components from a database.
When searching for TEXT use the LIKE comparator instead of =
ALWAYS Use ID references to other tables indicated in the foreign keys when possible, and NEVER make the query return the ID itself but the value it points to unless specificately stated.
Use ONLY given tables in the structure to find data, if there is not what the user requestet make an SQLite query that returns no data.
Always include a 15 rows limit for the output and order by relevant data asked by the user, ONLY if not asked to find a maximum or minimum value, if so then use the respective functions to get only that value.
REQUEST:
{query}
DATABASE STRUCTURE:
{db_structure}
{units}"""

    llm_response = llm.llm(
        llm_query,
        format={
            "type": "object",
            "properties": {
                "SQL_query": {"type": "string"},
            },
            "required": ["SQL_query"],
        },
    )

    result = json.loads(llm_response)["SQL_query"]

    return result, units
```

</details>

<details>
<summary>get_elastic_query</summary>

```python
def get_elastic_query(llm, input: str) -> str:
    """Returns an elasticsearch-optimized query based on the input query."""

    llm_query = f"""Given a query, generate another query that represents the input.
Your response should contain the request in the input, but formatted in a way optimized for a search engine looking into a components database,
using keywords and removing useless words.
Yout response also should be the most concise possible and point to the correct result.
QUERY:
{input}"""

    llm_response = llm.llm(
        llm_query,
        format={
            "type": "object",
            "properties": {
                "search_query": {"type": "string"},
            },
            "required": ["search_query"],
        },
    )

    return json.loads(llm_response)["search_query"]
```

</details>
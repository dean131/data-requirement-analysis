# SchemaCrawler User Guide

### *Comprehensive Guide for Generating Database Documentation, Data Dictionaries, ER Diagrams, and DBML Models*

---

## Table of Contents

1. [Introduction](#10-introduction)
2. [Prerequisites](#20-prerequisites)
3. [Initial Setup](#30-initial-setup)
4. [Connection Parameters](#40-connection-parameters)
5. [Output Format Options](#50-output-format-options)
6. [Standard Documentation Commands](#60-standard-documentation-commands)

   * [6.1 `--command=details`](#61---commanddetails)
   * [6.2 `--command=schema`](#62---commandschema)
   * [6.3 `--command=list`](#63---commandlist)
   * [6.4 `--command=count`](#64---commandcount)
   * [6.5 `--command=brief`](#65---commandbrief)
7. [Advanced Analysis Commands](#70-advanced-analysis-commands)

   * [7.1 `--command=lint`](#71---commandlint)
   * [7.2 `--command=serialize`](#72---commandserialize)
   * [7.3 `--command=grep`](#73---commandgrep)
   * [7.4 `--command=dbml`](#74---commanddbml)
8. [Customization and Advanced Features](#80-customization-and-advanced-features)

   * [8.1 Result Filtering](#81-result-filtering)
   * [8.2 Custom Annotations (Data Dictionary)](#82-custom-annotations-data-dictionary)
   * [8.3 Configuring Information Levels](#83-configuring-information-levels)
   * [8.4 Adding Custom Titles](#84-adding-custom-titles)
   * [8.5 Loading External Configuration Files](#85-loading-external-configuration-files)
9. [Case Study: Complete Usage Example](#90-case-study-complete-usage-example)
10. [Command Summary](#100-command-summary)
11. [Best Practices Recommendations](#110-best-practices-recommendations)
12. [Appendix: Using DBML Files with dbdiagram.io](#120-appendix-using-dbml-files-with-dbdiagramio)

---

## 1.0 Introduction

**SchemaCrawler** is an open-source, Java-based tool designed to analyze, visualize, and document database schemas. It connects to an existing database and produces professional documentation in multiple formats such as **HTML**, **PDF**, **Markdown**, **DBML**, **plain text**, or **JSON**.

Its core functionalities include:

* Generating comprehensive **Data Dictionaries**
* Creating **Entity-Relationship Diagrams (ERDs)**
* Exporting **DBML models** for dbdiagram.io
* Producing machine-readable schema exports for automation and version control

---

## 2.0 Prerequisites

Before beginning, ensure the following requirements are met:

* **Docker:** The Docker engine must be installed and running.
* **Database Access:** Have valid credentials and connection details (MySQL, PostgreSQL, etc.).
* **Project Directory:** Create a working directory to store outputs and configuration files.

---

## 3.0 Initial Setup

To manage input and output files efficiently, create a structured local environment.

```bash
# Create directory for output files
mkdir -p json

# Create directory for JDBC drivers (.jar files)
mkdir -p drivers

# Create a custom annotation file (optional)
touch dictionary.yaml

# Create a configuration file (optional)
touch schemacrawler.config.properties
```

Launch SchemaCrawler using an interactive Docker session:

```bash
docker run \
  -v $(pwd)/json:/home/schcrwlr/share \
  -v $(pwd)/drivers:/home/schcrwlr/drivers \
  -v $(pwd)/dictionary.yaml:/home/schcrwlr/dictionary.yaml \
  -v $(pwd)/schemacrawler.config.properties:/home/schcrwlr/schemacrawler.config.properties \
  --rm -it \
  --entrypoint=/bin/bash \
  schemacrawler/schemacrawler
```

After running the command, you’ll enter the container shell:

```
schcrwlr@container:/home/schcrwlr$
```

---

## 4.0 Connection Parameters

| Option                    | Example                            | Description                                           |
| :------------------------ | :--------------------------------- | :---------------------------------------------------- |
| `--server`                | `mysql`                            | Database server type.                                 |
| `--database`              | `my_database`                      | Database name.                                        |
| `--host`                  | `172.17.0.1`                       | Host IP address (use Docker bridge IP for localhost). |
| `--port`                  | `3306`                             | Connection port.                                      |
| `--user`                  | `root`                             | Username for authentication.                          |
| `--password`              | `root_password`                    | Password for authentication.                          |
| `--drivers`               | `/home/schcrwlr/drivers/mysql.jar` | (Optional) Path to JDBC driver.                       |
| `--connection-properties` | `sslmode=require`                  | (Optional) Additional driver properties.              |

---

## 5.0 Output Format Options

| Format     | Description                                | Example                     |
| :--------- | :----------------------------------------- | :-------------------------- |
| `html`     | Interactive, web-friendly documentation.   | `--output-format=html`      |
| `pdf`      | Printable document format.                 | `--output-format=pdf`       |
| `markdown` | Plain-text format for version control.     | `--output-format=markdown`  |
| `text`     | Minimal plain text output.                 | `--output-format=text`      |
| `json`     | Structured data for further processing.    | `--output-format=json`      |
| `dbml`*    | Database Markup Language for dbdiagram.io. | `--command=dbml` (see §7.4) |

> **Note:**
> DBML export is implemented as a Python script (`dbml.py`).
> To use it as a built-in command, ensure your `/home/schcrwlr/schemacrawler.config.properties` file contains:
>
> ```
> schemacrawler.command.dbml.script = dbml.py
> ```
>
> Alternatively, you can call it directly using:
>
> ```
> --command=script --script-language=python --script=dbml.py
> ```

---

## 6.0 Standard Documentation Commands

### 6.1 `--command=details`

Generates a detailed data dictionary.

```bash
schemacrawler ... \
  --info-level=maximum \
  --command=details \
  --title="Database Data Dictionary" \
  --output-format=html \
  --output-file="/home/schcrwlr/share/data_dictionary.html"
```

---

### 6.2 `--command=schema`

Generates a relational ER diagram.

```bash
schemacrawler ... \
  --command=schema \
  --info-level=standard \
  --output-format=pdf \
  --output-file="/home/schcrwlr/share/er_diagram.pdf"
```

---

### 6.3 `--command=list`

Lists all schema objects.

```bash
schemacrawler ... \
  --command=list \
  --info-level=standard \
  --output-format=text \
  --output-file="/home/schcrwlr/share/schema_list.txt"
```

---

### 6.4 `--command=count`

Counts rows in each table (if supported).

```bash
schemacrawler ... \
  --command=count \
  --output-format=text \
  --output-file="/home/schcrwlr/share/table_counts.txt"
```

---

### 6.5 `--command=brief`

Generates a concise schema summary.

```bash
schemacrawler ... \
  --command=brief \
  --info-level=standard \
  --output-format=text \
  --output-file="/home/schcrwlr/share/schema_brief.txt"
```

---

## 7.0 Advanced Analysis Commands

### 7.1 `--command=lint`

Performs a best-practice audit.

```bash
schemacrawler ... \
  --command=lint \
  --output-format=text \
  --output-file="/home/schcrwlr/share/lint_report.txt"
```

---

### 7.2 `--command=serialize`

Exports schema metadata to JSON or YAML.

```bash
schemacrawler ... \
  --info-level=maximum \
  --command=serialize \
  --output-format=json \
  --output-file="/home/schcrwlr/share/schema_dump.json"
```

---

### 7.3 `--command=grep`

Searches for database objects matching regex patterns.

```bash
schemacrawler ... \
  --command=grep \
  --grep-tables=.*customer.* \
  --output-format=text \
  --output-file="/home/schcrwlr/share/grep_customer.txt"
```

---

### 7.4 `--command=dbml`

Generates **Database Markup Language (DBML)** files for import into visualization tools like **[dbdiagram.io](https://dbdiagram.io)**.

**Example (registered command):**

```bash
schemacrawler \
  --server=postgresql \
  --database=your_db \
  --host=127.0.0.1 \
  --port=5432 \
  --user=user \
  --password=password123 \
  --schemas=tms \
  --info-level=standard \
  --command=dbml \
  --output-file="/home/schcrwlr/share/name_of_output.dbml"
```

**Example (direct script execution):**

```bash
schemacrawler \
  --server=postgresql \
  --database=your_db \
  --host=127.0.0.1 \
  --port=5432 \
  --user=user \
  --password=password123 \
  --schemas=name_of_schema \
  --info-level=standard \
  --command=script \
  --script-language=python \
  --script=dbml.py \
  --output-file="/home/schcrwlr/share/scylla_schema_name_of_schema.dbml"
```

**Result:**

* Produces `.dbml` file compatible with dbdiagram.io
* Includes relationships, keys, indexes, and remarks

---

## 8.0 Customization and Advanced Features

### 8.1 Result Filtering

```bash
--include-tables=users|orders
--exclude-tables=.*log.*
```

### 8.2 Custom Annotations (Data Dictionary)

Define business descriptions in `dictionary.yaml` and attach via:

```bash
--load-extension=schemacrawler.tools.databaseconnector.extension.data.dictionary \
--attributes-file=/home/schcrwlr/dictionary.yaml
```

### 8.3 Configuring Information Levels

| Level      | Description                               |
| :--------- | :---------------------------------------- |
| `minimum`  | Basic tables and columns only             |
| `standard` | Includes PK/FK and constraints            |
| `detailed` | Adds indexes and defaults                 |
| `maximum`  | Adds triggers, routines, and all metadata |

### 8.4 Adding Custom Titles

```bash
--title="My Database Documentation"
```

### 8.5 Loading External Configuration Files

```bash
--load-config=/home/schcrwlr/schemacrawler.config.properties
```

---

## 9.0 Case Study: Complete Usage Example

Generate a fully annotated **HTML Data Dictionary** for selected tables:

```bash
schemacrawler \
  --server=mysql \
  --database=example_db \
  --host=172.17.0.1 \
  --port=3306 \
  --user=user_db \
  --password=password_db \
  --command=details \
  --info-level=maximum \
  --load-extension=schemacrawler.tools.databaseconnector.extension.data.dictionary \
  --attributes-file=/home/schcrwlr/dictionary.yaml \
  --include-tables=users|orders \
  --title="Business Data Dictionary (Users & Orders)" \
  --output-format=html \
  --output-file="/home/schcrwlr/share/business_data_dictionary.html"
```

---

## 10.0 Command Summary

| Use Case           | Command               | Output                 |
| :----------------- | :-------------------- | :--------------------- |
| Data Dictionary    | `--command=details`   | `data_dictionary.html` |
| ER Diagram         | `--command=schema`    | `er_diagram.pdf`       |
| Schema Object List | `--command=list`      | `schema_list.txt`      |
| Row Count          | `--command=count`     | `table_counts.txt`     |
| Summary            | `--command=brief`     | `schema_brief.txt`     |
| Object Search      | `--command=grep`      | `grep_customer.txt`    |
| Design Audit       | `--command=lint`      | `lint_report.txt`      |
| JSON Export        | `--command=serialize` | `schema_dump.json`     |
| DBML Export        | `--command=dbml`      | `schema_model.dbml`    |

---

## 11.0 Best Practices Recommendations

* **Use `/home/schcrwlr/share/`** as the standard output path for mounted results.
* **Prefer `--info-level=maximum`** for comprehensive metadata capture.
* **Enhance readability** with dictionary annotations and database comments.
* **Version control** your `.dbml` files for schema evolution tracking.
* **Combine `serialize` + `dbml`** to cover both automated and visual documentation needs.

---

## 12.0 Appendix: Using DBML Files with dbdiagram.io

The generated `.dbml` files can be visualized directly on [dbdiagram.io](https://dbdiagram.io) or with the **DBML CLI**.

### Option 1 — Online Viewer

1. Open [https://dbdiagram.io](https://dbdiagram.io)
2. Click **Import > From DBML file**
3. Upload your `schema_model.dbml`
4. The ER diagram will render automatically.

### Option 2 — Local DBML CLI Conversion

Install DBML CLI (Node.js-based):

```bash
npm install -g @dbml/cli
```

Generate a diagram or SQL directly from your `.dbml`:

```bash
# Generate PostgreSQL DDL
dbml2sql /path/to/schema_model.dbml --postgres -o output.sql

# Convert DBML to PNG diagram
dbml-render /path/to/schema_model.dbml -o diagram.png
```

### Option 3 — Git Integration

Store your DBML exports in version control:

```
/dbml/
  ├── customer_schema.dbml
  ├── order_schema.dbml
  └── inventory_schema.dbml
```

Each commit will track schema changes as readable diffs, making DBML ideal for cross-team collaboration between developers, DBAs, and analysts.

---

✅ **End of Document**
*This guide now fully supports SchemaCrawler 17.1.4, including built-in DBML generation and dbdiagram.io integration.*

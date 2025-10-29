# 📘 SchemaCrawler Usage Guide

### _Generate Database Documentation, Data Dictionaries, and ER Diagrams Automatically_

---

## 🧩 1. Overview

**SchemaCrawler** is an open-source tool that helps you **analyze, visualize, and document** database structures.
It connects to your existing database and exports professional documentation in formats such as **HTML**, **PDF**, **Markdown**, **Text**, or **JSON**.

You can generate:

- A **Data Dictionary**
- An **Entity-Relationship Diagram (ERD)**
- A **Schema Summary**
- Row counts, statistics, and more

---

## ⚙️ 2. Requirements

- 🐳 **Docker** installed
- 🗃️ Access to your database (MySQL, PostgreSQL, etc.)
- 📂 A local folder to store output

---

## 📁 3. Setup

Inside your project directory:

```bash
mkdir -p output
```

This folder will store generated documentation (e.g., `data_dictionary.html`).

Then start SchemaCrawler interactively:

```bash
docker run \
  -v $(pwd)/output:/home/schcrwlr/share \
  --rm -it \
  --entrypoint=/bin/bash \
  schemacrawler/schemacrawler
```

You’ll now see a prompt inside the container:

```
schcrwlr@container:/home/schcrwlr$
```

---

## 🧠 4. Connection Parameters

Each SchemaCrawler command shares these basic options:

| Option       | Example           | Description                             |
| :----------- | :---------------- | :-------------------------------------- |
| `--server`   | `mysql`           | Database type                           |
| `--database` | `terafarma_clone` | Database name                           |
| `--host`     | `172.17.0.1`      | Host IP (use Docker bridge IP if local) |
| `--port`     | `3306`            | Database port                           |
| `--user`     | `root`            | Username                                |
| `--password` | `root_password`   | Password                                |

---

## 🧾 5. Common Output Formats

| Format     | Description                      | Example Flag               |
| :--------- | :------------------------------- | :------------------------- |
| `html`     | Clean, interactive documentation | `--output-format=html`     |
| `pdf`      | Printable, shareable             | `--output-format=pdf`      |
| `markdown` | Git-friendly                     | `--output-format=markdown` |
| `text`     | Terminal-friendly                | `--output-format=text`     |
| `json`     | Machine-readable                 | `--output-format=json`     |

Output files should always be saved under `/home/schcrwlr/share/`,
which maps to your local `./output/` folder.

---

## ⚙️ 6. Commands Overview

SchemaCrawler’s behavior depends on the **`--command`** option.
Each command produces a different type of output — from overviews to full data dictionaries.

---

### 🧱 `--command=details` → Full Data Dictionary

Generates a **detailed data dictionary** listing all tables, columns, constraints, and descriptions.

**Example:**

```bash
schemacrawler \
  --server=mysql \
  --database=terafarma_clone \
  --host=172.17.0.1 \
  --port=3306 \
  --user=root \
  --password=root_password \
  --info-level=maximum \
  --command=details \
  --title="TeraFarma Data Dictionary" \
  --output-format=html \
  --output-file="/home/schcrwlr/share/data_dictionary.html"
```

**Output:**
`output/data_dictionary.html` — full documentation of your schema.

---

### 🧩 `--command=schema` → ER Diagram

Generates a **graphical diagram** showing relationships between tables.

**Example:**

```bash
schemacrawler \
  --server=mysql \
  --database=terafarma_clone \
  --host=172.17.0.1 \
  --port=3306 \
  --user=root \
  --password=root_password \
  --command=schema \
  --info-level=standard \
  --title="TeraFarma ER Diagram" \
  --output-format=pdf \
  --output-file="/home/schcrwlr/share/er_diagram.pdf"
```

**Output:**
`output/er_diagram.pdf` — entity-relationship diagram.

---

### 📋 `--command=list` → Quick Object List

Generates a **list of all objects** (tables, views, routines, etc.) in the schema.

**Example:**

```bash
schemacrawler \
  --server=mysql \
  --database=terafarma_clone \
  --host=172.17.0.1 \
  --port=3306 \
  --user=root \
  --password=root_password \
  --command=list \
  --info-level=standard \
  --output-format=text \
  --output-file="/home/schcrwlr/share/schema_list.txt"
```

**Output:**
`output/schema_list.txt` — a summarized text list of database objects.

---

### 🔢 `--command=count` → Row Counts per Table

Displays the **number of rows** in each table (for supported databases).

**Example:**

```bash
schemacrawler \
  --server=mysql \
  --database=terafarma_clone \
  --host=172.17.0.1 \
  --port=3306 \
  --user=root \
  --password=root_password \
  --command=count \
  --output-format=text \
  --output-file="/home/schcrwlr/share/table_counts.txt"
```

**Output:**
`output/table_counts.txt` — table names with row counts.

---

### ⚙️ `--command=brief` → Compact Schema Summary

A **short summary** with basic information (good for quick checks).

**Example:**

```bash
schemacrawler \
  --server=mysql \
  --database=terafarma_clone \
  --host=172.17.0.1 \
  --port=3306 \
  --user=root \
  --password=root_password \
  --command=brief \
  --info-level=standard \
  --output-format=text \
  --output-file="/home/schcrwlr/share/schema_brief.txt"
```

**Output:**
`output/schema_brief.txt` — brief summary of tables, columns, and keys.

---

### 🔍 `--command=grep` → Search Objects by Name or Text

Search database objects by **regex or keyword**.

**Example:**

```bash
schemacrawler \
  --server=mysql \
  --database=terafarma_clone \
  --host=172.17.0.1 \
  --port=3306 \
  --user=root \
  --password=root_password \
  --command=grep \
  --grep-tables=.*customer.* \
  --output-format=text \
  --output-file="/home/schcrwlr/share/grep_customer.txt"
```

**Output:**
`output/grep_customer.txt` — filtered list of tables matching `customer`.

---

## 📊 7. Info Levels

You can control the **depth of information** included using `--info-level`:

| Level      | Description                          |
| :--------- | :----------------------------------- |
| `minimum`  | Only tables and columns              |
| `standard` | + Keys and constraints               |
| `maximum`  | + Indexes, triggers, remarks         |
| `detailed` | + Additional metadata and statistics |

**Example:**

```bash
--info-level=maximum
```

---

## 🧩 8. Adding a Custom Title

Add a custom title to the output header (HTML/PDF/Markdown):

```bash
--title="TeraFarma Database Documentation"
```

---

## 🎨 9. Optional: Improve Text Formatting

Create a config file for better formatting (optional):

**`schemacrawler.config.properties`**

```properties
schemacrawler.formatting.text.alignment=left
schemacrawler.formatting.text.line.width=120
schemacrawler.formatting.header.underline=true
schemacrawler.formatting.text.show.unicode=false
```

Then run SchemaCrawler with:

```bash
--load-config=schemacrawler.config.properties
```

---

## 📄 10. Example: Generate All Outputs in One Session

Run these commands inside the container to generate multiple documentation formats:

```bash
# Full Data Dictionary
schemacrawler --server=mysql --database=terafarma_clone --host=172.17.0.1 --port=3306 --user=root --password=root_password --info-level=maximum --command=details --output-format=html --output-file="/home/schcrwlr/share/data_dictionary.html"

# ER Diagram
schemacrawler --server=mysql --database=terafarma_clone --host=172.17.0.1 --port=3306 --user=root --password=root_password --command=schema --info-level=standard --output-format=pdf --output-file="/home/schcrwlr/share/er_diagram.pdf"

# Markdown for GitHub
schemacrawler --server=mysql --database=terafarma_clone --host=172.17.0.1 --port=3306 --user=root --password=root_password --info-level=maximum --command=details --output-format=markdown --output-file="/home/schcrwlr/share/data_dictionary.md"
```

---

## ✅ 11. Summary

| Purpose         | Command             | Output Example         |
| :-------------- | :------------------ | :--------------------- |
| Data Dictionary | `--command=details` | `data_dictionary.html` |
| ER Diagram      | `--command=schema`  | `er_diagram.pdf`       |
| Object List     | `--command=list`    | `schema_list.txt`      |
| Row Counts      | `--command=count`   | `table_counts.txt`     |
| Brief Summary   | `--command=brief`   | `schema_brief.txt`     |
| Search Objects  | `--command=grep`    | `grep_customer.txt`    |

---

## 💡 12. Tips

- Always save output to `/home/schcrwlr/share/...`
- Use `--info-level=maximum` for complete documentation
- HTML and PDF formats are best for readability
- Add `--title="..."` for clear headers
- Include database comments (`COMMENT ON ...`) — SchemaCrawler automatically includes them

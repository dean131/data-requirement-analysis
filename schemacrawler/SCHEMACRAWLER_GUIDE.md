# SchemaCrawler User Guide

### _Comprehensive Guide for Generating Database Documentation, Data Dictionaries, and ER Diagrams_

---

## Table of Contents

1. [Introduction](#10-introduction)  
2. [Prerequisites](#20-prerequisites)  
3. [Initial Setup](#30-initial-setup)  
4. [Connection Parameters](#40-connection-parameters)  
5. [Output Format Options](#50-output-format-options)  
6. [Standard Documentation Commands](#60-standard-documentation-commands)  
&nbsp;&nbsp;&nbsp;&nbsp;6.1 [`--command=details`](#61---commanddetails)  
&nbsp;&nbsp;&nbsp;&nbsp;6.2 [`--command=schema`](#62---commandschema)  
&nbsp;&nbsp;&nbsp;&nbsp;6.3 [`--command=list`](#63---commandlist)  
&nbsp;&nbsp;&nbsp;&nbsp;6.4 [`--command=count`](#64---commandcount)  
&nbsp;&nbsp;&nbsp;&nbsp;6.5 [`--command=brief`](#65---commandbrief)  
7. [Advanced Analysis Commands](#70-advanced-analysis-commands)  
&nbsp;&nbsp;&nbsp;&nbsp;7.1 [`--command=lint`](#71---commandlint)  
&nbsp;&nbsp;&nbsp;&nbsp;7.2 [`--command=serialize`](#72---commandserialize)  
&nbsp;&nbsp;&nbsp;&nbsp;7.3 [`--command=grep`](#73---commandgrep)  
8. [Customization and Advanced Features](#80-customization-and-advanced-features)  
&nbsp;&nbsp;&nbsp;&nbsp;8.1 [Result Filtering](#81-result-filtering)  
&nbsp;&nbsp;&nbsp;&nbsp;8.2 [Custom Annotations (Data Dictionary)](#82-custom-annotations-data-dictionary)  
&nbsp;&nbsp;&nbsp;&nbsp;8.3 [Configuring Information Levels](#83-configuring-information-levels)  
&nbsp;&nbsp;&nbsp;&nbsp;8.4 [Adding Custom Titles](#84-adding-custom-titles)  
&nbsp;&nbsp;&nbsp;&nbsp;8.5 [Loading External Configuration Files](#85-loading-external-configuration-files)  
9. [Case Study: Complete Usage Example](#90-case-study-complete-usage-example)  
&nbsp;&nbsp;&nbsp;&nbsp;9.1 [Scenario and Prerequisites](#91-scenario-and-prerequisites)  
&nbsp;&nbsp;&nbsp;&nbsp;9.2 [Full Execution Command](#92-full-execution-command)  
&nbsp;&nbsp;&nbsp;&nbsp;9.3 [Result Analysis](#93-result-analysis)  
10. [Command Summary](#100-command-summary)  
11. [Best Practices Recommendations](#110-best-practices-recommendations)  

---

## 1.0 Introduction

**SchemaCrawler** is an open-source, Java-based utility designed to analyze, visualize, and document database schemas. It connects to an existing database and exports professional documentation in various formats, including **HTML**, **PDF**, **Markdown**, **plain text**, or **JSON**.

Its core functionalities include generating:

- Detailed **Data Dictionaries**  
- **Entity-Relationship Diagrams (ERDs)**  
- **Schema Summaries**  
- Row counts, statistics, and design analysis  

---

## 2.0 Prerequisites

Before proceeding, ensure your system meets the following requirements:

- **Docker:** Docker environment must be installed and running.  
- **Database Access:** Credentials and connectivity details for the target database (MySQL, PostgreSQL, etc.).  
- **Directory Structure:** A local project directory to store output and configuration files.  

---

## 3.0 Initial Setup

It is recommended to set up a local directory structure to efficiently manage input and output files.

Inside your project directory, run the following commands:

```bash
# Create output directory (for results)
mkdir -p output

# Create directory for JDBC drivers (.jar files)
mkdir -p drivers

# Create a custom annotation file
touch dictionary.yaml

# Create an optional configuration file
touch schemacrawler.config.properties
```

Next, start an interactive Docker container session. The following `docker run` command mounts all required directories and files into the container:

```bash
docker run \
  -v $(pwd)/output:/home/schcrwlr/share \
  -v $(pwd)/drivers:/home/schcrwlr/drivers \
  -v $(pwd)/dictionary.yaml:/home/schcrwlr/dictionary.yaml \
  -v $(pwd)/schemacrawler.config.properties:/home/schcrwlr/schemacrawler.config.properties \
  --rm -it \
  --entrypoint=/bin/bash \
  schemacrawler/schemacrawler
```

After execution, you will be inside the container shell:

```
schcrwlr@container:/home/schcrwlr$
```

---

## 4.0 Connection Parameters

Every SchemaCrawler execution requires database connection parameters. Below are the most fundamental options:

| Option                    | Example                            | Description                                                  |
| :------------------------ | :--------------------------------- | :----------------------------------------------------------- |
| `--server`                | `mysql`                            | Specifies the database server type.                          |
| `--database`              | `terafarma_clone`                  | Name of the database (schema) to analyze.                    |
| `--host`                  | `172.17.0.1`                       | Host IP address. (Use Docker bridge IP if connecting to localhost.) |
| `--port`                  | `3306`                             | Database connection port.                                    |
| `--user`                  | `root`                             | Username for authentication.                                 |
| `--password`              | `root_password`                    | Password for authentication.                                 |
| `--drivers`               | `/home/schcrwlr/drivers/mysql.jar` | (Optional) Path to custom JDBC driver file.                  |
| `--connection-properties` | `sslmode=require`                  | (Optional) Additional JDBC driver parameters.                |

---

## 5.0 Output Format Options

Use the `--output-format` parameter to specify the output file format.

| Format     | Description                                     | Example Flag                |
| :--------- | :---------------------------------------------- | :-------------------------- |
| `html`     | Generates a clean, interactive document.        | `--output-format=html`      |
| `pdf`      | Produces a portable PDF file.                   | `--output-format=pdf`       |
| `markdown` | Plain-text format ideal for Git repositories.   | `--output-format=markdown`  |
| `text`     | Plain text output, suitable for terminals.      | `--output-format=text`      |
| `json`     | Structured, machine-readable format.            | `--output-format=json`      |

**Note:** Output files must always be saved under `/home/schcrwlr/share/`, which is mapped to your local `./output/` directory.

---

## 6.0 Standard Documentation Commands

SchemaCrawler’s functionality is determined by the `--command` option. This section covers commands focused on human-readable documentation.

---

### 6.1 `--command=details`

Generates a detailed data dictionary listing all tables, columns, constraints, and descriptions.

**Example:**

```bash
schemacrawler ... (connection parameters) ... \
  --info-level=maximum \
  --command=details \
  --title="TeraFarma Data Dictionary" \
  --output-format=html \
  --output-file="/home/schcrwlr/share/data_dictionary.html"
```

---

### 6.2 `--command=schema`

Generates a graphical diagram visualizing table relationships.

**Example:**

```bash
schemacrawler ... (connection parameters) ... \
  --command=schema \
  --info-level=standard \
  --title="TeraFarma ER Diagram" \
  --output-format=pdf \
  --output-file="/home/schcrwlr/share/er_diagram.pdf"
```

---

### 6.3 `--command=list`

Produces a concise list of all objects (tables, views, routines, etc.) in the schema.

**Example:**

```bash
schemacrawler ... (connection parameters) ... \
  --command=list \
  --info-level=standard \
  --output-format=text \
  --output-file="/home/schcrwlr/share/schema_list.txt"
```

---

### 6.4 `--command=count`

Displays the number of rows in each table (requires database support).

**Example:**

```bash
schemacrawler ... (connection parameters) ... \
  --command=count \
  --output-format=text \
  --output-file="/home/schcrwlr/share/table_counts.txt"
```

---

### 6.5 `--command=brief`

Generates a brief schema overview (ideal for quick reviews).

**Example:**

```bash
schemacrawler ... (connection parameters) ... \
  --command=brief \
  --info-level=standard \
  --output-format=text \
  --output-file="/home/schcrwlr/share/schema_brief.txt"
```

---

## 7.0 Advanced Analysis Commands

These commands enable deeper schema analysis and machine-readable outputs.

---

### 7.1 `--command=lint`

Analyzes the schema against best practices to identify potential design issues (e.g., tables without primary keys, inconsistent naming).

**Example:**

```bash
schemacrawler ... (connection parameters) ... \
  --command=lint \
  --output-format=text \
  --output-file="/home/schcrwlr/share/lint_report.txt"
```

---

### 7.2 `--command=serialize`

Exports the entire schema catalog into a structured data file (JSON or YAML). Ideal for processing by scripts or other analysis tools.

**Example:**

```bash
schemacrawler ... (connection parameters) ... \
  --info-level=maximum \
  --command=serialize \
  --output-format=json \
  --output-file="/home/schcrwlr/share/schema_dump.json"
```

---

### 7.3 `--command=grep`

Searches for database objects (tables, columns) using regular expressions or keywords.

**Example:**

```bash
schemacrawler ... (connection parameters) ... \
  --command=grep \
  --grep-tables=.*customer.* \
  --output-format=text \
  --output-file="/home/schcrwlr/share/grep_customer.txt"
```

---

## 8.0 Customization and Advanced Features

The following features allow deep customization of output.

---

### 8.1 Result Filtering

Control which database objects are included or excluded. Essential for large databases containing irrelevant tables.

| Option               | Example                | Description                                         |
| :------------------- | :--------------------- | :-------------------------------------------------- |
| `--include-tables`   | `users.*\|products.*`  | **Only** processes tables matching the regex.       |
| `--exclude-tables`   | `.*log.*\|.*backup.*`  | **Excludes** all tables matching the regex.         |

**Example (Include only 'users' and 'orders' tables):**

```bash
schemacrawler ... (connection parameters) ... \
  --command=details \
  --include-tables=users|orders \
  --output-file="/home/schcrwlr/share/user_order_docs.html"
```

---

### 8.2 Custom Annotations (Data Dictionary)

This feature allows users to add business-contextual descriptions to tables and columns—crucial for effective data mapping.

**Example `dictionary.yaml` file:**

```yaml
catalog:
  schemas:
    - name: terafarma_clone
      tables:
        - name: users
          remarks: "Stores primary customer login information."
          columns:
            - name: user_id
              remarks: "Primary key. Used as a reference in other databases."
```

**Example command (loading custom dictionary):**

```bash
schemacrawler ... (connection parameters) ... \
  --command=details \
  # Load data dictionary extension
  --load-extension=schemacrawler.tools.databaseconnector.extension.data.dictionary \
  # Reference mounted file from Step 3.0
  --attributes-file=/home/schcrwlr/dictionary.yaml \
  --output-file="/home/schcrwlr/share/annotated_docs.html"
```

---

### 8.3 Configuring Information Levels

Controls the depth of metadata extracted. Higher levels include all information from lower levels.

| Level      | Description                                                                                                          |
| :--------- | :------------------------------------------------------------------------------------------------------------------- |
| `minimum`  | Includes only tables and columns.                                                                                    |
| `standard` | `minimum` + Primary Keys, Foreign Keys, and Constraints.                                                             |
| `detailed` | `standard` + Indexes, Column Default Values, and Remarks.                                                            |
| `maximum`  | `detailed` + **All metadata**, including Triggers, Routines (Procedures/Functions), and Check Constraints.             |

**Example:**

```bash
--info-level=maximum
```

---

### 8.4 Adding Custom Titles

Adds a custom title to the output header (applies to HTML, PDF, Markdown).

```bash
--title="TeraFarma Database Documentation"
```

---

### 8.5 Loading External Configuration Files

Loads a `schemacrawler.config.properties` file (mounted in Step 3.0) to apply custom formatting settings.

**Example `schemacrawler.config.properties` file:**

```properties
schemacrawler.formatting.text.alignment=left
schemacrawler.formatting.text.line.width=120
schemacrawler.formatting.header.underline=true
schemacrawler.formatting.text.show.unicode=false
```

**Example command (loading config file):**

```bash
schemacrawler ... (connection parameters) ... \
  --command=details \
  --load-config=/home/schcrwlr/schemacrawler.config.properties \
  --output-format=text \
  --output-file="/home/schcrwlr/share/formatted_output.txt"
```

---

## 9.0 Case Study: Complete Usage Example

This section demonstrates a real-world scenario that combines multiple advanced features to generate a highly specific report.

### 9.1 Scenario and Prerequisites

**Objective:** Generate an annotated, business-friendly **HTML Data Dictionary** for the **business team**. The report must:

1. Include **only** the `users` and `orders` tables.  
2. Exclude all other tables, especially those matching `_log` or `_backup`.  
3. Display custom business descriptions from the `dictionary.yaml` file.  
4. Include the most comprehensive information possible (`maximum` info level).

**Prerequisite File (Local):**  
Ensure your local `dictionary.yaml` (mounted to `/home/schcrwlr/dictionary.yaml`) contains the following annotations:

```yaml
# dictionary.yaml
catalog:
  schemas:
    - name: terafarma_clone
      tables:
        - name: users
          remarks: "Master table for all user and customer data."
          columns:
            - name: user_id
              remarks: "Unique primary key. Used as a reference in other databases."
            - name: created_at
              remarks: "Timestamp indicating when the user registered."
        - name: orders
          remarks: "Records all sales transactions."
          columns:
            - name: order_id
              remarks: "Primary key for orders."
            - name: user_id
              remarks: "Logical foreign key referencing the 'users' table."
```

### 9.2 Full Execution Command

Run the following command inside your Docker container shell. This single command combines connection, filtering, annotation, and output customization:

```bash
schemacrawler \
  # 1. Connection Parameters
  --server=mysql \
  --database=terafarma_clone \
  --host=172.17.0.1 \
  --port=3306 \
  --user=root \
  --password=root_password \
  \
  # 2. Command & Information Level
  --command=details \
  --info-level=maximum \
  \
  # 3. Custom Annotations (Section 8.2)
  --load-extension=schemacrawler.tools.databaseconnector.extension.data.dictionary \
  --attributes-file=/home/schcrwlr/dictionary.yaml \
  \
  # 4. Filtering (Section 8.1)
  --include-tables=users|orders \
  \
  # 5. Output Customization & Title
  --title="Business Data Dictionary (Users & Orders)" \
  --output-format=html \
  --output-file="/home/schcrwlr/share/business_data_dictionary.html"
```

### 9.3 Result Analysis

After the command completes, check your local `./output/` directory. You will find the file `business_data_dictionary.html`.

When opened in a web browser, the report will show:

- **Custom Title:** The report header displays “Business Data Dictionary (Users & Orders)”.  
- **Filtered Output:** The report includes **only** the `users` and `orders` tables.  
- **Custom Annotations:** The “Remarks” (descriptions) for both tables and their columns reflect the business context you defined in `dictionary.yaml`, rather than (or in addition to) any technical comments from the database.

This output is ideal for sharing with non-technical stakeholders, such as product managers or business analysts, who need to understand data semantics without diving into technical schema details.

---

## 10.0 Command Summary

| Use Case               | Command               | Example Output         |
| :--------------------- | :-------------------- | :--------------------- |
| Full Data Dictionary   | `--command=details`   | `data_dictionary.html` |
| ER Diagram             | `--command=schema`    | `er_diagram.pdf`       |
| Schema Object List     | `--command=list`      | `schema_list.txt`      |
| Row Count              | `--command=count`     | `table_counts.txt`     |
| Brief Summary          | `--command=brief`     | `schema_brief.txt`     |
| Object Search          | `--command=grep`      | `grep_customer.txt`    |
| Design Analysis        | `--command=lint`      | `lint_report.txt`      |
| Machine-Readable Dump  | `--command=serialize` | `schema_dump.json`     |

---

## 11.0 Best Practices Recommendations

- **Output Location:** Always save output files to `/home/schcrwlr/share/` so they appear in your local `./output/` directory.  
- **Data Completeness:** Use `--info-level=maximum` when creating data dumps (e.g., with `serialize`) to ensure no metadata is omitted.  
- **Business Context:** Leverage Custom Annotations (Section 8.2) to enrich technical documentation with business logic.  
- **Focused Analysis:** Use Filtering parameters (Section 8.1) to ignore irrelevant tables (logs, backups) and focus on core data.  
- **Database Comments:** SchemaCrawler automatically includes existing database comments (`COMMENT ON ...`). Utilize this feature at the database level whenever possible.  


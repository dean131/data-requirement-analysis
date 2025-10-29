# **Data Analysis & Mapping Workflow for Existing Databases**

## **Purpose**

This workflow helps you analyze existing databases and determine which data is required for new or updated application features — even when there is little to no documentation available.
It focuses on **open-source tools** that can be used locally and safely with cloned copies of production databases.

---

## **Overview**

When a client wants to extend an existing system, you often receive database access but little documentation.
Your goal is to identify **which tables and columns** are used or needed for each feature.

This workflow will help you:

1. Extract and document database structure automatically.
2. Visualize table relationships (ERD).
3. Catalog and explore metadata across multiple databases.
4. Analyze data quality and content.
5. Map features to data sources clearly.

---

## ⚙️ **Recommended Toolchain**

| Purpose                                    | Tool                       | Type           | Output                         |
| ------------------------------------------ | -------------------------- | -------------- | ------------------------------ |
| Reverse engineering & schema documentation | **SchemaCrawler**          | CLI            | PDF / HTML structure report    |
| Visualize ER diagrams                      | **DbGate**                 | GUI            | ERD (PNG/SVG)                  |
| Metadata catalog & search                  | **OpenMetadata**           | Web App        | Centralized searchable catalog |
| Data profiling & quality report            | **YData Profiling**        | Python library | HTML report                    |
| Feature-to-data mapping                    | **Markdown / Spreadsheet** | Manual         | Traceability table             |

---

## 🧩 **Step-by-Step Workflow**

### **Step 1 — Clone and Set Up Local Databases**

**Goal:** Work with safe, local copies of production databases.

**Actions:**

1. Export each database using `mysqldump`, `pg_dump`, or similar tools.
2. Restore them locally using Docker for easy management.

**Example (MySQL via Docker Compose):**

```yaml
services:
  db_a:
    image: mysql:8
    container_name: db_a
    environment:
      MYSQL_ROOT_PASSWORD: root
    volumes:
      - ./db_a_dump.sql:/docker-entrypoint-initdb.d/db_a_dump.sql
    ports:
      - 3307:3306
```

✅ _Now you can connect each database locally without affecting production._

---

### **Step 2 — Auto-Generate Schema Documentation**

**Tool:** [SchemaCrawler](https://www.schemacrawler.com/)
**Goal:** Automatically extract tables, columns, and relationships into a human-readable format.

**Run:**

```bash
schemacrawler --server=mysql --database=db_a --user=root --password=root \
  --info-level=standard --output-format=pdf --output-file=db_a_schema.pdf
```

**Output:**

- PDF/HTML file with database structure
- List of all tables, columns, primary/foreign keys

📘 _SchemaCrawler helps you understand how existing data is organized._

---

### **Step 3 — Visualize Entity Relationships (ERD)**

**Tool:** [DbGate](https://dbgate.org/)
**Goal:** Quickly see how tables connect visually.

**Actions:**

1. Open DbGate (desktop or web).
2. Connect to your local database.
3. Use **ER Diagram → Auto Layout** to generate diagrams.
4. Export ERDs as PNG or SVG.

🖼️ _This makes it easier to communicate data structure to your team._

---

### **Step 4 — Centralize Metadata in a Catalog**

**Tool:** [OpenMetadata](https://open-metadata.org/)
**Goal:** Create a unified, searchable metadata repository for all databases.

**Setup:**

1. Deploy OpenMetadata locally via Docker Compose.
2. Add connection configurations for each of your 6 databases.
3. Run metadata ingestion:

   ```bash
   metadata ingest -c ./ingestion/mysql_db_a.yaml
   ```

**Result:**

- A central dashboard showing all tables, columns, and relationships.
- You can add business context tags (e.g., `feature_sales`, `feature_inventory`).

📘 _This step transforms your databases into a searchable knowledge base._

---

### **Step 5 — Profile Data for Quality and Content**

**Tool:** [YData Profiling (Pandas Profiling)](https://github.com/ydataai/ydata-profiling)
**Goal:** Understand the content and quality of key tables.

**Example in Python:**

```python
from ydata_profiling import ProfileReport
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://root:root@localhost:3307/db_a")
df = pd.read_sql("SELECT * FROM orders LIMIT 10000", engine)

profile = ProfileReport(df, title="Orders Data Profile")
profile.to_file("orders_profile.html")
```

**Output:**

- Interactive HTML report showing:

  - Column data types
  - Null values
  - Data distribution
  - Potential data issues

📊 _This helps verify whether existing data is suitable for new feature requirements._

---

### **Step 6 — Map Features to Data Sources**

**Goal:** Link each new feature to the specific database tables and columns it depends on.

**Tool:** Markdown or spreadsheet.

**Example Table:**

| Feature           | Database    | Table        | Columns Used              | Relationship                    | Notes |
| ----------------- | ----------- | ------------ | ------------------------- | ------------------------------- | ----- |
| Payment Feature   | db_sales    | users        | id, name, email           |                                 |       |
| Payment Feature   | db_finance  | transactions | id, user_id, total_amount | users.id = transactions.user_id |       |
| Inventory Feature | db_products | items        | item_id, stock            |                                 |       |

📘 _This mapping is crucial for developers and stakeholders to understand dependencies._

---

### **Step 7 — Create Final Documentation Repository**

**Goal:** Combine all findings into a version-controlled documentation folder.

**Suggested structure:**

```
data-analysis/
├── 1_schemas/
│   ├── db_a_schema.pdf
│   ├── db_b_schema.pdf
├── 2_erd/
│   ├── db_a_erd.png
│   ├── db_b_erd.png
├── 3_profiles/
│   ├── orders_profile.html
│   ├── users_profile.html
├── 4_feature_mapping.md
└── README.md
```

Use Git to track updates and share findings with the team.

---

## ✅ **Final Output**

By the end of this workflow, you will have:

- 📚 Comprehensive documentation of all existing databases
- 🧩 ER diagrams showing data relationships
- 🔎 Centralized metadata catalog (OpenMetadata)
- 📈 Data quality and profiling reports
- 🗂️ Clear mapping of features to database sources

---

## 💡 **Pro Tips**

- Run SchemaCrawler and profiling regularly as databases evolve.
- Use OpenMetadata tags to mark datasets relevant to each business feature.
- Keep your Markdown/feature mapping versioned in Git alongside your codebase.
- If a new feature is proposed, use OpenMetadata search + profiling reports to quickly identify which tables may contain the necessary data.

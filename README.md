# Delivery Analyzer - 上海好吃米道

A Streamlit web application built for a small Chinese food delivery business, 上海好吃米道.

The app processes food orders exported from WeChat by parsing raw export files, extracting item quantities for each order, validating totals against WeChat’s built-in summary table, and generating structured reports along with downloadable CSV files.

## Features

- **Raw WeChat export support** — reads the native `.xlsx` export format directly, no manual formatting needed
- **Summary table validation** — after parsing, automatically cross-checks item totals against the WeChat summary table and surfaces any discrepancies
- **Secure access** — password-protected with dual auth (Streamlit secrets for cloud, `config.json` for local)
- **Interactive order selection** — select individual orders or use Select All / Clear All
- **Analysis and export** — generates item quantity reports, bar charts, and downloadable CSV/text exports
- **Label generation** — generates Avery 5167 label sheets as a downloadable PDF (one label per item ordered, showing item ID and short Chinese name)

## Installation

### Prerequisites

- Python 3.7+
- `make` (pre-installed on macOS)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd delivery-analyzer
```

2. Create a virtual environment and install dependencies:
```bash
make install
```

3. Configure authentication.

   **For local development** — create `config.json` in the project root:
   ```json
   { "password": "your_password" }
   ```

   **For Streamlit Cloud** — add to your app's secrets in the dashboard:
   ```toml
   password = "your_password"
   ```

## Usage

```bash
make run
```

Then open `http://localhost:8501` in your browser.

1. **Login** — enter the configured password
2. **Upload** — drag and drop a raw WeChat export `.xlsx` file onto the main page
3. **Process** — click "Process" to parse and load the orders
4. **Select** — check the orders you want to include in the analysis
5. **Analyze** — click "Analyze Selected Orders" to generate the report
6. **Export** — download results as CSV or a text report
7. **Labels** — switch to the Labels tab to download an Avery 5167 label PDF

## Input File Format

The app expects a **raw WeChat export** `.xlsx` file with the following structure:

- **Rows 0–2**: WeChat metadata (ignored)
- **Row 3**: Column headers — `序号, 姓名, 内容, 标签, 手机号码, 收货地址, 所在城市, 邮政编码`
- **Rows 4–N**: Customer order records
- **Below orders**: Summary table (`商品汇总`) — automatically excluded from order parsing and used for validation

Column mapping:

| Column | Chinese | Meaning |
|--------|---------|---------|
| 0 | 序号 | Sequence number |
| 1 | 姓名 | Customer name |
| 2 | 内容 | Items ordered |
| 3 | 标签 | Tags (dropped) |
| 4 | 手机号码 | Phone number |
| 5 | 收货地址 | Delivery address |
| 6 | 所在城市 | City |
| 7 | 邮政编码 | ZIP code |

### Items Text Format

Each order's items text is Chinese comma-separated (`， `) with `x` quantity notation, ending with a total price segment that is dropped during parsing:

```
肉末香茹胡罗卜糯米烧卖 15个/份x3， 荠菜鲜肉馄饨 50/份x2， 总价：$100.00
```

## Menu Reference (`data/menu.csv`)

The parser matches order items against `data/menu.csv`, which is the authoritative list of available food items. Update this file manually when new items are added.

| Column | Description |
|--------|-------------|
| `id` | Auto-incremented integer ID |
| `item_zh` | Full Chinese name with unit spec (e.g. `肉末香茹胡罗卜糯米烧卖15个/份`) |
| `item_short_zh` | Shortened Chinese name (e.g. `烧卖`) |
| `item_en` | Hanyu pinyin of short name (e.g. `shao mai`) |

# Architecture — 上海好吃米道

## Overview

A single-service Streamlit web application. All business logic is isolated in `analyzer.py` (pure Python, no Streamlit imports). The UI layer in `app.py` handles rendering and user interaction only. This separation makes the core logic portable to a different frontend stack in the future.

```
┌─────────────────────────────────────────┐
│               app.py (UI)               │
│  Auth · Upload · Order Selection ·      │
│  Analysis Display · Warnings            │
└────────────────┬────────────────────────┘
                 │ imports
┌────────────────▼────────────────────────┐
│           analyzer.py (Logic)           │
│  load_food_items · process_excel ·      │
│  read_summary_table ·                   │
│  validate_against_summary ·             │
│  DeliveryOrderAnalyzer                  │
└────────────────┬────────────────────────┘
                 │ reads
┌────────────────▼────────────────────────┐
│           data/menu.csv                 │
│  id · item_zh · item_short_zh · item_en │
└─────────────────────────────────────────┘
```

---

## File Structure

```
food-delivery/
├── app.py                      # Streamlit UI entry point
├── analyzer.py                 # Business logic (no Streamlit)
├── requirements.txt            # Python dependencies
├── Makefile                    # make install / make run
├── .streamlit/
│   └── config.toml             # Theme (colors, font)
└── data/
    └── menu.csv                # Food item reference database
```

---

## Data Flow

```
User uploads .xlsx
       │
       ▼
read_summary_table()
  └─ Extracts 商品汇总 table → {item_name: expected_qty}
       │
       ▼ (file seeked back to 0)
process_excel()
  ├─ pd.read_excel(skiprows=3, usecols=[0,1,2,4,5,6,7])
  ├─ Coerce 序号 to numeric → NaN for summary rows → dropna
  ├─ Type cleanup: delivery→int, phone/zip→str
  ├─ Validate: raise ValueError if 0 orders found
  ├─ Parsing loop: split items text, match against menu.csv
  └─ validate_against_summary() → discrepancies list
       │
       ▼
(df, discrepancies) stored in st.session_state
       │
       ▼
DeliveryOrderAnalyzer.load(df)
  └─ Identifies food columns: df.columns[7:] with Chinese chars
       │
       ▼
User selects orders → analyze(selected_indices)
  └─ Sums food columns for selected rows → sorted results
```

---

## Key Components

### `process_excel(excel_file, food_items) → (DataFrame, discrepancies)`

Reads a raw WeChat export `.xlsx` file. Returns a DataFrame where:
- Columns 0–6: order metadata (`delivery`, `customer`, `items_ordered`, `phone_number`, `address`, `city`, `zip_code`)
- Columns 7+: one column per food item from `menu.csv`, values are quantities (int)

Also returns a list of `(food_item, parsed_total, expected_total)` tuples for any mismatches against the WeChat summary table.

### `read_summary_table(excel_file) → dict`

Locates the `商品汇总` section by finding the row where `序号 == '商品'`. Extracts item names and total quantities up to the `总计` row. Used as ground truth to validate parser output.

### `validate_against_summary(df, food_items, summary_dict) → list`

For each food item in `menu.csv`, compares the sum of its column in the parsed DataFrame against the expected quantity from the summary table. Returns discrepancies only — items absent from the summary table (not ordered that batch) are skipped.

### `DeliveryOrderAnalyzer`

Loaded with the processed DataFrame. `analyze(selected_indices)` sums food item columns for the selected rows and returns results sorted by quantity descending.

---

## Menu Database (`data/menu.csv`)

The reference list of available food items. Committed to the repo. Updated manually when new items are added to the WeChat ordering system.

| Column | Description | Example |
|--------|-------------|---------|
| `id` | Auto-incremented integer | `1` |
| `item_zh` | Full Chinese name with unit spec | `肉末香茹胡罗卜糯米烧卖15个/份` |
| `item_short_zh` | Shortened Chinese name | `烧卖` |
| `item_en` | Hanyu pinyin of short name | `shao mai` |

`item_zh` is used for parser matching. `item_short_zh` and `item_en` are available for future UI use (e.g. bilingual display).

---

## Item Parsing Logic

Order text format from WeChat:
```
肉末香茹胡罗卜糯米烧卖 15个/份x3， 荠菜鲜肉馄饨 50/份x2， 总价：$100.00
```

Steps:
1. Split by `， ` (Chinese comma + space)
2. Drop last segment (total price)
3. For each entry, `rsplit('x', 1)` to get item name and quantity
4. Match item name against `item_zh` values using normalized base names — unit specs stripped via `\d+个?[/／]?份?$`, whitespace removed
5. Items not matched against `menu.csv` are silently dropped

---

## Authentication

Dual-mode password auth:
1. **Streamlit Cloud** — reads from `st.secrets["password"]`
2. **Local development** — reads from `config.json`

Password comparison uses `hmac.compare_digest()` for timing-safe comparison.

---

## Theme

Configured in `.streamlit/config.toml`. Warm pink/rose palette:

| Token | Value | Role |
|-------|-------|------|
| `primaryColor` | `#C0575A` | Buttons, highlights |
| `backgroundColor` | `#FDF6F0` | Main background |
| `secondaryBackgroundColor` | `#F5E6E8` | Sidebar, cards |
| `textColor` | `#3D2C2C` | Body text |
| `font` | `serif` | All text |


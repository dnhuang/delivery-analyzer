import pandas as pd
import re
from typing import List, Tuple


def load_food_items(path: str = 'data/food_items.csv') -> List[str]:
    """Load food items from CSV. Raises on failure."""
    food_df = pd.read_csv(path)
    return food_df['food_items'].tolist()


def process_excel(excel_file, food_items: List[str]) -> pd.DataFrame:
    """
    Process an uploaded Excel file into a DataFrame with food item quantity columns.
    Raises ValueError on bad input structure.
    """
    df = pd.read_excel(excel_file, skiprows=3, usecols=[0, 1, 2, 4, 5, 6, 7])
    df = df.dropna(how='all')

    if len(df.columns) < 7:
        raise ValueError(f"Expected at least 7 columns, got {len(df.columns)}")

    df = df.rename(columns={
        df.columns[0]: 'delivery',       # 序号  (sequence number)
        df.columns[1]: 'customer',       # 姓名  (customer name)
        df.columns[2]: 'items_ordered',  # 内容  (items text)
        df.columns[3]: 'phone_number',   # 手机号码
        df.columns[4]: 'address',        # 收货地址
        df.columns[5]: 'city',           # 所在城市
        df.columns[6]: 'zip_code',       # 邮政编码
    })
    df['delivery'] = pd.to_numeric(df['delivery'], errors='coerce') # causes bottom summary table to be NaN
    df = df.dropna(subset=['delivery', 'customer']).reset_index(drop=True) # bottom summary table gets dropped
    df['delivery'] = df['delivery'].astype(int)
    df['phone_number'] = df['phone_number'].apply(lambda x: str(int(x)) if pd.notna(x) else '')
    df['zip_code'] = df['zip_code'].apply(lambda x: str(int(x)) if pd.notna(x) else '')


    for food_item in food_items:
        df[food_item] = 0

    for idx, row in df.iterrows():
        items_text = str(row['items_ordered'])
        if items_text == 'nan':
            continue

        items_list = items_text.split('， ')
        if len(items_list) > 1:
            items_list = items_list[:-1]

        for item_entry in items_list:
            item_entry = item_entry.strip()
            if not item_entry or 'x' not in item_entry:
                continue

            parts = item_entry.rsplit('x', 1)
            if len(parts) != 2:
                continue

            item_name_part = parts[0].strip()
            quantity_match = re.match(r'(\d+)', parts[1].strip())
            if not quantity_match:
                continue

            quantity = int(quantity_match.group(1))

            for food_item in food_items:
                base_name = re.sub(r'\d+个?[/／]?份?$', '', food_item).strip()
                item_name_norm = item_name_part.replace(' ', '')
                base_name_norm = base_name.replace(' ', '')

                if (base_name in item_name_part or item_name_part in base_name or
                        base_name_norm in item_name_norm or item_name_norm in base_name_norm):
                    df.at[idx, food_item] = quantity
                    break

    return df


class DeliveryOrderAnalyzer:
    def __init__(self):
        self.df = None
        self.food_columns: List[str] = []

    def load(self, df: pd.DataFrame) -> None:
        """Load data from a processed DataFrame."""
        self.df = df
        self.food_columns = [
            col for col in df.columns[7:]
            if re.search(r'[\u4e00-\u9fff]', col)
        ]

    def analyze(self, selected_indices: List[int]) -> Tuple[List[Tuple[str, int]], int]:
        """Return (sorted item totals, grand total) for selected order indices."""
        if not selected_indices or self.df is None:
            return [], 0

        selected_df = self.df.iloc[selected_indices]
        item_totals = {
            col: int(selected_df[col].sum())
            for col in self.food_columns
            if selected_df[col].sum() > 0
        }
        sorted_items = sorted(item_totals.items(), key=lambda x: x[1], reverse=True)
        return sorted_items, sum(item_totals.values())

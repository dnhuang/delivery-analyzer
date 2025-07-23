#!/usr/bin/env python3
"""
Delivery Order Analyzer - Enhanced Secure Web Version
Streamlit-based GUI with password protection and Excel file upload functionality.
"""

import streamlit as st
import pandas as pd
import re
import hashlib
import json
import io
from typing import Dict, List, Tuple

def load_config():
    """Load configuration from Streamlit secrets or config.json file."""
    # Try Streamlit secrets first (for deployment)
    try:
        if hasattr(st, 'secrets') and 'password' in st.secrets:
            return {"password": st.secrets["password"]}
    except Exception:
        pass
    
    # Fallback to config.json file (for local development)
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ Configuration not found! Please set up password in Streamlit secrets or ensure config.json exists.")
        st.info("💡 **For deployment**: Add password to Streamlit Cloud secrets")
        st.info("💡 **For local development**: Ensure config.json file exists")
        return None
    except Exception as e:
        st.error(f"Error loading config: {str(e)}")
        return None

def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        config = load_config()
        if config is None:
            st.session_state["password_correct"] = False
            return
            
        correct_password = config.get("password", "")
        
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.title("🔐 Delivery Order Analyzer - Access Required")
        st.info("Please enter the password to access the application.")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.markdown("---")
        st.markdown("**Contact administrator for access credentials.**")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.title("🔐 Delivery Order Analyzer - Access Required")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect. Please try again.")
        return False
    else:
        # Password correct.
        return True

def load_food_items():
    """Load the list of food items from food_items.csv"""
    try:
        food_df = pd.read_csv('food_items.csv')
        return food_df['food_items'].tolist()
    except FileNotFoundError:
        st.error("food_items.csv not found! Please ensure the file exists.")
        return []
    except Exception as e:
        st.error(f"Error loading food items: {str(e)}")
        return []

def process_excel_to_csv(excel_file):
    """
    Process uploaded Excel file and convert it to the required CSV format
    following the data processing steps from eda.ipynb
    """
    try:
        # Read Excel file
        df = pd.read_excel(excel_file, skiprows=3, usecols=[i for i in range(1, 8)])
        
        # Drop any rows that are completely empty
        df = df.dropna(how='all')
        
        # Load food items list
        food_items = load_food_items()
        
        if not food_items:
            st.error("Could not load food items list")
            return None
        
        # Rename columns to match expected format
        column_mapping = {
            df.columns[0]: 'delivery',
            df.columns[1]: 'customer',
            df.columns[2]: 'phone_number',
            df.columns[3]: 'address',
            df.columns[4]: 'city',
            df.columns[5]: 'zip_code',
            df.columns[6]: 'items_ordered'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Clean up the data - remove rows with no delivery or customer info
        df = df.dropna(subset=['delivery', 'customer'])
        
        # Reset index after dropping rows
        df = df.reset_index(drop=True)
        
        # Add food item columns with zeros
        for food_item in food_items:
            df[food_item] = 0
        
        # Parse items_ordered column to extract quantities
        for idx, row in df.iterrows():
            items_text = str(row['items_ordered'])
            
            # Skip empty rows
            if pd.isna(items_text) or items_text == 'nan':
                continue
            
            # Parse each food item from the items_ordered text
            for food_item in food_items:
                # Extract base name by removing unit specifications
                # Remove common unit patterns like "15个/份", "50/份", "3个／份", etc.
                base_name = re.sub(r'\d+个?[/／]?份?$', '', food_item).strip()
                
                # Look for patterns like "base_name ... x数量" in the text
                # The key insight is to match the base name, then look for x followed by quantity
                patterns = [
                    f"{re.escape(base_name)}.*?x(\\d+)",
                    f"{re.escape(base_name)}.*?×(\\d+)"
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, items_text)
                    if match:
                        quantity = int(match.group(1))
                        df.at[idx, food_item] = quantity
                        break
        
        return df
        
    except Exception as e:
        st.error(f"Error processing Excel file: {str(e)}")
        return None

class DeliveryOrderAnalyzer:
    def __init__(self):
        self.df = None
        self.chinese_columns = []
        
    def load_data_from_csv(self):
        """Load and process the CSV data"""
        try:
            self.df = pd.read_csv('data.csv')
            self._identify_chinese_columns()
            return True
            
        except FileNotFoundError:
            return False
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return False
    
    def load_data_from_dataframe(self, df):
        """Load data from a processed DataFrame"""
        self.df = df
        self._identify_chinese_columns()
        return True
    
    def _identify_chinese_columns(self):
        """Identify Chinese columns (food items)"""
        if self.df is not None:
            all_columns = self.df.columns.tolist()
            self.chinese_columns = []
            
            for col in all_columns[7:]:  # Skip first 7 non-food columns
                # Check if column name contains Chinese characters
                if re.search(r'[\u4e00-\u9fff]', col):
                    self.chinese_columns.append(col)
    
    def analyze_selected_orders(self, selected_indices: List[int]) -> Tuple[List[Tuple[str, int]], int]:
        """Analyze selected orders and return item totals"""
        if not selected_indices or self.df is None:
            return [], 0
        
        # Filter dataframe to selected rows
        selected_df = self.df.iloc[selected_indices]
        
        # Calculate totals for each food item
        item_totals = {}
        
        for col in self.chinese_columns:
            total = selected_df[col].sum()
            if total > 0:  # Only include items with quantity > 0
                item_totals[col] = total
        
        # Sort by quantity (descending)
        sorted_items = sorted(item_totals.items(), key=lambda x: x[1], reverse=True)
        total_items = sum(item_totals.values())
        
        return sorted_items, total_items

def main():
    # Check password first
    if not check_password():
        st.stop()
    
    st.set_page_config(
        page_title="Delivery Order Analyzer",
        page_icon="🚚",
        layout="wide"
    )
    
    # Add logout button in sidebar
    with st.sidebar:
        st.markdown("### 👤 Session")
        if st.button("🚪 Logout"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📂 Data Management")
        
        # File upload section
        uploaded_file = st.file_uploader(
            "Upload Excel File",
            type=['xlsx', 'xls'],
            help="Upload your delivery order Excel file to process"
        )
        
        if uploaded_file is not None:
            if st.button("🔄 Process Excel File"):
                with st.spinner("Processing Excel file..."):
                    processed_df = process_excel_to_csv(uploaded_file)
                    if processed_df is not None:
                        # Save to CSV
                        processed_df.to_csv('data.csv', index=False)
                        st.success("Excel file processed and saved as data.csv!")
                        st.session_state['data_uploaded'] = True
                        st.session_state['data_updated'] = True
                        st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("**Delivery Order Analyzer**")
        st.markdown("Version 2.0 - Enhanced")
        st.markdown("Secure access enabled")
        st.markdown("Excel upload supported")
    
    st.title("🚚 Delivery Order Analyzer")
    st.markdown("Upload Excel file or analyze existing delivery order data")
    
    # Initialize analyzer
    analyzer = DeliveryOrderAnalyzer()
    
    # Check if data has been uploaded in this session
    if 'data_uploaded' not in st.session_state:
        st.session_state['data_uploaded'] = False
    
    # Only try to load data if it was uploaded in this session
    data_loaded = False
    if st.session_state.get('data_uploaded', False):
        data_loaded = analyzer.load_data_from_csv()
    
    if not data_loaded:
        st.warning("📋 No data loaded. Please upload an Excel file to get started.")
        st.info("👆 Use the sidebar to upload your delivery order Excel file.")
        
        # Show upload instructions
        st.markdown("### 📤 How to Upload:")
        st.markdown("1. Click on 'Browse files' in the sidebar")
        st.markdown("2. Select your Excel file (.xlsx or .xls)")
        st.markdown("3. Click 'Process Excel File' to convert and load data")
        st.markdown("4. Start analyzing your delivery orders!")
        
        st.stop()
    
    st.success(f"✅ Loaded {len(analyzer.df)} delivery orders with {len(analyzer.chinese_columns)} food items")
    
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📋 Select Orders")
        
        # Add selection controls
        col1a, col1b, col1c = st.columns(3)
        with col1a:
            if st.button("Select All"):
                st.session_state.selected_orders = list(range(len(analyzer.df)))
        with col1b:
            if st.button("Clear All"):
                st.session_state.selected_orders = []
        with col1c:
            show_details = st.checkbox("Show Details", value=False)
        
        # Initialize session state for selections
        if 'selected_orders' not in st.session_state:
            st.session_state.selected_orders = []
        
        # Clear selections if data was updated
        if st.session_state.get('data_updated', False):
            st.session_state.selected_orders = []
            st.session_state['data_updated'] = False
        
        # Create a container for the order list
        order_container = st.container()
        
        with order_container:
            # Display orders with checkboxes
            for idx, row in analyzer.df.iterrows():
                # Count non-zero items for this order
                item_count = sum(1 for col in analyzer.chinese_columns 
                               if pd.notna(row[col]) and row[col] > 0)
                
                # Create checkbox
                order_key = f"order_{idx}"
                is_selected = idx in st.session_state.selected_orders
                
                # Order display text
                order_text = f"{row['delivery']} - {row['customer']} ({row['city']}) - {item_count} items"
                
                # Checkbox
                selected = st.checkbox(order_text, value=is_selected, key=order_key)
                
                # Update session state
                if selected and idx not in st.session_state.selected_orders:
                    st.session_state.selected_orders.append(idx)
                elif not selected and idx in st.session_state.selected_orders:
                    st.session_state.selected_orders.remove(idx)
                
                # Show details if requested
                if show_details and selected:
                    with st.expander(f"Details for {row['customer']}", expanded=False):
                        st.write(f"**Phone:** {row['phone_number']}")
                        st.write(f"**Address:** {row['address']}, {row['city']} {row['zip_code']}")
                        st.write(f"**Items Ordered:** {row['items_ordered']}")
    
    with col2:
        st.header("📊 Analysis Results")
        
        # Show selection count
        selected_count = len(st.session_state.selected_orders)
        st.info(f"Selected: {selected_count} orders")
        
        if selected_count > 0:
            # Analyze button
            if st.button("🔍 Analyze Selected Orders", type="primary"):
                # Perform analysis
                sorted_items, total_items = analyzer.analyze_selected_orders(st.session_state.selected_orders)
                
                if sorted_items:
                    st.success(f"Analysis complete! Found {len(sorted_items)} unique items, {total_items} total items")
                    
                    # Display results in tabs
                    tab1, tab2, tab3 = st.tabs(["📈 Summary", "📋 Item List", "📄 Detailed Report"])
                    
                    with tab1:
                        st.subheader("Summary")
                        
                        # Create summary metrics
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Orders Analyzed", selected_count)
                        with col_b:
                            st.metric("Unique Items", len(sorted_items))
                        with col_c:
                            st.metric("Total Items", total_items)
                        
                        # Create a bar chart
                        if sorted_items:
                            df_chart = pd.DataFrame(sorted_items[:10], columns=['Item', 'Quantity'])
                            st.bar_chart(df_chart.set_index('Item'))
                    
                    with tab2:
                        st.subheader("Item Quantities (Sorted by Total)")
                        
                        # Create DataFrame for display
                        df_display = pd.DataFrame(sorted_items, columns=['Food Item', 'Quantity'])
                        df_display.index = range(1, len(df_display) + 1)  # Start index from 1
                        
                        st.dataframe(
                            df_display,
                            use_container_width=True,
                            height=400
                        )
                        
                        # Download button
                        csv = df_display.to_csv(index=False)
                        st.download_button(
                            label="📥 Download as CSV",
                            data=csv,
                            file_name=f"delivery_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with tab3:
                        st.subheader("Detailed Report")
                        
                        # Generate detailed report
                        report = f"""
**DELIVERY ORDER ANALYSIS REPORT**
================================

**Analysis Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
**Orders Analyzed:** {selected_count}
**Unique Items Ordered:** {len(sorted_items)}
**Total Items:** {total_items}

**SELECTED ORDERS:**
"""
                        for idx in st.session_state.selected_orders:
                            row = analyzer.df.iloc[idx]
                            report += f"\n• {row['delivery']} - {row['customer']} ({row['city']})"
                        
                        report += f"\n\n**ITEM QUANTITIES:**"
                        for item_name, quantity in sorted_items:
                            report += f"\n• {item_name}: {quantity}"
                        
                        st.text_area("Report", report, height=400)
                        
                        # Download report
                        st.download_button(
                            label="📥 Download Report",
                            data=report,
                            file_name=f"delivery_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                else:
                    st.warning("No items found in selected orders.")
        else:
            st.info("Select some orders to analyze.")
    
    # Footer
    st.markdown("---")
    st.markdown("**Instructions:** Upload an Excel file using the sidebar, then select delivery orders and click 'Analyze Selected Orders' to generate quantity reports.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Delivery Order Analyzer - Streamlit web application.
Password-protected with dual auth (Streamlit secrets for cloud, config.json for local).
"""

import json

import pandas as pd
import streamlit as st
import hmac

from analyzer import DeliveryOrderAnalyzer, load_food_items, process_excel


def load_config():
    """Load configuration from Streamlit secrets or config.json file."""
    # Try Streamlit secrets first (for cloud deployment)
    try:
        if 'password' in st.secrets:
            return {"password": st.secrets["password"]}
    except Exception:
        pass  # No secrets configured locally, fall through to config.json

    # Fallback to config.json (for local development)
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ Configuration not found!")
        st.info("💡 **For deployment**: Add password to Streamlit Cloud secrets")
        st.info("💡 **For local development**: Ensure config.json file exists")
        return None
    except Exception as e:
        st.error(f"Error loading config: {str(e)}")
        return None


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        config = load_config()
        if config is None:
            st.session_state["password_correct"] = False
            return

        if hmac.compare_digest(st.session_state['password'], config.get("password", "")):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        _, col, _ = st.columns([3, 2, 3])
        with col:
            st.title("上海好吃米道")
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        _, col, _ = st.columns([3, 2, 3])
        with col:
            st.title("上海好吃米道")
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed", on_change=password_entered, key="password")
            st.error("Password incorrect. Please try again.")
        return False
    else:
        return True


def main():
    st.set_page_config(
        page_title="Delivery Order Analyzer",
        page_icon="🚚",
        layout="wide"
    )

    if not check_password():
        st.stop()

    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 Session")
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.markdown("---")
        st.markdown("### 📂 Data Management")

        uploaded_file = st.file_uploader(
            "Upload Excel File",
            type=['xlsx', 'xls'],
            help="Upload your delivery order Excel file to process"
        )

        if uploaded_file is not None:
            if st.button("🔄 Process Excel File"):
                with st.spinner("Processing Excel file..."):
                    try:
                        food_items = load_food_items()
                        df = process_excel(uploaded_file, food_items)
                        st.session_state['df'] = df
                        st.session_state['data_updated'] = True
                        st.success("Excel file processed successfully!")
                        st.rerun()
                    except FileNotFoundError as e:
                        st.error(f"❌ {e}")
                    except ValueError as e:
                        st.error(f"❌ {e}")
                    except Exception as e:
                        st.error(f"❌ Error processing file: {e}")

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("**Delivery Order Analyzer**")
        st.markdown("Version 2.0 - Enhanced")
        st.markdown("Secure access enabled")
        st.markdown("Excel upload supported")

    st.title("🚚 Delivery Order Analyzer")
    st.markdown("Upload Excel file or analyze existing delivery order data")

    if 'df' not in st.session_state:
        st.warning("📋 No data loaded. Please upload an Excel file to get started.")
        st.info("👆 Use the sidebar to upload your delivery order Excel file.")
        st.markdown("### 📤 How to Upload:")
        st.markdown("1. Click on 'Browse files' in the sidebar")
        st.markdown("2. Select your Excel file (.xlsx or .xls)")
        st.markdown("3. Click 'Process Excel File' to convert and load data")
        st.markdown("4. Start analyzing your delivery orders!")
        st.stop()

    analyzer = DeliveryOrderAnalyzer()
    analyzer.load(st.session_state['df'])

    st.success(f"✅ Loaded {len(analyzer.df)} delivery orders with {len(analyzer.food_columns)} food items")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📋 Select Orders")

        col1a, col1b, col1c = st.columns(3)
        with col1a:
            if st.button("Select All"):
                st.session_state.selected_orders = list(range(len(analyzer.df)))
        with col1b:
            if st.button("Clear All"):
                st.session_state.selected_orders = []
        with col1c:
            show_details = st.checkbox("Show Details", value=False)

        if 'selected_orders' not in st.session_state:
            st.session_state.selected_orders = []

        if st.session_state.get('data_updated', False):
            st.session_state.selected_orders = []
            st.session_state['data_updated'] = False

        with st.container():
            for idx, row in analyzer.df.iterrows():
                item_count = sum(1 for col in analyzer.food_columns
                                 if pd.notna(row[col]) and row[col] > 0)

                order_key = f"order_{idx}"
                is_selected = idx in st.session_state.selected_orders
                order_text = f"{row['delivery']} - {row['customer']} ({row['city']}) - {item_count} items"

                selected = st.checkbox(order_text, value=is_selected, key=order_key)

                if selected and idx not in st.session_state.selected_orders:
                    st.session_state.selected_orders.append(idx)
                elif not selected and idx in st.session_state.selected_orders:
                    st.session_state.selected_orders.remove(idx)

                if show_details and selected:
                    with st.expander(f"Details for {row['customer']}", expanded=False):
                        st.write(f"**Phone:** {row['phone_number']}")
                        st.write(f"**Address:** {row['address']}, {row['city']} {row['zip_code']}")
                        st.write(f"**Items Ordered:** {row['items_ordered']}")

    with col2:
        st.header("📊 Analysis Results")

        selected_count = len(st.session_state.selected_orders)
        st.info(f"Selected: {selected_count} orders")

        if selected_count > 0:
            if st.button("🔍 Analyze Selected Orders", type="primary"):
                sorted_items, total_items = analyzer.analyze(st.session_state.selected_orders)

                if sorted_items:
                    st.success(f"Analysis complete! Found {len(sorted_items)} unique items, {total_items} total items")

                    tab1, tab2, tab3 = st.tabs(["📈 Summary", "📋 Item List", "📄 Detailed Report"])

                    with tab1:
                        st.subheader("Summary")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Orders Analyzed", selected_count)
                        with col_b:
                            st.metric("Unique Items", len(sorted_items))
                        with col_c:
                            st.metric("Total Items", total_items)

                        df_chart = pd.DataFrame(sorted_items[:10], columns=['Item', 'Quantity'])
                        st.bar_chart(df_chart.set_index('Item'))

                    with tab2:
                        st.subheader("Item Quantities (Sorted by Total)")
                        df_display = pd.DataFrame(sorted_items, columns=['Food Item', 'Quantity'])
                        df_display.index = range(1, len(df_display) + 1)
                        st.dataframe(df_display, use_container_width=True, height=400)

                        st.download_button(
                            label="📥 Download as CSV",
                            data=df_display.to_csv(index=False),
                            file_name=f"delivery_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )

                    with tab3:
                        st.subheader("Detailed Report")
                        report = (
                            f"**DELIVERY ORDER ANALYSIS REPORT**\n"
                            f"================================\n\n"
                            f"**Analysis Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"**Orders Analyzed:** {selected_count}\n"
                            f"**Unique Items Ordered:** {len(sorted_items)}\n"
                            f"**Total Items:** {total_items}\n\n"
                            f"**SELECTED ORDERS:**\n"
                        )
                        for idx in st.session_state.selected_orders:
                            row = analyzer.df.iloc[idx]
                            report += f"\n• {row['delivery']} - {row['customer']} ({row['city']})"
                        report += "\n\n**ITEM QUANTITIES:**\n"
                        for item_name, quantity in sorted_items:
                            report += f"\n• {item_name}: {quantity}"

                        st.text_area("Report", report, height=400)
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

    st.markdown("---")
    st.markdown("**Instructions:** Upload an Excel file using the sidebar, then select delivery orders and click 'Analyze Selected Orders' to generate quantity reports.")


if __name__ == "__main__":
    main()

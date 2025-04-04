import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Set the page configuration for a wide, corporate-style layout
st.set_page_config(page_title="Naf Finance Tracker", page_icon=":money_with_wings:", layout="wide")

# st.sidebar.header("Instructions")
# st.sidebar.write("""
#     1. **Upload an Excel file** that contains product pricing data for scraping.
#     2. Click **Start Scraping** to begin the extraction process.
#     3. The scraper will extract product details and update the file.
#     4. After the scraping process, you will be able to download the updated file.
#     5. The scraper will process different product categories.
# """)

# ----------------- Inject Custom CSS -----------------
st.markdown("""
    <style>
        /* Set the overall page background */
        body {
            background-color: #f2f2f2;
        }
        /* Main container style */
        .block-container {
            padding-top: 2rem;
            background-color: #ffffff;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }
        /* Header style */
        h1, h2, h3, h4, h5, h6 {
            color: #003366;
            font-weight: 600;
        }
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #003366;
            color: white;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }
        /* Ensure sidebar headings and labels are white */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] h5,
        [data-testid="stSidebar"] h6,
        [data-testid="stSidebar"] label {
            color: white !important;
        }
        /* Force the dropdown text (the selected item and menu items) to black */
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] * {
            color: black !important;
        }
        /* Button styling */
        .stButton>button {
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-size: 16px;
            font-weight: 600;
        }
        /* Dataframe table styles */
        .dataframe-container table {
            border: 2px solid #003366;
            border-collapse: collapse;
        }
        .dataframe-container th {
            background-color: #007BFF;
            color: white;
            border: 1px solid #003366;
            padding: 0.5rem;
        }
        .dataframe-container td {
            border: 1px solid #003366;
            padding: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

# ----------------- Helper Functions -----------------
def parse_comma_number(input_str, default=0):
    """
    Parses a string that may contain commas into a float.
    For example, "90,000" becomes 90000.0.
    """
    try:
        return float(input_str.replace(",", "").strip())
    except Exception:
        return default

def format_number(num):
    """
    Formats a number with commas.
    """
    try:
        return f"{num:,.0f}"
    except Exception:
        return num

# ----------------- Google Sheets Functions -----------------
def init_google_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(
        "adept-rock-445911-p3-6f1266b2435a.json",  # Replace with your JSON file name
        scopes=scope
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key("1DNuyA2vy2uN9sO-I3z0hakfVUpAGkRrS3eGDw13Ju_0")
    return spreadsheet

def create_worksheet_layout(spreadsheet, month):
    """
    Creates a new worksheet for the given month with the layout:
      Row 1: A1 = "Monthly Income", B1 = 0
      Row 2: A2 = "Total Expenses so far", B2 = formula to sum expenses (rows 6 onward)
      Row 3: A3 = "Remaining Amount (Savings)", B3 = formula = B1 - B2
      Row 5: A5:D5 = table headers: [Date, Category, Description, Amount]
    """
    worksheet = spreadsheet.add_worksheet(title=month, rows="1000", cols="20")
    
    # Row 1: Monthly Income
    worksheet.update_cell(1, 1, "Monthly Income")
    worksheet.update_cell(1, 2, 0)
    
    # Row 2: Total Expenses so far (formula)
    worksheet.update_cell(2, 1, "Total Expenses so far")
    worksheet.update_cell(2, 2, "=SUM(D6:D1000)")
    
    # Row 3: Remaining Amount (Savings)
    worksheet.update_cell(3, 1, "Remaining Amount (Savings)")
    worksheet.update_cell(3, 2, "=B1 - B2")
    
    # Row 5: Table headers
    worksheet.update("A5:D5", [["Date", "Category", "Description", "Amount"]])
    
    return worksheet

# ----------------- Main App -----------------
def main():
    # st.title("Naf Finance Tracker")
    st.markdown('<h1 style="text-align: center;">Naf Finance Tracker</h1>', unsafe_allow_html=True)

    
    # 1. Initialize Google Sheets once
    if "spreadsheet" not in st.session_state:
        st.session_state.spreadsheet = init_google_sheet()
    spreadsheet = st.session_state.spreadsheet
    
    # 2. Fetch all existing worksheet tabs from the spreadsheet
    worksheets = spreadsheet.worksheets()
    worksheet_titles = [ws.title for ws in worksheets]
    
    # 3. Build the sidebar dropdown from the worksheet titles plus "View All Months"
    st.sidebar.title("Manage Months")
    if "View All Months" not in worksheet_titles:
        worksheet_titles.insert(0, "View All Months")
    
    selected_option = st.sidebar.selectbox("Select Month", worksheet_titles)
    
    # Button to create a new month
    if st.sidebar.button("Create New Month"):
        selected_option = None  # This triggers the new month creation form
    
    # 4. Main logic based on sidebar selection
    if not selected_option:
        st.subheader("Enter a New Month for Your Expenses")
        with st.form("month_form"):
            month_input = st.text_input("Month (e.g., April-2025)")
            submit_month = st.form_submit_button("Set Month")
            if submit_month and month_input.strip():
                month = month_input.strip()
                try:
                    spreadsheet.worksheet(month)
                    st.warning("That worksheet already exists!")
                except gspread.WorksheetNotFound:
                    create_worksheet_layout(spreadsheet, month)
                    st.success(f"New month '{month}' created successfully!")
                st.experimental_rerun()
    
    elif selected_option == "View All Months":
        st.header("View All Months")
        for ws in worksheets:
            # Skip any pseudo-tab if present
            if ws.title == "View All Months":
                continue
            with st.container():
                st.write(f"## {ws.title}")
                total_income_val = ws.acell("B1").value
                try:
                    total_income = float(total_income_val)
                except:
                    total_income = 0
                st.warning(f"**Monthly Income:** {format_number(total_income)}")
                
                expense_data = ws.get("A6:D1000")
                expense_data = [row for row in expense_data if any(cell.strip() for cell in row)]
                if expense_data:
                    df = pd.DataFrame(expense_data, columns=["Date", "Category", "Description", "Amount"])
                    df["Amount"] = pd.to_numeric(df["Amount"].str.replace(",", ""), errors="coerce").fillna(0)
                    total_expenses = df["Amount"].sum()
                    remaining_amount = total_income - total_expenses
                    
                    styled_df = (
                        df.style
                        .format({"Amount": "{:,.0f}"})
                        .set_properties(**{'background-color': '#f5f5f5','color': '#333'})
                        .set_table_styles([
                            {'selector': 'th', 'props': [('background-color', '#003366'),
                                                        ('color', 'white'),
                                                        ('border', '1px solid #003366')]},
                            {'selector': 'td', 'props': [('border', '1px solid #003366')]},
                            {'selector': 'table', 'props': [('border', '2px solid #003366'),
                                                            ('border-collapse', 'collapse')]}
                        ])
                    )
                    st.dataframe(styled_df)
                    
                    st.error(f"**Total Expenses so far:** {format_number(total_expenses)}")
                    st.success(f"**Remaining Amount (Savings):** {format_number(remaining_amount)}")
                else:
                    st.write("No expenses recorded yet.")
                
                with st.expander("Add Expense"):
                    with st.form(key=f"expense_form_{ws.title}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            expense_date = st.date_input("Date", value=datetime.now())
                        with col2:
                            category = st.text_input("Category", value="Shopping")
                        col3, col4 = st.columns(2)
                        with col3:
                            description = st.text_input("Description", value="Near office")
                        with col4:
                            expense_amount_str = st.text_input("Expense Amount", value="0")
                            expense_amount = parse_comma_number(expense_amount_str)
                        submit_expense = st.form_submit_button("Add Expense")
                        if submit_expense:
                            new_expense = [
                                expense_date.strftime("%Y-%m-%d"),
                                category,
                                description,
                                expense_amount
                            ]
                            ws.append_row(new_expense)
                            st.success("Expense added successfully!")
                            st.experimental_rerun()
    
    else:
        st.header(f"Expense Tracker for {selected_option}")
        try:
            worksheet = spreadsheet.worksheet(selected_option)
        except gspread.WorksheetNotFound:
            st.error("Worksheet not found!")
            return
        
        monthly_income_val = worksheet.acell("B1").value
        try:
            monthly_income = float(monthly_income_val)
        except:
            monthly_income = 0
        
        st.subheader("Enter Your Monthly Income")
        monthly_income_str = st.text_input(
            "Monthly Income",
            value=format_number(monthly_income),
            key="monthly_income"
        )
        new_monthly_income = parse_comma_number(monthly_income_str, default=monthly_income)
        if new_monthly_income != monthly_income:
            worksheet.update_cell(1, 2, new_monthly_income)
            monthly_income = new_monthly_income
        
        expense_data = worksheet.get("A6:D1000")
        expense_data = [row for row in expense_data if any(cell.strip() for cell in row)]
        if expense_data:
            df = pd.DataFrame(expense_data, columns=["Date", "Category", "Description", "Amount"])
            df["Amount"] = pd.to_numeric(df["Amount"].str.replace(",", ""), errors="coerce").fillna(0)
            st.subheader("Expense Records")
            styled_df = (
                df.style
                .format({"Amount": "{:,.0f}"})
                .set_properties(**{'background-color': '#f5f5f5','color': '#333'})
                .set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#007BFF'),
                                                 ('color', 'white'),
                                                 ('border', '1px solid #003366')]},
                    {'selector': 'td', 'props': [('border', '1px solid #003366')]},
                    {'selector': 'table', 'props': [('border', '2px solid #003366'),
                                                      ('border-collapse', 'collapse')]}
                ])
            )
            st.dataframe(styled_df)
            
            total_expenses = df["Amount"].sum()
            remaining_amount = monthly_income - total_expenses
            st.error(f"**Total Expenses so far:** {format_number(total_expenses)}")
            st.success(f"**Remaining Amount (Savings):** {format_number(remaining_amount)}")
        else:
            st.write("No expenses recorded yet.")
        
        with st.expander("Add Expense"):
            with st.form("expense_form"):
                col1, col2 = st.columns(2)
                with col1:
                    expense_date = st.date_input("Date", value=datetime.now())
                with col2:
                    category = st.text_input("Category", value="Shopping")
                col3, col4 = st.columns(2)
                with col3:
                    description = st.text_input("Description", value="Near office")
                with col4:
                    expense_amount_str = st.text_input("Expense Amount", value="0", key="expense_amount")
                    expense_amount = parse_comma_number(expense_amount_str)
                submit_expense = st.form_submit_button("Add Expense")
                if submit_expense:
                    new_expense = [
                        expense_date.strftime("%Y-%m-%d"),
                        category,
                        description,
                        expense_amount
                    ]
                    worksheet.append_row(new_expense)
                    st.success("Expense added successfully!")
                    st.experimental_rerun()

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="Financial Planning: EMI Calculator",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Calculation Function ---
def calculate_emi(principal, rate_annual, tenure_months):
    """Calculates the EMI, total interest, and generates the amortization schedule."""
    if rate_annual == 0:
        # Simple division if interest rate is 0
        monthly_emi = principal / tenure_months
        total_interest = 0
    else:
        rate_monthly = (rate_annual / 100) / 12
        # EMI Formula: P * r * (1 + r)^n / ((1 + r)^n - 1)
        # Handle the case where the tenure is 0 to avoid division by zero
        if tenure_months == 0:
            return 0, 0, pd.DataFrame()
            
        monthly_emi = principal * rate_monthly * (1 + rate_monthly)**tenure_months / (((1 + rate_monthly)**tenure_months) - 1)
        total_interest = (monthly_emi * tenure_months) - principal

    total_payable = principal + total_interest

    # --- Amortization Schedule Generation ---
    balance = principal
    schedule = []
    
    for month in range(1, tenure_months + 1):
        if rate_annual == 0:
            interest_paid = 0
        else:
            interest_paid = balance * ((rate_annual / 100) / 12)
        
        principal_paid = monthly_emi - interest_paid
        balance -= principal_paid
        
        # Adjust last payment to ensure balance is exactly 0 due to floating point inaccuracies
        if month == tenure_months:
            # Ensure the last principal paid covers the remaining balance from the previous step
            principal_paid = balance + principal_paid 
            balance = 0
            
        schedule.append({
            'Month': month,
            'Starting Balance': principal, # This is technically wrong for the table but useful for tracking. We'll use the 'Ending Balance' for the actual table.
            'EMI': monthly_emi,
            'Principal Paid': principal_paid,
            'Interest Paid': interest_paid,
            'Ending Balance': balance
        })
        
        # Reset principal for the next iteration's calculation of starting balance in the loop
        principal = balance + principal_paid

    schedule_df = pd.DataFrame(schedule)
    
    # Calculate cumulative values for charting
    schedule_df['Cumulative Interest'] = schedule_df['Interest Paid'].cumsum()
    schedule_df['Cumulative Principal'] = schedule_df['Principal Paid'].cumsum()
    schedule_df['Total Paid'] = schedule_df['Cumulative Interest'] + schedule_df['Cumulative Principal']

    return monthly_emi, total_interest, total_payable, schedule_df


# --- Main Application Layout ---
st.title("🏡 The Smart EMI Calculator 💰")
st.markdown("Easily calculate your monthly EMI and visualize your loan repayment plan.")
st.write("---")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("⚙️ Loan Details")
    
    # Input Widgets
    loan_amount = st.slider(
        "Loan Amount (Principal) $",
        min_value=10000,
        max_value=10000000,
        value=500000,
        step=50000,
        help="The total amount borrowed."
    )
    
    interest_rate_annual = st.slider(
        "Annual Interest Rate (%) 📈",
        min_value=0.0,
        max_value=20.0,
        value=8.0,
        step=0.1,
        format="%.1f",
        help="The yearly interest rate charged by the lender."
    )
    
    loan_tenure_years = st.slider(
        "Loan Tenure (Years) 🗓️",
        min_value=1,
        max_value=30,
        value=10,
        step=1,
        help="The duration of the loan in years."
    )

# Convert years to months for calculation
loan_tenure_months = loan_tenure_years * 12

# --- Calculation and Result Display ---
if loan_amount > 0 and loan_tenure_months > 0:
    emi, total_interest, total_payable, amortization_df = calculate_emi(
        loan_amount, 
        interest_rate_annual, 
        loan_tenure_months
    )

    st.subheader("✅ Calculation Summary")
    
    # --- Metrics Section ---
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Monthly EMI 💵", f"${emi:,.2f}")
    col2.metric("Total Payable Amount 💸", f"${total_payable:,.2f}")
    col3.metric("Total Interest Paid 🧡", f"${total_interest:,.2f}")
    col4.metric("Total Payments (Months) 📅", f"{loan_tenure_months:,}")
    
    # Information ratio
    interest_ratio = (total_interest / loan_amount) * 100 if loan_amount > 0 else 0
    st.info(f"The total interest paid amounts to **{interest_ratio:.1f}%** of the principal loan amount. This is crucial for financial planning. 🧐")

    st.write("---")

    # --- Charts Section (Tabs) ---
    st.subheader("📊 Repayment Visualizations")
    chart_tab, distribution_tab, table_tab = st.tabs(["Repayment Breakdown", "Interest/Principal Distribution", "Amortization Table"])

    with chart_tab:
        st.write("### Principal vs. Interest Over Time")
        
        # Area/Line Chart using Plotly
        fig_repayment = go.Figure()

        # Cumulative Principal Paid
        fig_repayment.add_trace(go.Scatter(
            x=amortization_df['Month'], 
            y=amortization_df['Cumulative Principal'],
            fill='tozeroy', 
            mode='lines', 
            name='Principal Paid (Cumulative)',
            line=dict(width=0, color='rgb(31, 119, 180)')
        ))
        
        # Cumulative Interest Paid
        fig_repayment.add_trace(go.Scatter(
            x=amortization_df['Month'], 
            y=amortization_df['Cumulative Interest'],
            fill='tozeroy', 
            mode='lines', 
            name='Interest Paid (Cumulative)',
            line=dict(width=0, color='rgb(255, 127, 14)')
        ))

        fig_repayment.update_layout(
            title_text='**Cumulative Repayment Breakdown**',
            xaxis_title='Month of Repayment',
            yaxis_title='Amount Paid ($)',
            hovermode="x unified",
            height=500
        )
        st.plotly_chart(fig_repayment, use_container_width=True)
        

    with distribution_tab:
        st.write("### Principal vs. Interest Distribution (Pie Chart)")
        
        # Pie Chart showing the distribution of total payable amount
        pie_data = pd.DataFrame({
            'Category': ['Principal', 'Total Interest'],
            'Amount': [loan_amount, total_interest]
        })

        fig_pie = px.pie(
            pie_data, 
            values='Amount', 
            names='Category', 
            title='**Total Payable Amount Distribution**',
            color_discrete_sequence=['#1f77b4', '#ff7f0e'], # Blue for Principal, Orange for Interest
            hole=.3 # Creates a donut chart
        )
        
        fig_pie.update_traces(textinfo='percent+value', texttemplate='%{label}<br>$%{value:,.0f}')
        fig_pie.update_layout(height=450)
        
        st.plotly_chart(fig_pie, use_container_width=True)
        


    with table_tab:
        st.write("### 📝 Detailed Amortization Table")
        
        # Prepare the DataFrame for display (dropping cumulative columns)
        display_df = amortization_df[['Month', 'EMI', 'Principal Paid', 'Interest Paid', 'Ending Balance']].copy()
        
        # Format the numbers for better readability
        format_mapping = {
            'EMI': '${:,.2f}',
            'Principal Paid': '${:,.2f}',
            'Interest Paid': '${:,.2f}',
            'Ending Balance': '${:,.2f}'
        }

        # Use st.dataframe with custom formatting
        st.dataframe(
            display_df.style.format(format_mapping), 
            use_container_width=True,
            height=400
        )
        
        st.markdown(f"**Loan Term:** {loan_tenure_years} years ({loan_tenure_months} months) | **Principal:** ${loan_amount:,.2f}")

else:
    st.warning("Please ensure the loan amount and tenure are greater than zero to perform the calculation.")

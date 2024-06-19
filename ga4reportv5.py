import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


# Function to process the uploaded CSV file
def process_csv(file):
    df = pd.read_csv(file)

    df['date'] = pd.to_datetime(df['date'])
    df['Month'] = df['date'].dt.to_period('M')
    monthly_data = df.groupby(['account_name', 'Month']).agg({'users': 'sum', 'conversions': 'sum'}).reset_index()
    monthly_data['Conversion Rate'] = monthly_data['conversions'] / monthly_data['users']

    # Adding Conversion Status column
    def conversion_status(conversions):
        if conversions < 30:
            return 'Needs attention'
        elif 30 <= conversions <= 49:
            return 'Good'
        else:
            return 'Great!'

    monthly_data['Conversion Status'] = monthly_data['conversions'].apply(conversion_status)

    # Adding Conversion Rate Status column
    def conversion_rate_status(rate):
        if rate < 0.10:
            return 'Needs attention'
        else:
            return 'Ok'

    monthly_data['Conversion Rate Status'] = monthly_data['Conversion Rate'].apply(conversion_rate_status)

    # Reorder columns
    monthly_data = monthly_data[
        ['account_name', 'Month', 'users', 'conversions', 'Conversion Status', 'Conversion Rate',
         'Conversion Rate Status']]

    # Rename columns for better readability
    monthly_data.columns = ['Account Name', 'Month', 'Users', 'Conversions', 'Conversion Status', 'Conversion Rate',
                            'Conversion Rate Status']

    return monthly_data, df


# Function to get top 10 pages per month per account
def get_top_pages(df):
    df['Month'] = df['date'].dt.to_period('M')
    top_pages = df.groupby(['account_name', 'Month', 'page_path']).agg(
        {'users': 'sum', 'conversions': 'sum', 'user_conversion_rate': 'mean'}).reset_index()

    # Calculate conversion status and conversion rate status for each page
    def conversion_status(conversions):
        if conversions < 30:
            return 'Needs attention'
        elif 30 <= conversions <= 49:
            return 'Good'
        else:
            return 'Great!'

    def conversion_rate_status(rate):
        if rate < 0.10:
            return 'Needs attention'
        else:
            return 'Ok'

    top_pages['Conversion Status'] = top_pages['conversions'].apply(conversion_status)
    top_pages['Conversion Rate Status'] = top_pages['user_conversion_rate'].apply(conversion_rate_status)
    top_pages = top_pages.sort_values(['account_name', 'Month', 'users'], ascending=[True, True, False])

    top_pages_list = []
    for account in top_pages['account_name'].unique():
        for month in top_pages[top_pages['account_name'] == account]['Month'].unique():
            top_10 = top_pages[(top_pages['account_name'] == account) & (top_pages['Month'] == month)].head(10)
            top_pages_list.append(top_10)

    top_pages_df = pd.concat(top_pages_list)
    top_pages_df = top_pages_df[
        ['account_name', 'Month', 'page_path', 'users', 'conversions', 'Conversion Status', 'user_conversion_rate',
         'Conversion Rate Status']]
    top_pages_df.columns = ['Account Name', 'Month', 'Page Path', 'Users', 'Conversions', 'Conversion Status',
                            'Conversion Rate', 'Conversion Rate Status']

    return top_pages_df


# Function to plot monthly statistics
def plot_statistics(data, account):
    account_data = data[data['Account Name'] == account]
    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:blue'
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Users', color=color)
    ax1.plot(account_data['Month'].astype(str), account_data['Users'], color=color, marker='o')
    for i, txt in enumerate(account_data['Users']):
        ax1.annotate(txt, (account_data['Month'].astype(str).iloc[i], account_data['Users'].iloc[i]),
                     textcoords="offset points", xytext=(0, 10), ha='center')
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Conversions', color=color)
    ax2.plot(account_data['Month'].astype(str), account_data['Conversions'], color=color, marker='o')
    for i, txt in enumerate(account_data['Conversions']):
        ax2.annotate(txt, (account_data['Month'].astype(str).iloc[i], account_data['Conversions'].iloc[i]),
                     textcoords="offset points", xytext=(0, 10), ha='center')
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()
    st.pyplot(fig)


# Streamlit app
st.title('GA4 Monthly Report (Organic Traffic)')

st.header('Instructions')
st.markdown('Login to Windsor AI and download a CSV file with GA4 data of the clients you want to analyze.')
st.markdown('Include the following columns in the Windsor AI report: 1) Account Name, 2) Key Events, 3) Date, 4) First User Medium, 5) Page Path, 6) User Key Event Rate, 7) Users.')
st.markdown("**Important:** Before exporting from Windsor AI, filter the data using the column First User Medium to view only the rows that 'contain' the word *organic*.")

uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    monthly_data, df = process_csv(uploaded_file)
    if monthly_data is not None:

        st.header('Account Level GA4 Report')
        st.dataframe(monthly_data)

        top_pages_df = get_top_pages(df)
        st.header('Top 10 Pages per Month per Account')
        st.dataframe(top_pages_df)

        st.header('Monthly Key Metrics Per Account')
        accounts = monthly_data['Account Name'].unique()
        for account in accounts:
            st.markdown(f'Monthly Statistics for {account}')
            plot_statistics(monthly_data, account)


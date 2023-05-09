import yfinance as yf
import pandas as pd
import numpy as np
from bokeh.io import show
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, Div, LinearColorMapper, ColorBar
from bokeh.plotting import figure
from bokeh.layouts import column, row
from datetime import datetime, timedelta
from bokeh.models.formatters import NumeralTickFormatter

def user_input():
    # define the stock ticker symbol
    # user inputs
    choice = str(input('Please enter the ticker symbol here: '))
    start_date = str(input('Please enter start date (YYYY-MM-DD): '))
    end_date = str(input('Please enter end date (YYYY-MM-DD): '))
    stock_input = float(input('Please enter number of shares owned, otherwise enter 0: '))
    purchase_date = str(input('Please enter first purchase date (YYYY-MM-DD), otherwise enter 0: '))    
    return choice, start_date, end_date, stock_input, purchase_date

def get_purchase_info():
    purchase_info = {}
    while True:
        purchase_date = input('Enter purchase date (YYYY-MM-DD), or press enter to finish: ')
        if not purchase_date:
            break
        shares_owned = float(input('Enter number of shares owned: '))
        purchase_info[purchase_date] = shares_owned
    return purchase_info

def ticker(choice, start_date, end_date):
    # retrieve the stock data
    print(f"You selected {choice}")
    ticker = yf.Ticker(choice)
    company_name = ticker.info['longName']
    print(f"The company name is: {company_name}")
    print(f'You selected {start_date} to {end_date} as the period')
    print('The dashboard will now open on your browser as an HTML file')
    stock_data = ticker.history(start=start_date, end=end_date)
    return stock_data, company_name

def dataframe(stock_data):
    # create a dataframe
    df = pd.DataFrame(stock_data, columns=['Open','High','Low','Close','Volume'])

    # remove the time from the date index column
    df.index = df.index.date

    # reset index and use date as index column
    df = df.reset_index()
    df = df.rename(columns={'index':'Date'})
    df['Date'] = pd.to_datetime(df['Date'])

    # sort the dataframe by date
    df = df.sort_values(by=['Date'])

    return df

def create_scatter_plot(df,company_name):
    # creates scatter plot
    title = f'Open Prices Over Time for {company_name}'
    p = figure(title=title, x_axis_label='', y_axis_label='Open Price')

    # formatting properties
    p.scatter(df['Date'], df['Open'], color='navy')
    p.xaxis[0].formatter = DatetimeTickFormatter(months='%b %Y')
    return p

def create_candlestick_chart(df,company_name):
    # creates candlestick chart
    title = f'Candlestick Chart for {company_name}'
    inc = df.Close > df.Open
    dec = df.Open > df.Close
    w = 12*60*60*1000 # half day in ms
    p = figure(x_axis_type="datetime", title = title,x_axis_label='')

    # formatting properties
    p.xaxis.major_label_orientation = np.pi/4
    p.grid.grid_line_alpha=0.3
    p.segment(df.Date, df.High, df.Date, df.Low, color="black")
    p.vbar(df.Date[inc], w, df.Open[inc], df.Close[inc], fill_color="#D5E1DD", line_color="black")
    p.vbar(df.Date[dec], w, df.Open[dec], df.Close[dec], fill_color="#F2583E", line_color="black")

    # formats date on x-axis as mmm yyyy
    p.xaxis[0].formatter = DatetimeTickFormatter(months='%b %Y')
    return p

def create_bar_chart(df,company_name):
    # creates bar chart
    title = f'Volume of Trading Activity for {company_name}'

    # creates the figure
    p = figure(title=title, x_axis_label='', y_axis_label='Volume')
    # Add the bars to the chart
    p.vbar(x=df['Date'], top=df['Volume'], width=0.5, color='green', 
       fill_alpha=0.5, legend_label='Volume')
    
    # Set the chart properties
    p.legend.title = 'Volume'
    p.legend.location = "top_right"
    p.legend.label_text_font_size = "10pt"
    p.xaxis.major_label_orientation = 1.2
    p.xaxis[0].formatter = DatetimeTickFormatter(months='%b %Y')

    # set y-axis formatter to millions
    p.yaxis.formatter = NumeralTickFormatter(format='0.00a')
    return p

def create_heatmap(df, company_name):
    # Create a new DataFrame for heatmap
    heatmap_df = pd.DataFrame(columns=['Date', 'Day', 'Close'])

    # Iterate over each date in the DataFrame
    for index, row in df.iterrows():
        date = row['Date']
        weekday = date.strftime('%A')
        close_price = row['Close']
        heatmap_df = pd.concat([heatmap_df, pd.DataFrame({'Date': [date], 'Day': [weekday], 'Close': [close_price]})])

    # Define color mapper based on closing price
    color_mapper = LinearColorMapper(palette='RdYlGn11', low=heatmap_df['Close'].min(), high=heatmap_df['Close'].max())

    # Create heatmap figure
    title = f'Stock History Heatmap for {company_name}'
    heatmap = figure(title=title, x_axis_label='', y_axis_label='Day of Week',
                     x_axis_type='datetime', y_range=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
    heatmap.xaxis[0].formatter = DatetimeTickFormatter(months='%b %Y')
    
    # Add heatmap rectangle glyphs
    heatmap.rect(x='Date', y='Day', width=86400000, height=1, source=heatmap_df,
                 fill_color={'field': 'Close', 'transform': color_mapper}, line_color=None)

    # Add color bar to the right of the heatmap
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12, location=(0, 0))
    heatmap.add_layout(color_bar, 'right')
    return heatmap

def share_price_at_dates(df, stock_input, purchase_date, purchase_info):
    total_shares = 0
    total_cost = 0
    average_cost_basis = 0

    if not purchase_info:
        print('No purchase information provided')
    else:
        for purchase_date, shares_owned in purchase_info.items():
            purchase_df = df[df['Date'] >= pd.to_datetime(purchase_date)]
            purchase_price = purchase_df.iloc[0]['Close']
            purchase_cost = purchase_price * shares_owned
            total_cost += purchase_cost
            total_shares += shares_owned

        total_shares += stock_input

        if total_shares == 0:
            print('No shares owned')
        else:
            average_cost_basis = total_cost / total_shares

    current_price = df.iloc[-1]['Close']
    current_value = current_price * total_shares
    gain_or_loss = current_value - total_cost

    return total_cost, total_shares, average_cost_basis, current_value, gain_or_loss

def purchase_details(purchase_date, end_date, total_cost, total_shares, average_cost_basis, current_value, gain_or_loss):
    output = []
    output.append(f"Total Cost: ${total_cost:,.2f}")
    output.append(f"Total Shares: {total_shares:,.2f}")
    output.append(f"Current Value: ${current_value:,.2f}")
    output.append(f'Average Cost Basis: ${average_cost_basis:,.2f}')
    if gain_or_loss > 0:
        output.append(f"Gain between {purchase_date} and {end_date}: ${gain_or_loss:,.0f}")
    else:
        output.append(f"Loss between {purchase_date} and {end_date}: ${gain_or_loss:,.0f}")
    return output

def create_dashboard_text(purchase_date, end_date, total_cost, total_shares, average_cost_basis, current_value, gain_or_loss):
    output = purchase_details(purchase_date, end_date, total_cost, total_shares, average_cost_basis, current_value, gain_or_loss)
    text = "<br>".join(output)
    if gain_or_loss > 0:
        text += "<br><span style='color:green;font-weight:bold'>Gain</span>"
    else:
        text += "<br><span style='color:red;font-weight:bold'>Loss</span>"
    div = Div(text=text, width=400,styles={'font-size': '20pt'})
    return div

def show_dashboard(p1, p2, p3, p4, div, company_name, choice, start_date, end_date):
    # create a new column layout
    col = column()

    # format start date
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')  # convert start date to datetime object
    start_date = start_date_obj.strftime('%B %Y')  # format the datetime object to desired format

    # format end date
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')  # convert end date to datetime object
    end_date = end_date_obj.strftime('%B %Y')  # format the datetime object to desired format

    # add a disclaimer to the dashboard
    disclaimer = Div(text="<h3 style='text-align:center;color:red;'>Disclaimer: This Stock History Data Analysis Dashboard is for educational and creative purposes only. The information presented in this dashboard is not intended to be used for making financial decisions. We do not provide financial advice or make any representations as to the accuracy, completeness, or timeliness of the information contained in this dashboard. You are solely responsible for any investment decisions you make based on the information presented in this dashboard. Please consult with a licensed financial advisor before making any investment decisions.</h3>")
    col.children.append(disclaimer)

    # add a title to the dashboard
    title = Div(text=f"<h1 style='text-align:center;'>Stock History Data Analysis Dashboard for {company_name} (${choice}) between {start_date} and {end_date}</h1>")
    col.children.append(title)

    # create a new column layout for p1 and p3
    p1_p3_column = column(p1, p3)

    # create a new column layout for p2 and p4
    p2_p4_column = column(p2, p4)

    # create a new column layout for div
    div_column = column(div)

    # create a new row layout with p1_p3_column and p2_p4_column as columns
    heatmap_bubble_row = row(p1_p3_column, p2_p4_column,div_column)

    # add heatmap_bubble_row to a new row layout
    dashboard_row = row(heatmap_bubble_row)

    # add the dashboard_row to the column layout
    col.children.append(dashboard_row)

    # show the dashboard
    show(col)

def main():
    choice, start_date, end_date, stock_input,purchase_date = user_input()
    stock_data, company_name = ticker(choice, start_date, end_date)
    df = dataframe(stock_data)
    p1 = create_scatter_plot(df,company_name)
    p2 = create_candlestick_chart(df,company_name)
    p3 = create_bar_chart(df,company_name)
    p4 = create_heatmap(df,company_name)
    purchase_info = get_purchase_info()
    total_cost, total_shares, average_cost_basis, current_value, gain_or_loss = share_price_at_dates(df, stock_input, purchase_date, purchase_info)
    purchase_details(purchase_date, end_date, total_cost, total_shares, average_cost_basis, current_value, gain_or_loss)
    div = create_dashboard_text(purchase_date, end_date, total_cost, total_shares, average_cost_basis, current_value, gain_or_loss)
    show_dashboard(p1, p2, p3, p4, div, company_name, choice, start_date, end_date)

if __name__ == "__main__":
    main() 
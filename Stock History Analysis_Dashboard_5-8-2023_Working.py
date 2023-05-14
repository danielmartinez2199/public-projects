from datetime import datetime
import pandas as pd
import numpy as np
import yfinance as yf
from bokeh.io import show
from bokeh.models import DatetimeTickFormatter, Div, LinearColorMapper, ColorBar
from bokeh.plotting import figure
from bokeh.layouts import column, row
from bokeh.models.formatters import NumeralTickFormatter

def user_input():
    """
    Prompts the user for input and returns a tuple of the ticker symbol choice, 
    period start and end dates, initial number of shares owned (if applicable), 
    and initial purchase date of shares (if applicable).
    """
    choice = str(input('Please enter the ticker symbol here: '))
    start_date = str(input('Please enter start date (YYYY-MM-DD): '))
    end_date = str(input('Please enter end date (YYYY-MM-DD): '))
    shares_input = float(input('Please enter number of shares owned, otherwise enter 0: '))
    purchase_date = str(input('Please enter first purchase date (YYYY-MM-DD), otherwise enter 0: '))    

    return choice, start_date, end_date, shares_input, purchase_date

def get_purchase_info():
    """
    Prompts the user to enter purchase dates and owned number of shares, and 
    returns a dictionary where the keys are purchase dates (YYYY-MM-DD) and 
    the values are the corresponding number of shares.
    """
    purchase_info = {}
    while True:
        purchase_date = input('Enter purchase date (YYYY-MM-DD), or press enter to finish: ')
        if not purchase_date:
            break
        shares_owned = float(input('Enter number of shares owned: '))
        purchase_info[purchase_date] = shares_owned\
        
    return purchase_info

def ticker(choice, start_date, end_date):
    """
    Function inputs: ticker choice, start and end dates of stock history.
    Prints the user selected ticker symbol and company name. 
    Returns the stock data from the user inputted choice.
    """
    print(f"You selected {choice}")
    ticker = yf.Ticker(choice)
    company_name = ticker.info['longName']
    print(f"The company name is: {company_name}")
    print(f'You selected {start_date} to {end_date} as the period')
    print('The dashboard will now open on your browser as an HTML file')
    stock_data = ticker.history(start=start_date, end=end_date)

    return stock_data, company_name

def dataframe(stock_data):
    """
    Function input: stock data from ticker function.
    Creates a dataframe. Removes the time from the date index column.
    Resets the index and uses the date as the index column.
    Sorts the index date column and returns the dataframe.
    """
    df = pd.DataFrame(stock_data, columns=['Open','High','Low','Close','Volume'])
    df.index = df.index.date
    df = df.reset_index()
    df = df.rename(columns={'index':'Date'})
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by=['Date'])

    return df

def create_scatter_plot(df,company_name):
    """
    Function input: dataframe and company name from dataframe function.
    Creates the scatter plot and formats the chart with the date as x-axis and the open price as the y-axis with a navy blue color.
    The chart outputs the date in mmm yyyy format and finally returns the chart.
    """
    title = f'Open Prices Over Time for {company_name}'
    p = figure(title=title, x_axis_label='', y_axis_label='Open Price')
    p.scatter(df['Date'], df['Open'], color='navy')
    p.xaxis[0].formatter = DatetimeTickFormatter(months='%b %Y')
    return p

def create_candlestick_chart(df,company_name):
    """
    Function input: dataframe and company name from dataframe function.
    Creates the candlestick chart and formats the chart with the date as the x-axis and the open/close prices as the y-axis.
    The closing price is the top of each "candlestick", while the open price is the bottom of each "candlestick".
    The chart outputs the date in mmm yyyy format and finally returns the chart.
    """
    title = f'Candlestick Chart for {company_name}'
    inc = df.Close > df.Open
    dec = df.Open > df.Close
    w = 12*60*60*1000 # half day in ms
    p = figure(x_axis_type="datetime", title = title,x_axis_label='')
    p.xaxis.major_label_orientation = np.pi/4
    p.grid.grid_line_alpha=0.3
    p.segment(df.Date, df.High, df.Date, df.Low, color="black")
    p.vbar(df.Date[inc], w, df.Open[inc], df.Close[inc], fill_color="#D5E1DD", line_color="black")
    p.vbar(df.Date[dec], w, df.Open[dec], df.Close[dec], fill_color="#F2583E", line_color="black")
    p.xaxis[0].formatter = DatetimeTickFormatter(months='%b %Y')
    return p

def create_bar_chart(df,company_name):
    """
    Function input: dataframe and company name from dataframe function.
    Creates a bar chart for the volume of trading activity. X-axis = dates and the y-axis = volume.
    Adds a legend and formats the volume to units of millions in shares. 
    """
    title = f'Volume of Trading Activity for {company_name}'
    p = figure(title=title, x_axis_label='', y_axis_label='Volume')
    p.vbar(x=df['Date'], top=df['Volume'], width=0.5, color='green', 
       fill_alpha=0.5, legend_label='Volume')
    p.legend.title = 'Volume'
    p.legend.location = "top_right"
    p.legend.label_text_font_size = "10pt"
    p.xaxis.major_label_orientation = 1.2
    p.xaxis[0].formatter = DatetimeTickFormatter(months='%b %Y')
    p.yaxis.formatter = NumeralTickFormatter(format='0.00a')
    return p

def create_heatmap(df, company_name):
    """
    Function input: dataframe and company name from dataframe function.
    Creates a new dataframe for the heatmap. Returns the corresponding day of the dates and the close price between the start and end date.
    Creates a color mapper based on close price and heatmap figure with rectangular glyphs and color bar (on the right)
    """
    heatmap_df = pd.DataFrame(columns=['Date', 'Day', 'Close'])

    for index, row in df.iterrows():
        date = row['Date']
        weekday = date.strftime('%A')
        close_price = row['Close']
        heatmap_df = pd.concat([heatmap_df, pd.DataFrame({'Date': [date], 'Day': [weekday], 'Close': [close_price]})])

    color_mapper = LinearColorMapper(palette='RdYlGn11', low=heatmap_df['Close'].min(), high=heatmap_df['Close'].max())
    title = f'Stock History Heatmap for {company_name}'
    heatmap = figure(title=title, x_axis_label='', y_axis_label='Day of Week',
                     x_axis_type='datetime', y_range=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
    heatmap.xaxis[0].formatter = DatetimeTickFormatter(months='%b %Y')
    
    heatmap.rect(x='Date', y='Day', width=86400000, height=1, source=heatmap_df,
                 fill_color={'field': 'Close', 'transform': color_mapper}, line_color=None)

    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12, location=(0, 0))
    heatmap.add_layout(color_bar, 'right')
    return heatmap

def share_price_at_dates(df, shares_input, purchase_date, purchase_info):
    """
    Function input: dataframe from dataframe function, number of share(s) owned and purchase date(s) from get_purchase_info function
    Calculates the accumulation of shares, total share cost, average cost basis, current share price, current total stock value, and gain or loss value.
    """
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

        total_shares += shares_input

        if total_shares == 0:
            print('No shares owned')
        else:
            average_cost_basis = total_cost / total_shares

    current_price = df.iloc[-1]['Close']
    current_value = current_price * total_shares
    gain_or_loss = current_value - total_cost

    return total_cost, total_shares, average_cost_basis, current_value, gain_or_loss

def purchase_details(purchase_date, end_date, total_cost, total_shares, average_cost_basis, current_value, gain_or_loss):
    """
    Function input: dataframe from dataframe function, number of share(s) owned and purchase date(s) from get_purchase_info function
    Calculates the accumulation of shares, total share cost, average cost basis, current share price, current total stock value, and gain or loss value.
    """
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
    """
    Function input: end date of stock history from user input function, number of share(s) owned and purchase date(s) from get_purchase_info function, share costs and values, and gain or loss from get_purchase_details function
    Calculates the accumulation of shares, total share cost, average cost basis, current share price, current total stock value, and gain or loss value.
    """
    output = purchase_details(purchase_date, end_date, total_cost, total_shares, average_cost_basis, current_value, gain_or_loss)
    text = "<br>".join(output)
    if gain_or_loss > 0:
        text += "<br><span style='color:green;font-weight:bold'>Gain</span>"
    else:
        text += "<br><span style='color:red;font-weight:bold'>Loss</span>"
    div = Div(text=text, width=400,styles={'font-size': '20pt'})
    return div

def show_dashboard(p1, p2, p3, p4, div, company_name, choice, start_date, end_date):
    """
    Function inputs: charts from chart functions above, dashboard text, ticker symbol and company name, start and end dates of stock history.
    Adds a title and disclaimer to the dashboard layout.
    Organizes column layout in three columns.    
    Returns dashboard layout
    """
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

    # create a new row layout with p1_p3_column, p2_p4_column, and div_column as columns
    heatmap_bubble_row = row(p1_p3_column, p2_p4_column,div_column)

    # add heatmap_bubble_row to a new row layout
    dashboard_row = row(heatmap_bubble_row)

    # add the dashboard_row to the column layout
    col.children.append(dashboard_row)

    # show the dashboard
    show(col)

def main():
    choice, start_date, end_date, shares_input,purchase_date = user_input()
    stock_data, company_name = ticker(choice, start_date, end_date)
    df = dataframe(stock_data)
    p1 = create_scatter_plot(df,company_name)
    p2 = create_candlestick_chart(df,company_name)
    p3 = create_bar_chart(df,company_name)
    p4 = create_heatmap(df,company_name)
    purchase_info = get_purchase_info()
    total_cost, total_shares, average_cost_basis, current_value, gain_or_loss = share_price_at_dates(df, shares_input, purchase_date, purchase_info)
    purchase_details(purchase_date, end_date, total_cost, total_shares, average_cost_basis, current_value, gain_or_loss)
    div = create_dashboard_text(purchase_date, end_date, total_cost, total_shares, average_cost_basis, current_value, gain_or_loss)
    show_dashboard(p1, p2, p3, p4, div, company_name, choice, start_date, end_date)

if __name__ == "__main__":
    main() 

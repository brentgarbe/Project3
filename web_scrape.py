import pandas as pd
from sqlalchemy import *
import requests
from bs4 import BeautifulSoup
import datetime
from time import *
import yfinance as yf


def CIKfinder(stock):
    # stock = "msft"
    url = f'https://www.sec.gov/cgi-bin/browse-edgar?CIK={stock}&owner=exclude&action=getcompany'
    response = requests.get(url)
    soup = BeautifulSoup(response.text,'html.parser')
    # print(soup.prettify())
    alldata = soup.find('div', class_="companyInfo")
    results = alldata.find_all('a')
    CIKsplit=str(results[0]).split('CIK')
    CIKstr=str(CIKsplit[1])
    CIKNumber = str(CIKstr[1:11])
    #print(CIKNumber)
    Stock_list = []
    CIKNumber_list = []
    CIKNumber_list.append(CIKNumber)
    Stock_list.append(stock)
    cik_df = pd.DataFrame({"Ticker_Symbol":Stock_list,"CIK":CIKNumber_list})
    cik_df.to_sql('Stock_Stocks', engine, if_exists = 'append', index = False)

def PullStockMovingAvgs(ticker, api_key, time_period, resolution_CS, start_year, start_month, start_day):
    #This converts the dates into Epoch time for input into the code
    start_timeseries = round(datetime.datetime(start_year,start_month,start_day).timestamp())
    end_timeseries = round(time())
    #dates = pd.to_datetime(start_timeseries,unit='s')
    #This also pulls the stock date, open, close, high, low, and volume
    SMA = requests.get(f'https://finnhub.io/api/v1/indicator?symbol={ticker}&resolution={resolution_CS}&from={start_timeseries}&to={end_timeseries}&indicator=sma&timeperiod={time_period}&token={api_key}').json()
    EMA = requests.get(f'https://finnhub.io/api/v1/indicator?symbol={ticker}&resolution={resolution_CS}&from={start_timeseries}&to={end_timeseries}&indicator=ema&timeperiod={time_period}&token={api_key}').json()
    WMA = requests.get(f'https://finnhub.io/api/v1/indicator?symbol={ticker}&resolution={resolution_CS}&from={start_timeseries}&to={end_timeseries}&indicator=wma&timeperiod={time_period}&token={api_key}').json()
    timestamp = SMA['t']
    sma_calc = SMA['sma']
    ema_calc = EMA['ema']
    wma_calc = WMA['wma']
    open_price = SMA['o']
    close_price = SMA['c']
    high_price = SMA['h']
    low_price = SMA['l']
    volume = SMA['v']
    date_a = pd.to_datetime(timestamp, unit='s')
    #Stores everything as dictionaries before putting into dataframe
    stock_raw_data = {"Date":date_a,"Open":open_price,"Close":close_price,"High":high_price,"Low":low_price,"SMA":sma_calc,"EMA":ema_calc,"WMA":wma_calc,"Volume":volume}  
    #Makes the dataframe
    stockMA_df = pd.DataFrame(stock_raw_data)
    #Below makes the date into year, month, day
    stockMA_df['Date'] = pd.to_datetime(stockMA_df["Date"]).dt.date  
    # Add ticker symbol to what was pulled
    for index, row in stockMA_df.iterrows():
        stockMA_df.loc[index,"Ticker_Symbol"] = ticker
    #Re orders the data frame
    stockMA_df = stockMA_df.reindex(['Ticker_Symbol','Date','Open','Close','High','Low','SMA','EMA','WMA','Volume'], axis = 1)
    print(stockMA_df)
    stockMA_df.to_sql('Stock_History', engine, if_exists = 'append', index = False)

def Metrics(ticker,api_key):
    metrics = requests.get(f'https://finnhub.io/api/v1/stock/metric?symbol={ticker}&metric=all&token={api_key}').json()

    #This is a part of the metrics function above
    longTermDebt2EquityAnnual = metrics['metric']['longTermDebt/equityAnnual']
    bookValuePerShareAnnual = metrics['metric']['bookValuePerShareAnnual']
    bookValuePerShareQuarterly = metrics['metric']['bookValuePerShareQuarterly']
    cashFlowPerShareTTM = metrics['metric']['cashFlowPerShareTTM']
    freeCashFlowPerShareTTM = metrics['metric']['freeCashFlowPerShareTTM']
    revenuePerShareTTM = metrics['metric']['revenuePerShareTTM']


    #Setting up and building the DataFrame
    raw_metrics = {"Debt/Equity, Annual":longTermDebt2EquityAnnual,"Book Value/Share, Annual":bookValuePerShareAnnual,
                "Book Value/Share, Quarter":bookValuePerShareQuarterly,"CF/Share, TTM":cashFlowPerShareTTM, 
                "Free CF/Share, TTM":freeCashFlowPerShareTTM, "Revenue/Share, TTM":revenuePerShareTTM}
    #raw_metrics
    metrics_key = []
    metrics_value = []

    for key, value in raw_metrics.items():
        metrics_key.append(key)
        metrics_value.append(value)

    Metrics_df = pd.DataFrame({"Ticker_Symbol":ticker,"Data":metrics_key,"Values":metrics_value})
    print(Metrics_df)
    try:
        Metrics_df.to_sql('Stock_Metrics', engine, if_exists = 'append', index = False)
    except:
        print(f"ERROR {ticker} bad data somewhere")

def Peers(ticker,api_key):
    r = requests.get(f'https://finnhub.io/api/v1/stock/peers?symbol={ticker}&token={api_key}').json()

    # # Create the dataframe
    peers_df = pd.DataFrame({"Peers":r,})

    #Add Ticker Symbol
    for index, row in peers_df.iterrows():
        peers_df.loc[index,"Ticker_Symbol"] = ticker

    # #Re orders the data frame
    peers_df = peers_df.reindex(['Ticker_Symbol','Peers'], axis = 1)
    #print(metrics_df)
    try:
        print(peers_df.head(5))
        peers_df.to_sql('Stock_Peers', engine, if_exists = 'append', index = False)
    except:
        print(f"ERROR {ticker} bad data somewhere")

def Profile(ticker,api_key):
    r = requests.get(f'https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={api_key}').json()

    # unpack the json
    profile_key = []
    profile_value = []

    for key, value in r.items():
        profile_key.append(key)
        profile_value.append(value)
    # # Create the dataframe
    profile_df = pd.DataFrame({"Ticker_Symbol":ticker,"Profile":profile_key,"Values":profile_value})
    try:
        print(profile_df.head(5))
        profile_df.to_sql('Stock_Profile', engine, if_exists = 'append', index = False)
    except:
        print(f"ERROR {ticker} bad data somewhere")

def GetTargets(ticker,api_key,tech_ind_resolution):
    #Price Target
    price_target = requests.get(f'https://finnhub.io/api/v1/stock/price-target?symbol={ticker}&token={api_key}').json()

    #Stock Quote
    quote = requests.get(f'https://finnhub.io/api/v1/quote?symbol={ticker}&token={api_key}').json()

    #Aggregate Indicators
    tech_ind = requests.get(f'https://finnhub.io/api/v1/scan/technical-indicator?symbol={ticker}&resolution={tech_ind_resolution}&token={api_key}').json()

    names = ticker
    quotes = quote['c']

    target_H = price_target['targetHigh']
    target_L = price_target['targetLow']
    target_A = price_target['targetMean']
    target_update = price_target['lastUpdated'][:10]
    
    try:
        tech_analysis_B = tech_ind['technicalAnalysis']['count']['buy']
    except:
        tech_analysis_B = "NA"
    try:
        tech_analysis_S = tech_ind['technicalAnalysis']['count']['sell']
    except:
        tech_analysis_S = "NA"
    try:
        tech_analysis_N = tech_ind['technicalAnalysis']['count']['neutral']
    except:
        tech_analysis_N = "NA" 
    try:
        tech_analysis_sig = tech_ind['technicalAnalysis']['signal']
    except:
        tech_analysis_sig = "NA"


    raw_data_m = {"Quote":quotes,"High Target":target_H,"Low Target":target_L,
                "Avg Target":target_A,"Target Updated":target_update,"Buy":tech_analysis_B,
                "Sell":tech_analysis_S,"Neutral":tech_analysis_N,
                "Signal":tech_analysis_sig}

    targetHeader = []
    targetValue = []
    tickerSymb = []
    for k,v in raw_data_m.items():
        targetHeader.append(k)
        targetValue.append(v)
        tickerSymb.append(ticker)
    Target_df = pd.DataFrame({"Ticker_Symbol":tickerSymb,"Header":targetHeader,"Value":targetValue})
    
    try:
        print(Target_df.head(5))
        Target_df.to_sql('Stock_Target', engine, if_exists = 'append', index = False)
    except:
        print(f"ERROR {ticker} bad data somewhere")

def EPSdata(ticker, api_key,s_yr,s_mo,s_day):
    s_date = str(f'{s_yr}-{s_mo}-{s_day}')

    #This gets the current time
    end_timeseries = round(time())
    date_end = pd.to_datetime(end_timeseries,unit='s')

    #This breaks down to current date
    e_yr = str(date_end)[:4]
    e_mo = str(date_end)[5:7]
    e_day = str(date_end)[8:10]
    e_date = str(f'{e_yr}-{e_mo}-{e_day}')

    EPS = requests.get(f'https://finnhub.io/api/v1/calendar/earnings?from={s_date}&to={e_date}&symbol={ticker}&token={api_key}').json()
    date = []
    year = []
    quarter = []
    epsActual = []
    epsEstimate = []
    revenueActual = []
    revenueEstimate = []
    x=0

    for val in EPS['earningsCalendar']:
        date.append(EPS['earningsCalendar'][x]['date'])
        year.append(EPS['earningsCalendar'][x]['year'])
        quarter.append(EPS['earningsCalendar'][x]['quarter'])
        epsActual.append(EPS['earningsCalendar'][x]['epsActual'])
        epsEstimate.append(EPS['earningsCalendar'][x]['epsEstimate'])
        revenueActual.append(EPS['earningsCalendar'][x]['revenueActual'])
        revenueEstimate.append(EPS['earningsCalendar'][x]['revenueEstimate'])
        x=x+1

    #Setting up and building the DataFrame
    raw_EPS = {"Ticker_Symbol":ticker,"Date":date,"Year":year,"Quarter":quarter, "EPS_Actual":epsActual, 
                "EPS_Estimate":epsEstimate, "Actual_Revenue":revenueActual,"Estimated_Revenue":revenueEstimate}

    EPS_df = pd.DataFrame(raw_EPS)
    # Doing some extra stuff in pandas
    EPS_df['EPS_Diff'] = EPS_df['EPS_Actual']-EPS_df['EPS_Estimate']
    EPS_df['Revenue_Diff'] = EPS_df['Actual_Revenue']-EPS_df['Estimated_Revenue']

    try:
        print(EPS_df.head(5))
        EPS_df.to_sql('Stock_EPS', engine, if_exists = 'append', index = False)
    except:
        print(f"ERROR {ticker} bad data somewhere")

def Description(tSymbol):
    # use yfinance to download the company information
    stock = yf.Ticker(tSymbol)
    # get stock info
    r = stock.info
    # return just the business summary
    longbs = r['longBusinessSummary']
    # Pass the single row data frame item into a single list for the PD dataframe
    tSymbol = [tSymbol]
    longbs = [longbs]
    # pass it to a pandas dataframe
    profile_df = pd.DataFrame({"Ticker_Symbol":tSymbol, "Description":longbs})
    # Upload to SQL
    try:
        print(profile_df.head(5))
        profile_df.to_sql('Stock_Info', engine, if_exists = 'append', index = False)
    except:
        try:
            longbs = ["need to find this data"]
            profile_df = pd.DataFrame({"Ticker_Symbol":tSymbol,"Description":longbs})
            print(profile_df.head(5))
            profile_df.to_sql('Stock_Info', engine, if_exists = 'append', index = False)
        except:
            print(f"ERROR {tSymbol} bad data somewhere")

def Machine_learn(ticker):
    # loads from AWS
    engine = create_engine('sql')
    # This pulls from SQL
    data = pd.read_sql_table('Stock_History',engine)
    # Limit dataframe to your single stock
    ticker = 'AMZN'
    data = data.loc[(data["Ticker_Symbol"] == ticker), :]
    # Limit dataframe by time
    data = data.loc[(data["Date"] > "01/01/2020"), :]
    # Limit down to what you want to forecast
    df = data[["Date","Close"]]
    # Rename your columns for machine learning
    df = df.rename(columns={"Date":"ds","Close":"y"})
    # Prophet
    # m = Prophet(seasonality_mode='multiplicative')
    # m.add_seasonality('quarterly', period= 91.25, fourier_order=8, mode='additive')
    m = Prophet()
    m.fit(df)
    future = m.make_future_dataframe(periods=360)
    # each period is a day
    # 52 weeks
    # 365 days
    # 365 would be daily
    # 30.5 is monthly
    forecast = m.predict(future)
    # forecast[['ds','yhat','yhat_lower','yhat_upper']]
    # Poop out the image
    fig1 = m.plot(forecast)
    fig2 = m.plot_components(forecast)
    from fbprophet.plot import plot_plotly
    import plotly.offline as py
    py.init_notebook_mode()
    fig = plot_plotly(m, forecast)  # This returns a plotly Figure
    py.iplot(fig)
    #Add Ticker Symbol
    for index, row in forecast.iterrows():
        forecast.loc[index,"Ticker_Symbol"] = ticker
    #Re orders the data frame
    df = df.rename(columns={"Date":"ds","Close":"y"})
    forecast = forecast.reindex(['Ticker_Symbol','ds','yhat_lower','trend','yhat_upper'], axis = 1)
    forecast = forecast.rename(columns={"ds":"Date"})
    from datetime import datetime as dt
    forecast['Date'] = forecast['Date'].dt.normalize()
    # forecast.to_sql('Stock_Forecast', engine, if_exists = 'append', index = False)
    #forecast.head()
    forecast['Close'] = data['Close']
    merge_table = pd.merge(forecast, data, on="Date", how="outer")
    #merge_table
    final = merge_table[['Ticker_Symbol_x','Date','yhat_lower','trend','yhat_upper','Close_y']]
    final_forecast = final.rename(columns={"Ticker_Symbol_x":"Ticker_Symbol","Close_y":"Close"})
    final_forecast = final_forecast.fillna(0)
    # final_forecast.head(1000)
    final_forecast.to_sql('Stock_Forecast', engine, if_exists = 'append', index = False)


def Main(ticker):
    api_key = "api key"
    #Start date for candles and M.A. data
    start_year = 1980
    start_month = 1
    start_day = 1
    resolution_CS = 'D'
    time_period = 20
    # Resolution for target function
    tech_ind_resolution = 'D'
    #Start date for EPS data
    s_yr = 2010
    s_mo = 1
    s_day = 1
    # Activate Engine
    engine = create_engine('engine')
    print(ticker)
    try:
        PullStockMovingAvgs(ticker, api_key, time_period, resolution_CS, start_year, start_month, start_day)
    except:
        print(f"{ticker} had an error pulling the stock historical data")
    try:
        Metrics(ticker,api_key)
    except:
        print(f"{ticker} had an error pulling the stock metric data")
    try:
        Peers(ticker,api_key)
    except:
        print(f"{ticker} had an error pulling the stock peers data")
    try:
        Profile(ticker,api_key)
    except:
        print(f"{ticker} had an error pulling the stock profile data")
    try:
        GetTargets(ticker,api_key,tech_ind_resolution)
    except:
        print(f"{ticker} had an error pulling the stock target data")
    try:
        EPSdata(ticker, api_key,s_yr,s_mo,s_day)
    except:
        print(f"{ticker} had an error pulling the EPS data")
    try:
        Description(ticker)
    except:
        print(f"{ticker} had an error pulling the Description data")
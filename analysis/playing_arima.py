"""
Let's check this glorious repo from R in Python
Some explanation here https://youtu.be/10pvXLKw5dQ

Blogs:
1) Basic explanation ARIMA https://www.analyticsvidhya.com/blog/2018/08/auto-arima-time-series-modeling-python-r/
3) Comprehensive example is you would like to see what is ARIMA:
 https://datafai.com/auto-arima-using-pyramid-arima-python-package/
Library:
1) https://pypi.org/project/pmdarima/
2) http://alkaline-ml.com/pmdarima/0.9.0/setup.html
"""
import sys
import os
from covid_forecast.utils.data_io import get_data, download_csv_from_link
from covid_forecast.utils.visualizations import plt_arima_forecast,plt_arima_forecast_outsample
from tqdm import tqdm
import pmdarima as pm
from pmdarima.model_selection import train_test_split
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta
import pandas as pd

sys.path.insert(0,'../../../covid_forcast')
# where to save things
OUTPUT = '../outputs/arima/countries_2april2020'
os.makedirs(OUTPUT,exist_ok=True)
# In case you need to refresh the data, you need a folder /data
download_csv_from_link()
"""To save some time just run the part you want"""
run_example = False
run_real_cases = False
run_predict_next_3_days = True

"""List of countries to explore"""
data = get_data()
#country_list = ['China', 'Italy', 'Germany', 'India', 'Spain', 'United_Kingdom', 'United_States_of_America',
#                     'Lithuania', 'Cyprus']
country_list = data['countriesAndTerritories'].unique()

def filter_by_country(self, country_vname='Countries and territories', date_vname='DateRep'):
    """
    Filters given dataframe by country and sorts by date

    Args:
        self (pd.DataFrame): input df
        country_vname (str): obvious
        date_vname (str): obvious

    Returns:
        pd.DataFrame: filtered
    """
    data_out_df = self[self[country_vname] == country].sort_values(by=date_vname).copy()
    return data_out_df


if run_example:
    """Example"""
    # Author: Taylor Smith <taylor.smith@alkaline-ml.com
    # Load/split your data
    y = pm.datasets.load_wineind()
    train, test = train_test_split(y, train_size=150)
    # Fit your model
    model = pm.auto_arima(train, seasonal=True, m=12)
    # make your forecasts
    forecasts = model.predict(test.shape[0])  # predict N steps into the future
    # Visualize the forecasts (blue=train, green=forecasts)
    plt.clf()
    x = np.arange(y.shape[0])
    plt.plot(x[:150], train, c='blue')
    plt.plot(x[150:], forecasts, c='green')
    plt.savefig(OUTPUT+'/arima_example.png')
    plt.show()
    plt.clf()

if run_real_cases:
    """Real data ARIMA"""
    data = get_data()
    data['dateRep'] = pd.to_datetime(data['dateRep'],infer_datetime_format=True)
    for country in tqdm(['China','Italy', 'Germany','India', 'Spain', 'United_Kingdom', 'United_States',
            'Lithuania', 'Cyprus']):
        print('Working on: {}'.format(country))
        for variable in ['cases', 'deaths']:
            try:
                data_ = data[data['countriesAndTerritories'] == country].copy()
                data_ = data_.sort_values(by='dateRep')
                # Triming initial zeros
                remove_initia_zeros = np.trim_zeros(data_[variable]).__len__()
                #y = data_[variable][0:remove_initia_zeros]
                y = data_[variable][-remove_initia_zeros:]
                data_labels = data_['dateRep'][-remove_initia_zeros:]
                # taking 90% of the data
                length_for_training = round(y.__len__()*0.9)
                # taking the last 3
                #length_for_training = 4
                train, test = train_test_split(y, train_size=length_for_training)
                # Fit your model
                model = pm.auto_arima(train, seasonal=False, suppress_warnings=True)
                # make your forecasts
                #forecasts = model.predict(test.shape[0])  # predict N steps into the future
                forecasts, conf_int = model.predict(test.shape[0], return_conf_int=True)
                # Visualize the forecasts (blue=train, green=forecasts)
                plt_arima_forecast(y, forecasts, conf_int=conf_int,
                                   length_for_training=length_for_training,
                                   title=country,
                                   y_label=variable,
                                   x=data_labels,
                                   save_here=OUTPUT + '/arima_{}_{}.png'.format(country, variable))
            except Exception as e: print(e)

"""Let's predict next 3 days
Explanation/visualization some outputs as well in notebook"""
report_country = pd.DataFrame()
if run_predict_next_3_days:
    data = get_data()
    data['dateRep'] = pd.to_datetime(data['dateRep'], format="%d/%m/%Y")
    report_country = pd.DataFrame()
    report = pd.DataFrame()
    for country in tqdm(country_list):
        print('Working on: {}'.format(country))
        first_variable = pd.DataFrame()
        for variable in ['cases', 'deaths']:
            try:
                data_ = data[data['countriesAndTerritories'] == country].copy()
                data_ = data_.sort_values(by='dateRep')
                # Triming initial zeros
                remove_initia_zeros = np.trim_zeros(data_[variable]).__len__()
                # y = data_[variable][0:remove_initia_zeros]
                y = data_[variable][-remove_initia_zeros:]
                data_labels = data_['dateRep'][-remove_initia_zeros:]
                # taking the last 3. # Change it to any other amount
                lenght_for_forecast = 3
                # Fit your model
                model = pm.auto_arima(y, seasonal=False, suppress_warnings=True)
                # make your forecasts
                # predict N steps into the future
                forecasts, conf_int = model.predict(lenght_for_forecast, return_conf_int=True)
                # Adding labels for each new day
                data_labels = data_labels.to_list()
                for i in range(1,lenght_for_forecast+1):
                    data_labels.append(data_labels[-1] + timedelta(1))
                forecasts, conf_int = model.predict(lenght_for_forecast, return_conf_int=True)
                # Visualize the forecasts (blue=train, green=forecasts)
                plt_arima_forecast_outsample(y, forecasts, conf_int=conf_int,
                           title=country,
                           y_label=variable,
                           x=data_labels,
                           save_here=OUTPUT + '/forecast_next_3days_{}_{}.png'.format(country, variable))
                # To save the data
                df_for_data = pd.DataFrame()
                df_for_data = pd.DataFrame(y.to_list()+forecasts.tolist(),
                    columns=[variable])
                df_for_data['countriesAndTerritories'] = country
                df_for_data['dateRep'] = data_labels
                if first_variable.empty:
                    first_variable = df_for_data
                else:
                    first_variable = first_variable.merge(df_for_data, on=('dateRep', 'countriesAndTerritories'))
            except Exception as e: print(e)
        if report.empty:
            report = first_variable
        else:
            report = pd.concat([report, first_variable])
    if report_country.empty:
        report_country = report
    else:
        report_country = pd.concat([report_country, report])
    # Creation of report
    report_country.to_csv(OUTPUT+"/forecast_next_free_days.csv")



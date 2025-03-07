import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def load_data():
    path = os.path.dirname(__file__)
    #path = "C:/Users/spac-43/Desktop/Projects/"
    return(pd.read_csv(path+"/data/DKHousingPricesSample100k.csv",encoding = "utf-8"))

def format_print(data):
    for k,v in data.items():
        print("{}: {:.2f}kr".format(k,v))

def plot_bar_graph(dataframe):
    ax = plt.subplot(111)
    ind = np.arange(len(dataframe))
    offset = -0.2
    width = 0.2
    for i in dataframe:
        ax.bar(ind+offset, dataframe[i],width = width)
        offset+=width
    ax.set_xticks(ind)
    ax.set_xticklabels(dataframe.index)
    ax.legend(dataframe.columns)
    plt.show()

data = load_data()
a = data.groupby(by = ["city"])["purchase_price"].mean()
format_print(a)
a = data.groupby(["region","house_type"])["purchase_price"].mean().unstack("region")
plot_bar_graph(a)

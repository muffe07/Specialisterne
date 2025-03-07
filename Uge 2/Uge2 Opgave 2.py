import pandas as pd
import os

path = os.path.dirname(__file__)
def read_log():
    with open(path+"/data/app_log.txt", encoding = "utf-8") as f:
        data = []
        for i in f:
            line = i.split(" ")
            if(len(line)>=4):
                line = [line[0],line[1],line[2]," ".join(line[3:]).rstrip("\n")]
                data.append(line)
        dataframe = pd.DataFrame(data,columns = ["date","time","log_type","info"])

        return(dataframe)

def save_logtype(log_type,dataframe):
    file_name = path+"/output/"+log_type+".csv"
    save_data = dataframe[dataframe["log_type"]==log_type]
    save_data.to_csv(file_name,encoding='utf-8',index = False)

data = read_log()
log_types = set(data["log_type"])
for i in log_types:
    save_logtype(i,data)

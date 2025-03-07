import os
import csv
import re

def read_file(file_path):
    try:
        with open(file_path) as source:
            return(source.read())
    except OSError as e: 
        if e.errno == 22: #invalid argument
            print("path is invalid. Try another path")
        elif(e.errno == 2): #file not found
            print("could not find file or folder")
        else:
            print("unkown error while reading file:")
            print(e)

def write_file(file_path, data):
    try:
        with open(file_path, "w") as target:
            target.write(data)
    except OSError as e:
        if(e.errno == 13): #permission denied (write protection)
            print("target is write protected")
        else:
            print("unkown error while writing file")
            print(e)


def remove_invalid_lines(fileString):
    id_match = r"\d+"
    name_match = r"[a-zA-Z- ]+"
    email_match = r"[\w\-\.]+@([\w-]+\.)+[\w-]{2,}"
    purchase_match = r"[\d]+(\.[\d]+){0,1}"
    full_match = r"^"+id_match+r"\,"+name_match+r"\,"+email_match+r"\,"+purchase_match+r"$"
    new_file = ""
    for line in fileString.split("\n"):
        if(re.findall(full_match,line)==1):
            new_file+=(line+"\n")
    return new_file

path = os.path.dirname(__file__)
source = path+"/data/source_data.csv"
_, extension = os.path.splitext(source)
target = path+"/output/target_file"+extension

file = read_file(source)
new_file = remove_invalid_lines(file)
write_file(target,new_file)
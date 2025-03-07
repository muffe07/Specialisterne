import matplotlib.pyplot as plt
import collections
import numpy as np
from wordcloud import WordCloud 
import os

#I use my own data as I don't have access to the dataset
def load_names():
    names = []
    dirname = os.path.dirname(__file__)
    with open(dirname+"/data/navne.txt", encoding = "utf-8") as f:
        names = [i.split(" ")[0] for i in f]
    return names

names = load_names()

def count_characters(names_list):
    assert(type(names_list) == list)
    counts = {}
    for name in names_list:
        assert(type(name) == str)
        for character in name.lower():
            if(not character in counts):
                counts[character] = 1
            else:
                counts[character] += 1
    return counts

def create_character_histogram(names:list):
    char_count = count_characters(names)
    char_count = collections.OrderedDict(sorted(char_count.items()))
    plt.bar(char_count.keys(),char_count.values())
    plt.show()

def create_word_cloud(names:list):
    word_cloud = WordCloud().generate_from_frequencies(count_characters(names))
    plt.imshow(word_cloud)
    plt.axis("off")
    plt.show()

def show_name_length_distribution(names:list):
    name_length_count = collections.defaultdict(int)
    for i in names:
        name_length_count[len(i)]+=1
    name_length_count = collections.OrderedDict(sorted(name_length_count.items()))
    plt.plot(name_length_count.keys(),name_length_count.values())
    plt.show()

def name_analysis(names:list):
    name_length = list(map(lambda x: len(x),names))
    print("average name length: {}".format(np.average(name_length)))
    print("median name length: {}".format(np.median(name_length)))


name_analysis(names)
create_character_histogram(names)
create_word_cloud(names)
show_name_length_distribution(names)
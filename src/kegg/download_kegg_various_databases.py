import sys, re, os
import requests
from threading import Thread
import queue

import json

database = sys.argv[1]
output_folder = sys.argv[2]

rx_prefix_catch = re.compile(r'(\w+):\w+')

ko_list_url = "https://rest.kegg.jp/list/" + database

module_url_prefix = "https://rest.kegg.jp/get/"

def work(package):
        #print ("first", package, package[1]

        
        #try:
        print(module_url_prefix + package)
        detail = requests.get(module_url_prefix + package).text


        output_file = os.path.join(output_folder, package.replace(":", "_"))
        with open(output_file, 'a+') as output:
            output.write(detail)

exists = set()

for (head, dirs, files) in os.walk(output_folder):
    for file in files:
        exists.add(file)

ko_list = requests.get(ko_list_url).text
print (ko_list)

for line in ko_list.split("\n"):
    fields = line.strip().split("\t")
    #print (fields)
    if len(fields) == 2:
        kegg = fields[0]
        name = fields[1]

        if kegg.replace(":", "_") not in exists:

            work(kegg)


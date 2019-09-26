#from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json


con_code = 'CM' 

con_url = "https://www.ethnologue.com/country/" + con_code + "/languages"
con_html = requests.get(con_url)
con_bso = BeautifulSoup(con_html.content)

# find language names
con_lan_list_html = con_bso.findAll('div', {'class': 'title'})  
con_lan_list = []
for con_lan in con_lan_list_html:
    con_lan_list.append(con_lan.text.strip())
con_lan_n = len(con_lan_list)
print(str(con_lan_n) + " languages found in " + con_code)

# create iso dictionary
con_p_href_list = con_bso.select('p a[href]') 
con_lan_href_list = con_p_href_list[:-2]
con_lan_iso_list = [con_lan_href['href'] for con_lan_href in con_lan_href_list]
con_iso_dict = {}
for i in range(len(con_lan_list)):
    con_iso_dict[con_lan_list[i]] = con_lan_iso_list[i]

# create country dictionary
con_dict = dict.fromkeys(con_lan_list)

# loop to extract language information
n = 0 # count language
t0 = time.time()
del t0
print("Start downloading language data")
for lan in con_dict:
    ####################
    #        Log       #
    ####################
    # time remaining
    n += 1
    try:
        t_delta = time.time() - t0
        t_remaining_raw = t_delta * (con_lan_n - n + 1)
        t_remaining_tup = divmod(t_remaining_raw, 60)
        t_remaining_m = (str(int(t_remaining_tup[0])))
        if len(t_remaining_m) == 1:
            t_remaining_m = '0' + t_remaining_m
        t_remaining_s = str(round(t_remaining_tup[1]))  
        if len(t_remaining_s) == 1:
            t_remaining_s = '0' + t_remaining_s
        t_remaining = t_remaining_m + ':' + t_remaining_s
    except NameError:
        t_remaining = '99:99'
    dl_echo = "(" + str(n) + "/" + str(con_lan_n) + ") " + t_remaining + " Downloading " + lan
    #print(t_remaining_raw)
    print(dl_echo)
    t0 = time.time()
    ####################
    lan_iso = con_iso_dict[lan]
    lan_url = 'https://www.ethnologue.com' + lan_iso
    lan_html = requests.get(lan_url)
    lan_bso = BeautifulSoup(lan_html.content)
    # extract label name
    lan_label_html = lan_bso.findAll('div', {'class': 'field-label'})
    lan_label_list = [lan_label.text.strip() for lan_label in lan_label_html]
    # extract information
    lan_item_html = lan_bso.findAll('div', {'class': 'field-item'})
    lan_item_list = [lan_item.text.strip() for lan_item in lan_item_html][1:]
    # create language dictoinary
    lan_dict = {}
    i = 0
    j = 0
    i_max = len(lan_label_list)
    while i < i_max:
        key = lan_label_list[i]
        value = lan_item_list[j]
        #print(key, i, value)
        if key == 'Language Maps':
            #print(j, value)
            value_list = []
            while str.isdigit(lan_item_list[j][0]) == False:
                value = lan_item_list[j]
                value_list.append(value)
                j += 1
                #print(j, value)
            value = ','.join(value_list)
            #print(j, value_list)
            j -= 1
        lan_dict[key] = value
        j += 1
        i += 1
    # insert language dictionary 
    con_dict[lan] = lan_dict

# save con_dict as json
timestamp = str(int(time.time()))
file_name = 'con_dict_' + timestamp + '.json'
with open(file_name, 'w') as outfile:
    json.dump(con_dict, outfile)

# convert con_dict to dataframe
con_df = pd.DataFrame.from_dict(con_dict).transpose()

# save con_df as csv
timestamp = str(int(time.time()))
file_name = 'con_df_' + timestamp + '.csv'
con_df.to_csv(file_name, index=True)




# create language tree
# count number of columns (levels in the language tree)
tree_col_n = 1
for class_str in con_df['Classification']:
    n = len(class_str.split(','))
    if n > tree_col_n:
        tree_col_n = n
tree_col_n += 2 # one extra column for alternative name, another for dialects 

# count number of rows
tree_row_n = con_df.shape[0]

# create blank language tree
tree_index = con_df.index
lev_list = ['lev_' + str(i) for i in range(1,13)]
tree_col_names = ['alt_name'] + lev_list + ['dialect']
tree_df = pd.DataFrame(index = tree_index, columns = tree_col_names)
for index in tree_df.index:
    
    print('Converting data for: ' + index)

    # alternate names
    try:
        alt_name = con_dict[index]['Alternate Names']
        tree_df.loc[index, 'alt_name'] = alt_name 
    except KeyError:
        pass

    # dialects 
    try:
        dialect = con_dict[index]['Dialects']
        tree_df.loc[index, 'dialect'] = dialect 
    except KeyError:
        pass

    # parse classification
    class_str = con_dict[index]['Classification']
    class_list = class_str.split(', ')
    for i in range(len(class_list)):
        value = class_list[i]
        col_name = 'lev_' + str(i+1)
        tree_df.loc[index, col_name] = value

# save tree_df as csv
timestamp = str(int(time.time()))
file_name = 'tree_df_' + timestamp + '.csv'
tree_df.to_csv(file_name, index=True)

# sort language tree rows by level names
print('Sorting...')
tree_sorted_df = tree_df.sort_values(lev_list)
print('Complete')

# save sorted language tree
timestamp = str(int(time.time()))
file_name = 'tree_sorted_df_' + timestamp + '.csv'
tree_sorted_df.to_csv(file_name, index=True)



#######################
# create extra column #
#######################

# add location column
tree_sorted_extra_df = tree_sorted_df
tree_sorted_extra_df['loc'] = [0 for i in range(tree_sorted_df.shape[0])]
for index in tree_sorted_extra_df.index:
    try:
        loc_info = con_dict[index]['Location']
        tree_sorted_extra_df.loc[index, 'loc'] = loc_info
    except KeyError:
        pass

tree_sorted_extra_sorted_df = tree_sorted_extra_df.sort.value(lev_list + ['loc'])

timestamp = str(int(time.time()))
file_name = 'tree_sorted_extra_sorted_df_' + timestamp + '.csv'
tree_sorted_extra_sorted_df.to_csv(file_name, index=True)

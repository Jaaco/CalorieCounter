import os.path
from datetime import date
from time import strftime, localtime
import pandas as pd

import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin import firestore

"""
dir_file = os.path.dirname(__file__)
path = os.path.join(dir_file).replace("\\", "/")
os.chdir(path)"""


cred = credentials.Certificate('firebase-sdk.json')
firebase_admin.initialize_app(cred, {
  'projectId': 'calorie-counter-eb4ad',
})
print(cred)

db = firestore.client()


def ccn_create_new_user():
    user_input = str(input('Username:'))
    custom_token = auth.create_custom_token(user_input)
    return custom_token


def ccn_add_new_entry(name, cal, prot, fat, carbs, pp):
    doc_ref = db.collection(u'foods').document(str(name).capitalize())
    food_stat_dict = {'Calories': cal, 'Protein': prot, 'Fats': fat, 'Carbs': carbs, 'Gram or Ml per Piece or cup': pp}
    print(food_stat_dict)
    doc_ref.set(food_stat_dict)


def cc_check_for_file(food_input, amount, username):
    doc_ref = db.collection(u'foods').document(str(food_input['text']))
    print(doc_ref)
    food = doc_ref.get()
    food_dict = food.to_dict()
    factor = amount / 100
    new_food_dict = {'Calories': food_dict['Calories'], 'Protein': food_dict['Protein'],
                     'Carbs': food_dict['Carbs'], 'Fats': food_dict['Fats']}
    for stat in new_food_dict:
        new_food_dict[stat] = int(int(new_food_dict[stat]) * float(factor))
    print(new_food_dict, 'this is the list that should be added')

    doc_ref = db.collection('users').document(username).collection('days').document(str(date.today()))
    doc = doc_ref.get()
    if doc.exists:
        print('doc exists!')
        doc = doc.to_dict()
        for stat in doc:
            print(doc[stat], 'this is for every single line of the already existing stats')
            stat_int = int(doc[stat])
            print(new_food_dict[stat], 'this is the value that should be added')
            stat_int += int(new_food_dict[stat])
            doc[stat] = stat_int
            print((doc[stat]), 'this is for every single line of the new stats')
        print(doc, 'this should be the edited doc')
        doc_ref.set(doc)
    else:
        doc_ref.set(new_food_dict)
        print('this document does not exist')



def cc_add_today_stats(filename, header_needed, food_input, amount):
    data_row, data_name = cc_calculate_nutrients(food_input, amount)
    my_time = strftime('%H', localtime())
    column_list_foods = {'Name': [data_name], 'Calories': [data_row[0]], 'Protein': [data_row[1]],
                         'Carbs': [data_row[2]], 'Fats': [data_row[3]], 'Amount': [data_row[4]],
                         'Time': [my_time]}
    to_be_attached = pd.DataFrame(column_list_foods)
    to_be_attached.to_csv(filename, mode='a', index=False, header=header_needed)


def cc_read_list():
    docs = db.collection(u'foods').stream()
    list1 = []
    for doc in docs:
        dict1 = {'text': doc.id}
        list1.append(dict1)
    print(list1)
    return list1


def cc_calculate_nutrients(dict_input, amount):
    for stat in dict_input:
        dict_input[stat] = int(dict_input[stat]) * int(amount)
    return dict_input


def cc_get_stats():
    file_path = 'database/overall_stats/overall_data.csv'
    database = pd.read_csv(file_path)
    x = list(database['Date'])
    y = list(database['Calories'])
    print(x, y)
    return x, y


def cc_overall_stats():
    file_name = r"overall_data.csv"
    path_check = os.path.join('database/overall_stats', file_name).replace("\\", "/")
    if os.path.exists(path_check):
        if os.stat(path_check).st_size != 0:
            compare_files()
    else:
        file = open(r'database/overall_stats/overall_data.csv', "w+")
        build_overall_data_file()


def compare_files():
    file_path = 'database/overall_stats/overall_data.csv'
    data = pd.read_csv(file_path)
    list1 = os.listdir('database/single_days')
    list1[:] = [os.path.splitext(x)[0] for x in list1]
    list2 = list(data['Date'])
    list_joined = list(dict.fromkeys(list1 + list2))
    list_joined.sort()
    list_dif = list_difference(list1, list2)
    f = list1 + list_dif
    g = list(dict.fromkeys(f))
    files_dif = list_difference(g, list2)
    print('List 1: ', list1, 'List 2: ', list2)
    print('Different Files that should be matched: ', files_dif)
    for item in files_dif:
        data_row = calculate_day(item)
        column_list = {'Date': [item], 'Calories': [data_row[1]], 'Protein': [data_row[1]],
                       'Carbohydrates': [data_row[2]], 'Fats': [data_row[3]], 'AmountofFood': [data_row[4]]}

        conformed_data = pd.DataFrame(column_list)
        print(conformed_data)
        conformed_data.to_csv(file_path, mode='a', index=False, header=False, columns=column_list)
    data = pd.read_csv(file_path)


def build_overall_data_file():
    list1 = os.listdir('database/single_days')
    list1[:] = [os.path.splitext(x)[0] for x in list1]
    print(list1)
    counter = 0
    for item in list1:
        if counter == 0:
            header_var = True
        else:
            header_var = False
        data_row = calculate_day(item)
        column_list = {'Date': [item], 'Calories': [data_row[1]], 'Protein': [data_row[1]],
                       'Carbohydrates': [data_row[2]], 'Fats': [data_row[3]], 'AmountofFood': [data_row[4]]}

        conformed_data = pd.DataFrame(column_list)
        print(conformed_data)
        file_path = 'database/overall_stats/overall_data.csv'
        conformed_data.to_csv(file_path, mode='a', index=False, header=header_var, columns=column_list)
        counter += 1


def calculate_day(item):
    name = item + '.csv'
    data_of_item = pd.read_csv('database/single_days/{name}'.format(name=name))
    new_row = [None] * 7
    counter = 0
    for col in data_of_item:
        if col == 'Name':
            continue
        counter += 1
        new_row[counter] = sum_of_cols(data_of_item[col])
    return new_row


def sum_of_cols(col):
    number = 0
    for n in col:
        number += int(n)
    return number


def list_difference(list1, list2):
    list_dif = [i for i in list1 + list2 if i not in list1 or i not in list2]
    return list_dif



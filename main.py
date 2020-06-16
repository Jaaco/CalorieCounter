from os.path import join
from datetime import timedelta, date
import pandas as pd
from firebase_admin import firestore
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.properties import BooleanProperty, ObjectProperty, ListProperty
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.behaviors import FocusBehavior, ButtonBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.uix.widget import Widget
from matplotlib.dates import DateFormatter
from calorie_counter import cc_read_list, ccn_add_new_entry, cc_check_for_file, cc_overall_stats, cc_get_stats
from kivy.core.window import Window
import numpy as np
import matplotlib.pyplot as plt
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from pandas.plotting import register_matplotlib_converters
import seaborn as sns


class Statistics(Screen):

    def test_data_plotter(self):
        plot_data('week')
        self.ids.destination.add_widget(FigureCanvasKivyAgg(plt.gcf()))


class MyFigure(FigureCanvasKivyAgg):
    def __init__(self, **kwargs):
        plot_data(**kwargs)
        super(MyFigure, self).__init__(plt.gcf(), **kwargs)


def plot_data(number):
    register_matplotlib_converters()

    sns.set(font_scale=1.5, style="whitegrid")

    file_path = 'database/overall_stats/overall_data.csv'
    calories_dates = pd.read_csv(file_path,
                                 parse_dates=['Date'],
                                 index_col=['Date'],
                                 na_values=['999.99'])

    if number == 'week':
        td = 7
        title = 'Last Seven Days'
    if number == 'month':
        td = 30
        title = 'Last Thirty Days'
    else:
        pass
    calories_dates.sort_index(inplace=True)
    i = str((date.today()))
    u = str(date.today() - timedelta(days=td))
    calories_dates_week = calories_dates[u:i]
    var_one = np.array(list(calories_dates_week['Calories']))
    var_two = np.array(list(calories_dates_week.index.values))
    fig, ax = plt.subplots(figsize=(12, 12))

    ax.bar(var_two,
           var_one,
           color='#fdaba0FF')

    ax.set(xlabel='Date',
           ylabel='Calories (kcal)',
           title='This Week')

    calories_dates.index = pd.to_datetime(calories_dates.index)
    date_form = DateFormatter('%d-%m')
    ax.xaxis.set_major_formatter(date_form)


"""calories = [int(line) for line in y]
    ys = np.array(calories)
    y_axis_def = 3
    N = 5
    menMeans = (20, 35, 30, 35, 27)
    menStd = (2, 3, 4, 1, 2)
    ind = np.arange(N)  # the x locations for the groups
    width = 0.35  # the width of the bars
    figure, ax = plt.subplots()
    ax.set_ylabel('----------------------Calories-----------------')
    ax.set_ylim(top=3000, bottom=0)
    ax.set_xlabel('Dates')
    ax.set_title('This Week')
    ax.set_xticks(ind + width)
    ax.set_yticklabels(y)

    figure.patch.set_alpha(0.4)
    ax.patch.set_alpha(0.4)

    return plt.plot(dates, ys)"""


class LogIn(Screen):
    # global user
    # user = username
    pass


class MainWindow(Screen):
    amount_slider = ObjectProperty(None)
    food_rv = ListProperty()

    def data_new(self):
        return cc_read_list()

    def deleteEntry(self):
        global selected_food
        db.collection(u'foods').document(selected_food['text']).delete()

    def get_amount(self):
        global selected_food
        if int(self.amount_slider.value) != 0 and selected_food != ():
            #global user
            print(selected_food)
            food_row = cc_check_for_file(food_input=selected_food, amount=int(self.amount_slider.value), username='Lomena')
        else:
            print("Missing input arguments")


class AddFood(Screen):
    name1 = ObjectProperty(None)
    cal1 = ObjectProperty(None)
    prot1 = ObjectProperty(None)
    fat1 = ObjectProperty(None)
    carbs1 = ObjectProperty(None)
    pp1 = ObjectProperty(None)

    def submit_data_entry(self):
        if self.name1.text == '':
            print('Missing input arguments')
            return
        name = str(self.name1.text)
        cal = int(self.cal1.value)
        prot = int(self.prot1.value)
        fat = int(self.fat1.value)
        carbs = int(self.carbs1.value)
        pp = int(self.pp1.value)

        ccn_add_new_entry(name, cal, prot, fat, carbs, pp)
        global global_data
        global_data = cc_read_list()


class WindowManager(ScreenManager):
    pass


def invalidLogin():
    pop = Popup(title='Invalid Login',
                content=Label(text='Invalid username or password.'),
                size_hint=(None, None), size=(400, 400))
    pop.open()


def invalidForm():
    pop = Popup(title='Invalid Form',
                content=Label(text='Please fill in all inputs with valid information.'),
                size_hint=(None, None), size=(400, 400))

    pop.open()


class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior,
                                  RecycleGridLayout):
    """"""


class SelectableLabel(RecycleDataViewBehavior, Label):
    """ Add selection support to the Label """
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        """ Add selection on touch down """
        print(2)
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """ Respond to the selection of items in the view. """
        self.selected = is_selected
        if is_selected:
            global selected_food
            selected_food = rv.data[index]
        else:
            print(1)


class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.updateData()

    def my_callback(self, *args):
        self.updateData()

    def updateData(self):
        self.data = cc_read_list()


__version__ = "1.0.3"


global_data = cc_read_list()

db = firestore.client()


selected_food = ()

plt.plot([1, 23, 2, 4])
plt.ylabel('some numbers')

kv = Builder.load_file("caloriecounterkivy.kv")

sm = WindowManager()

screens = [MainWindow(name="main"), Statistics(name="statistics"), AddFood(name='addfood'), LogIn(name='login')]
for screen in screens:
    sm.add_widget(screen)

sm.current = "main"

Window.clearcolor = (1, 1, 1, 1)


class CalorieCounterApp(App):
    def build(self):
        return sm


if __name__ == "__main__":
    CalorieCounterApp().run()

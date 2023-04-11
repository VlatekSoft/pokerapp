import sqlite3
from datetime import datetime, timedelta

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.effects.scroll import ScrollEffect

class PokerAccountingApp(App):
    def build(self):
        # Connect to the SQLite database file
        self.database = sqlite3.connect('poker_accounting.db')

        # Create the "accounts" table if it doesn't already exist
        self.database.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                money INTEGER,
                datetime TEXT
            )
        ''')

        # Create the main layout for the app
        main_layout = BoxLayout(orientation='vertical')

        # Add an "Entrance" button and a "History" button to the main layout
        button_layout = BoxLayout(size_hint=(1, 0.1))
        entrance_button = Button(text='Сделать запись')
        entrance_button.bind(on_press=self.show_entrance_popup)
        button_layout.add_widget(entrance_button)

        history_button = Button(text='History')
        history_button.bind(on_press=self.show_history_popup)
        button_layout.add_widget(history_button)

        main_layout.add_widget(button_layout)

        # Add a label to display the total amount of money in the bank
        now_in_bank_layout = BoxLayout(size_hint=(1, 0.1))
        now_in_bank_layout.add_widget(Label(text='Now in Bank:'))
        self.now_in_bank_value_label = Label()
        now_in_bank_layout.add_widget(self.now_in_bank_value_label)
        main_layout.add_widget(now_in_bank_layout)

        # Add a table to display the balances for each player
        balance_layout = BoxLayout(orientation='vertical')
        balance_layout.add_widget(Label(text='Balance'))
        self.balance_grid = GridLayout(cols=2, size_hint=(1, None), row_default_height=40, row_force_default=True, spacing=5)

        
        balance_layout.add_widget(self.balance_grid)
        main_layout.add_widget(balance_layout)

        # Update the balance table with the current data from the database
        self.update_balance_table()

        # Return the main layout as the root widget for the app
        return main_layout

    def on_stop(self):
        # Close the database connection when the app is closed
        self.database.close()

    def show_entrance_popup(self, *args):
        # Create a popup window for entering a new account entry
        entrance_popup = Popup(title='Entrance', size_hint=(0.6, 0.6))
        entrance_layout = BoxLayout(orientation='vertical')

        # Add text input fields for entering a name and money amount
        name_input = TextInput(hint_text='Name')
        entrance_layout.add_widget(name_input)

        money_input = TextInput(hint_text='Money')
        entrance_layout.add_widget(money_input)

        # Add a "Send" button to submit the new account entry
        send_button = Button(text='Send')
        send_button.bind(on_press=lambda *args: self.add_account_entry(name_input.text, money_input.text))
        entrance_layout.add_widget(send_button)

        # Add the layout to the popup window and open it
        entrance_popup.add_widget(entrance_layout)
        entrance_popup.open()

    def show_history_popup(self, *args):
        # Create a popup window for displaying the history of account entries
        history_popup = Popup(title='History', size_hint=(0.8, 0.8))
        history_layout = BoxLayout(orientation='vertical')

        # Add a table to display the history data
        history_grid = GridLayout(cols=3, size_hint=(1, None), row_default_height=40, row_force_default=True, spacing=5)

        # Add column headers to the history table
        history_grid.add_widget(Label(text='DateTime'))
        history_grid.add_widget(Label(text='Name'))
        history_grid.add_widget(Label(text='Money'))

        # Get all account entries from the database and add them to the history table
        results = self.database.execute('SELECT datetime, name, money FROM accounts ORDER BY datetime DESC').fetchall()
        # Get the number of rows  and set the height of the grid accordingly¶
        history_grid.height = history_grid.row_default_height * len(results)
        for result in results:
            history_grid.add_widget(Label(text=result[0]))
            history_grid.add_widget(Label(text=result[1]))
            history_grid.add_widget(Label(text=str(result[2])))
        
        # Create a ScrollView and add the history grid to it
        scrollview = ScrollView(effect_cls=ScrollEffect)
        scrollview.add_widget(history_grid)

        # Add the ScrollView to the layout and open the popup window
        history_layout.add_widget(scrollview)

        # Create a box layout to hold the delete button and add it to the history layout
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=5)
        button_layout.add_widget(Button(text='Delete Last Record', on_release=self.delete_last_record, size_hint=(0.3, 1)))

        history_layout.add_widget(button_layout)

        # Open the popup window
        history_popup.add_widget(history_layout)
        history_popup.open()

    def delete_last_record(self, *args):
        # Delete the last record from the database
        self.database.execute('DELETE FROM accounts WHERE rowid = (SELECT MAX(rowid) FROM accounts)')
        self.database.commit()

        # Refresh the history popup
        self.show_history_popup()
        
    def add_account_entry(self, name, money):
        # Convert the money input to an integer
        try:
            money = int(money)
        except ValueError:
            return

########################################
        # Add the new account entry to the  "accounts" table with the current date and time
        now = datetime.now()
        datetime_str = now.strftime('%Y-%m-%d %H:%M:%S')
        self.database.execute('INSERT INTO accounts (name, money, datetime) VALUES (?, ?, ?)', (name, money, datetime_str))
        self.database.commit()

        # Update the [balance table](poe://www.poe.com/_api/key_phrase?phrase=balance%20table&prompt=Tell%20me%20more%20about%20balance%20table.) and the now in [bank label](poe://www.poe.com/_api/key_phrase?phrase=bank%20label&prompt=Tell%20me%20more%20about%20bank%20label.)
        self.update_balance_table()
        self.update_now_in_bank_label()

    def update_balance_table(self):
        # Clear the balance table
        self.balance_grid.clear_widgets()

        # Add column headers to the balance table
        self.balance_grid.add_widget(Label(text='Name'))
        self.balance_grid.add_widget(Label(text='Money'))

        # Get the current balance for each player from the database and add it to the balance table
        results = self.database.execute("SELECT name, SUM(money), datetime FROM accounts WHERE strftime('%s', datetime) > strftime('%s', 'now', '-23 hour') GROUP BY name").fetchall()
        self.balance_grid.height = self.balance_grid.row_default_height*len(results)
        print(results)
        #print(type(results[0][1]))
        # Create a ScrollView and add the history grid to it
        #scrollview = ScrollView(effect_cls=ScrollEffect)
        #scrollview.add_widget(self.balance_grid)

        # Add the ScrollView to the layout and open the popup window
        #history_layout.add_widget(scrollview)

        balances = {}
        for result in results:
            name = result[0]
            money = result[1]

            if name in balances:
                balances[name] += money
            else:
                balances[name] = money

            self.balance_grid.add_widget(Label(text=name))
            self.balance_grid.add_widget(Label(text=str(balances[name])))
           # self.balance_grid.add_widget(Label(text=datetime_str))

    def update_now_in_bank_label(self):
        # Get the total amount of money in the bank from the database
        total_money = self.database.execute("SELECT SUM(money) FROM accounts WHERE strftime('%s', datetime) > strftime('%s', 'now', '-23 hour') ").fetchall()[0]
        print(total_money)
        # Update the now in bank label with the total amount of money
        self.now_in_bank_value_label.text = str(total_money).strip('(),')

if __name__ == '__main__':
    PokerAccountingApp().run()
from PyQt5 import QtWebEngineWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QGraphicsColorizeEffect
from PyQt5.uic import loadUi
import yfinance as yf
import database_connector
import data_analysis
import plotly.graph_objs as go
import plotly.express as px


class AnalysePortfolio(QMainWindow):
    database_connector = database_connector.DatabaseConnector()
    data_analysis = data_analysis.DataAnalysis()
    current_portfolio = ''
    stocks = []
    values = []
    past_values = []
    dates = []

    def __init__(self):
        super().__init__()

        # read the window layout from file
        loadUi("static/analyse_portfolio.ui", self)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.browser = QtWebEngineWidgets.QWebEngineView(self)
        self.vlayout.addWidget(self.browser)

        try:
            self.fill_combo_box()
        except TypeError as e:
            print(e)

        try:
            self.load_portfolio()
        except Exception as e:
            print('Preventing from crashing as there is no portfolio in database')
            print(e)

        self.load_button.clicked.connect(self.load_portfolio)

        # self.portfolio_returns_button.clicked.connect(self.go_to_portfolio_charts)
        # self.analyse_corr_button.clicked.connect(self.go_to_correlation_charts)
        # self.analyse_sharpe_button.clicked.connect(self.go_to_sharpe_charts)

    def load_portfolio(self):

        data = self.database_connector.select_from(self.portfolio_combobox.currentText())

        AnalysePortfolio.stocks = []
        AnalysePortfolio.values = []
        AnalysePortfolio.past_values = []
        AnalysePortfolio.dates = []

        for i in range(len(data)):
            AnalysePortfolio.dates.append(data[i][3])
            if data[i][0] in AnalysePortfolio.stocks:
                stock_index = AnalysePortfolio.stocks.index(data[i][0])
                AnalysePortfolio.values[stock_index] += float(data[i][1]) * round(
                    yf.Ticker(data[i][0]).history(period='1d')['Close'][0], 2)
                AnalysePortfolio.past_values[stock_index] += float(data[i][2])
            else:
                AnalysePortfolio.stocks.append(data[i][0])
                AnalysePortfolio.values.append(
                    round(float(data[i][1]) * (yf.Ticker(data[i][0]).history(period='1d')['Close'][0]), 2))
                AnalysePortfolio.past_values.append(round(float(data[i][2]), 2))

        # fig = go.Figure(data=[go.Pie(values=AnalysePortfolio.values, labels=AnalysePortfolio.stocks, hole=.4)])
        fig = px.pie(values=AnalysePortfolio.values, names=AnalysePortfolio.stocks, hole=.4,
                     color_discrete_sequence=px.colors.sequential.Viridis[::-1])
        # fig.layout.template = 'plotly_dark'
        self.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))

        self.value.setText(str(round(sum(AnalysePortfolio.values), 2)) + ' $')

        # creating a color effect
        color_effect = QGraphicsColorizeEffect()

        # TODO: Compering the current value with the value from the date of portfolio last edit
        change = round(sum(AnalysePortfolio.values) - sum(AnalysePortfolio.past_values), 2)
        percentage_change = round((change / sum(AnalysePortfolio.past_values)) * 100, 2)
        if change > 0.0:
            profit = '+' + str(change) + ' $' + '       +' + str(percentage_change) + ' %'
            # setting color to color effect
            color_effect.setColor(Qt.darkGreen)
        elif change == 0.0:
            profit = str(abs(change)) + ' $' + '       ' + str(percentage_change) + ' %'
            color_effect.setColor(Qt.gray)
        else:
            profit = str(change) + ' $' + '       ' + str(percentage_change) + ' %'
            # setting color to color effect
            color_effect.setColor(Qt.red)

        self.change.setText(profit)
        # adding color effect to the label
        self.change.setGraphicsEffect(color_effect)

        # TODO: Make the same thing with all components

        self.clear()

        for i in range(len(data)):
            item = QTableWidgetItem(str(data[i][0]))
            item2 = QTableWidgetItem(
                str(round(float(data[i][1]) * (yf.Ticker(data[i][0]).history(period='1d')['Close'][0]), 2)) + ' $')
            item3 = QTableWidgetItem(str(data[i][3]))
            component_change = round(
                float(data[i][1]) * (yf.Ticker(data[i][0]).history(period='1d')['Close'][0]) - data[i][2], 2)
            font = QFont()
            font.setBold(True)
            if component_change > 0.0:
                component_change = '+' + str(component_change) + ' $'
                color = Qt.darkGreen
            elif component_change == 0.0:
                component_change = str(abs(component_change)) + ' $'
                color = Qt.gray
            else:
                component_change = str(component_change) + ' $'
                color = Qt.red
            item4 = QTableWidgetItem(component_change)
            # item4.setBackground(color)
            item4.setForeground(color)
            item4.setFont(font)
            component_percentage_change = round(((float(data[i][1]) * (
                yf.Ticker(data[i][0]).history(period='1d')['Close'][0]) - data[i][2]) / data[i][2]) * 100, 2)
            if component_percentage_change > 0.0:
                component_percentage_change = '+' + str(component_percentage_change) + ' %'
            elif component_percentage_change == 0.0:
                component_percentage_change = str(abs(component_percentage_change)) + ' %'
                color = Qt.gray
            else:
                component_percentage_change = str(component_percentage_change) + ' %'
            item5 = QTableWidgetItem(component_percentage_change)
            # item5.setBackground(color)
            item5.setForeground(color)
            item5.setFont(font)
            row_position = self.portfolio_table.rowCount()
            self.portfolio_table.insertRow(row_position)
            self.portfolio_table.setItem(row_position, 0, item)
            self.portfolio_table.setItem(row_position, 1, item2)
            self.portfolio_table.setItem(row_position, 2, item3)
            self.portfolio_table.setItem(row_position, 3, item4)
            self.portfolio_table.setItem(row_position, 4, item5)

        try:
            sharpe_ratio = self.data_analysis.sharpe_ratio(AnalysePortfolio.stocks, AnalysePortfolio.values)
            self.sharpe_label.setText('Sharpe ratio: ' + str(round(sharpe_ratio, 2)))
        except Exception as e:
            print('DUPA: ')
            print(e)

        corr_data = self.data_analysis.correlation(AnalysePortfolio.stocks)
        (corr, extremes) = corr_data
        keys = list(extremes)
        if len(keys) == 1:
            (a, b) = keys[0]
            self.corr_label.setText('Correletion between ' + a + ' and ' + b + ': ' + str(round(extremes[keys[0]], 2)))
        else:
            (a, b) = keys[0]
            (c, d) = keys[1]
            self.corr_label.setText('Highest correletion between ' + a + ' and ' + b + ': ' + str(
                round(extremes[keys[0]], 2)) + '\n' + 'Lowest correletion between ' + c + ' and ' + d + ': ' + str(
                round(extremes[keys[1]], 2)))

        vol_data = self.data_analysis.volatility(AnalysePortfolio.stocks, AnalysePortfolio.values)
        (annual, daily) = vol_data
        self.risk_label.setText(
            'Daily volatility: ' + str(round(daily * 100, 2)) + ' %\n' + 'Annual volatility: ' + str(
                round(annual * 100, 2)) + ' %')

    # fill portfolio_combobox with stock names
    def fill_combo_box(self):
        for name in self.database_connector.show_tables():
            if name == 'portfolio_names':
                continue
            self.portfolio_combobox.addItem(name)

    def clear(self):
        for i in reversed(range(self.portfolio_table.rowCount())):
            self.portfolio_table.removeRow(i)
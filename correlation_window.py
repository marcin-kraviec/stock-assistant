from PyQt5 import QtWebEngineWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow
from PyQt5.uic import loadUi
import data_analysis
import plotly.graph_objs as go
from analyse_portfolio import AnalysePortfolio
import logging


class CorrelationWindow(QMainWindow):

    # initialise data_analysis to provide methods for calculations
    data_analysis = data_analysis.DataAnalysis()

    def __init__(self):
        super().__init__()

        # read the window layout from file
        loadUi("static/ui_files/portfolio_charts.ui", self)
        self.setWindowFlags(Qt.FramelessWindowHint)

        # setup a webengine for plots
        self.browser = QtWebEngineWidgets.QWebEngineView(self)
        self.vlayout.addWidget(self.browser)

        # default state
        try:
            self.show_correlation_plot()
        except ValueError as e:
            logging.error(str(e))

        self.portfolio_charts_title_label.setText('Correlation matrix')
        self.info_label.setText('This window provides a matrix of correlation between portfolio components. The lighter the color the higher correlation.')

    def show_correlation_plot(self):

        # culculating correlation
        data = self.data_analysis.correlation(AnalysePortfolio.stocks)
        (corr, extremes) = data

        def df_to_plotly(df):
            return {'z': df.values.tolist(),
                    'x': df.columns.tolist(),
                    'y': df.index.tolist(),
                    'zmin': 0, 'zmax': 1}

        # initialise figure (heatmap plot)
        fig = go.Figure(data=go.Heatmap(df_to_plotly(corr), colorscale='Viridis'))

        # changing plot into html file so that it can be displayed with webengine
        self.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))

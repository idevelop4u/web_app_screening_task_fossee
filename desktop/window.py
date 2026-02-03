import sys, requests, os
from pathlib import Path
from dotenv import load_dotenv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

load_dotenv(Path(__file__).parent / '.env')

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, is_dark=False):
        self.bg = '#1e1e1e' if is_dark else '#f8f9fa'
        self.fg = '#f8f9fa' if is_dark else '#212529'
        fig = Figure(figsize=(5, 3), dpi=100, facecolor=self.bg)
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor(self.bg)
        self.axes.tick_params(colors=self.fg, labelsize=8)
        for spine in self.axes.spines.values():
            spine.set_color('#333333' if is_dark else '#dee2e6')
        super(MplCanvas, self).__init__(fig)

class ChemicalVisualizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemical Equipment Visualizer")
        self.setGeometry(100, 100, 1100, 850)
        self.is_dark = False
        self.current_dist = None
        self.init_ui()
        self.apply_professional_theme()
        self.fetch_history()

    def init_ui(self):
        self.central = QWidget()
        self.central.setObjectName("appContainer")
        self.setCentralWidget(self.central)
        self.main_layout = QVBoxLayout(self.central)
        self.main_layout.setContentsMargins(50, 40, 50, 40)
        self.main_layout.setSpacing(25)

        header = QHBoxLayout()
        self.title_lbl = QLabel("Chemical Equipment Visualizer")
        self.title_lbl.setObjectName("headerTitle")
        self.pdf_btn = QPushButton("Generate PDF Report")
        self.pdf_btn.setObjectName("themeToggle")
        self.pdf_btn.clicked.connect(self.generate_pdf_report)
        self.theme_btn = QPushButton("Switch to Dark Mode")
        self.theme_btn.setObjectName("themeToggle")
        self.theme_btn.clicked.connect(self.toggle_theme)
        header.addWidget(self.title_lbl)
        header.addStretch()
        header.addWidget(self.pdf_btn)
        header.addWidget(self.theme_btn)
        self.main_layout.addLayout(header)

        self.import_card = QFrame()
        self.import_card.setObjectName("card")
        import_layout = QHBoxLayout(self.import_card)
        import_layout.addWidget(QLabel("Data Import: Upload CSV for analysis"))
        self.up_btn = QPushButton("Upload and Analyze")
        self.up_btn.setObjectName("executeBtn")
        self.up_btn.clicked.connect(self.upload_csv)
        import_layout.addStretch()
        import_layout.addWidget(self.up_btn)
        self.main_layout.addWidget(self.import_card)

        grid = QHBoxLayout()
        self.stats_card = QFrame()
        self.stats_card.setObjectName("card")
        self.stats_card.setFixedWidth(300)
        stats_layout = QVBoxLayout(self.stats_card)
        self.lbl_count = QLabel("--")
        self.lbl_count.setObjectName("statsValue")
        stats_layout.addWidget(QLabel("Total Equipment Units"))
        stats_layout.addWidget(self.lbl_count)
        self.lbl_temp = QLabel("--")
        self.lbl_temp.setObjectName("statsValue")
        stats_layout.addWidget(QLabel("Avg Operating Temp"))
        stats_layout.addWidget(self.lbl_temp)
        
        self.chart_card = QFrame()
        self.chart_card.setObjectName("card")
        self.chart_layout = QVBoxLayout(self.chart_card)
        self.canvas = MplCanvas(self, self.is_dark)
        self.chart_layout.addWidget(self.canvas)
        
        grid.addWidget(self.stats_card)
        grid.addWidget(self.chart_card)
        self.main_layout.addLayout(grid)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["File Name", "Date", "Avg Temp"])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.main_layout.addWidget(self.table)

    def apply_professional_theme(self):
        bg = "#121212" if self.is_dark else "#ffffff"
        txt = "#f8f9fa" if self.is_dark else "#212529"
        accent = "#0d6efd"
        card_bg = "#1e1e1e" if self.is_dark else "#f8f9fa"
        border = "#333333" if self.is_dark else "#dee2e6"
        alt_row = "#252525" if self.is_dark else "#f1f3f5"

        self.setStyleSheet(f"""
            QMainWindow, #appContainer {{ background-color: {bg}; }}
            #headerTitle {{ font-size: 26px; font-weight: bold; color: {txt}; }}
            #card {{ background-color: {card_bg}; border: 1px solid {border}; border-radius: 12px; }}
            #executeBtn {{ background-color: {accent}; color: white; padding: 12px; border-radius: 6px; font-weight: bold; }}
            #statsValue {{ font-size: 24px; font-weight: bold; color: {accent}; }}
            QLabel {{ color: {txt}; font-family: 'Segoe UI'; }}
            QTableWidget {{ 
                background-color: transparent; border: none; color: {txt}; 
                alternate-background-color: {alt_row}; gridline-color: transparent;
            }}
            QHeaderView::section {{ background-color: {card_bg}; color: {accent}; font-weight: bold; border: none; border-bottom: 2px solid {border}; }}
        """)

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.theme_btn.setText("Switch to Light Mode" if self.is_dark else "Switch to Dark Mode")
        self.apply_professional_theme()
        
        self.canvas.deleteLater()
        self.canvas = MplCanvas(self, self.is_dark)
        self.chart_layout.addWidget(self.canvas)
        
        if self.current_dist:
            self.update_chart(self.current_dist)

    def upload_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV (*.csv)")
        if path:
            with open(path, 'rb') as f:
                api_username = os.getenv('API_USERNAME', 'puspal')
                api_password = os.getenv('API_PASSWORD', 'admin12345')
                api_url = os.getenv('API_URL', 'http://127.0.0.1:8000')
                auth = (api_username, api_password)
                res = requests.post(f"{api_url}/api/upload/", files={'file': f}, auth=auth)
                if res.status_code == 200:
                    data = res.json()
                    self.lbl_count.setText(str(data['total_count']))
                    self.lbl_temp.setText(f"{data['averages']['temp']:.2f} C")
                    self.current_dist = data['distribution'] 
                    self.update_chart(self.current_dist)
                    self.fetch_history()

    def update_chart(self, dist):
        self.canvas.axes.cla()
        self.canvas.axes.bar(dist.keys(), dist.values(), color='#0d6efd')
        self.canvas.draw()

    def fetch_history(self):
        try:
            api_username = os.getenv('API_USERNAME', 'puspal')
            api_password = os.getenv('API_PASSWORD', 'admin12345')
            api_url = os.getenv('API_URL', 'http://127.0.0.1:8000')
            auth = (api_username, api_password)
            res = requests.get(f"{api_url}/api/upload/", auth=auth)
            if res.status_code == 200:
                data = res.json()[:5]
                self.table.setRowCount(len(data))
                for i, item in enumerate(data):
                    self.table.setItem(i, 0, QTableWidgetItem(item['file_name']))
                    self.table.setItem(i, 1, QTableWidgetItem(item['uploaded_at']))
                    self.table.setItem(i, 2, QTableWidgetItem(f"{item['results']['averages']['temp']} C"))
        except: pass

    def generate_pdf_report(self):
        try:
            api_username = os.getenv('API_USERNAME', 'puspal')
            api_password = os.getenv('API_PASSWORD', 'admin12345')
            api_url = os.getenv('API_URL', 'http://127.0.0.1:8000')
            auth = (api_username, api_password)
            res = requests.get(f"{api_url}/api/export-pdf/", auth=auth)
            if res.status_code == 200:
                file_path = QFileDialog.getSaveFileName(self, "Save PDF Report", "Equipment_Report.pdf", "PDF (*.pdf)")[0]
                if file_path:
                    with open(file_path, 'wb') as pdf_file:
                        pdf_file.write(res.content)
            else:
                print("Failed to generate report")
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ChemicalVisualizerApp()
    win.show()
    sys.exit(app.exec_())
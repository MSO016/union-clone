from PyQt5.QtWidgets import QMessageBox
from app.views.main_view import MainView
from app.models.solutions_model import SolutionsModel
from app.views.solution_detail_view import SolutionDetailView
class MainController:
    def __init__(self):
        self.model = SolutionsModel()
        self.view = MainView(self)
        self.current_solutions = []
    def handle_brand_click(self, brand):
        try:
            solutions = self.model.get_solutions_by_brand(brand)
            self.current_solutions = solutions
            if solutions:
                detail_view = SolutionDetailView(solutions, brand)
                detail_view.exec_()
                return
            QMessageBox.information(self.view, 'Informa├º├úo', f'Nenhuma solu├º├úo dispon├¡vel para {brand}')
            return
        except Exception as e:
            QMessageBox.critical(self.view, 'Erro', f'Erro ao carregar solu├º├Áes: {str(e)}')
    def handle_search(self, text):
        if len(text) >= 3:
            try:
                results = self.model.search_solutions(text)
                self.show_search_results(results)
            except Exception as e:
                print(f'Erro na busca: {str(e)}')
    def run(self):
        self.view.show()

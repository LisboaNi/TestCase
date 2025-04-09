from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from employees.models import Employee
from .models import BoardTrello
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from unittest import mock
from accounts.models import UserModel

class BoardTrelloCRUDTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.test_user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword'
        )
        try:
            self.company_account = UserModel.objects.get(user=self.test_user)
        except UserModel.DoesNotExist:
            self.company_account = UserModel.objects.create(user=self.test_user)

        self.employee = Employee.objects.create(
            user=self.test_user,
            accounts=self.company_account,  # Associe o UserModel aqui
            name='Test Employee'
        )
        self.client.force_login(self.test_user)

    def _authenticate_user(self):
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        auth_middleware = AuthenticationMiddleware(lambda x: x)
        auth_middleware.process_request(request)
        request.user = self.test_user
        return request

    def test_board_create_view(self):
        """Testa a criação de um novo board."""
        board_data = {'nome_board': 'Meu Board de Teste', 'trello_board_id': 'TESTBOARD123'}
        response = self.client.post(reverse('board-create'), board_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BoardTrello.objects.count(), 1)
        board = BoardTrello.objects.first()
        self.assertEqual(board.nome_board, 'Meu Board de Teste')
        self.assertEqual(board.trello_board_id, 'TESTBOARD123')
        self.assertEqual(board.employee, self.employee)

    def test_board_list_view(self):
        """Testa a visualização da lista de boards do employee logado."""
        BoardTrello.objects.create(employee=self.employee, nome_board='Board 1', trello_board_id='BOARD1')
        BoardTrello.objects.create(employee=self.employee, nome_board='Board 2', trello_board_id='BOARD2')
        response = self.client.get(reverse('board-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Board 1')
        self.assertContains(response, 'Board 2')

        # Cria um board para outro usuário e verifica que não aparece na lista
        other_user = User.objects.create_user(username='other@example.com', password='otherpassword')
        try:
            other_account = UserModel.objects.get(user=other_user)
        except UserModel.DoesNotExist:
            # Gere um CNPJ único para o teste
            other_account = UserModel.objects.create(user=other_user, cnpj='TEST_CNPJ_OTHER')
        other_employee = Employee.objects.create(user=other_user, accounts=other_account, name='Other Employee')
        BoardTrello.objects.create(employee=other_employee, nome_board='Other Board', trello_board_id='OTHERBOARD')
        response = self.client.get(reverse('board-list'))
        self.assertNotContains(response, 'Other Board')

    def test_board_update_view(self):
        """Testa a atualização de um board."""
        board = BoardTrello.objects.create(employee=self.employee, nome_board='Board Antigo', trello_board_id='OLD123')
        updated_data = {'nome_board': 'Board Novo', 'trello_board_id': 'NEW456'}
        response = self.client.post(reverse('board-update', args=[board.pk]), updated_data)
        self.assertEqual(response.status_code, 302)
        updated_board = BoardTrello.objects.get(pk=board.pk)
        self.assertEqual(updated_board.nome_board, 'Board Novo')
        self.assertEqual(updated_board.trello_board_id, 'NEW456')

    def test_board_delete_view(self):
        """Testa a exclusão de um board."""
        board = BoardTrello.objects.create(employee=self.employee, nome_board='Board a Deletar', trello_board_id='DELETE1')
        response = self.client.post(reverse('board-delete', args=[board.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BoardTrello.objects.count(), 0)

class AtualizarCardsTrelloViewTests(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword'
        )
        try:
            self.company_account = UserModel.objects.get(user=self.test_user)
        except UserModel.DoesNotExist:
            self.company_account = UserModel.objects.create(user=self.test_user)

        self.employee = Employee.objects.create(
            user=self.test_user,
            accounts=self.company_account,
            name='Test Employee',
            trello_username='TEST_USER',  # Correção aqui
            trello_token='TEST_TOKEN'     # Correção aqui
        )
        self.client.force_login(self.test_user)
        self.board1 = BoardTrello.objects.create(employee=self.employee, nome_board='Board 1', trello_board_id='BOARD1')
        self.board2 = BoardTrello.objects.create(employee=self.employee, nome_board='Board 2', trello_board_id='BOARD2')

    @mock.patch('trello.views.sync_trello_cards_for_employee')
    def test_atualizar_cards_view(self, mock_sync_cards):
        """Testa a função de atualização de cards do Trello."""
        url = reverse('atualizar-cards-trello', args=[self.employee.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mensagem": "Sincronização concluída com sucesso!"})
        mock_sync_cards.assert_called_once_with(self.employee)

    @mock.patch('trello.views.sync_trello_cards_for_employee')
    def test_atualizar_cards_view_employee_not_found(self, mock_sync_cards):
        """Testa o caso em que o employee não é encontrado."""
        url = reverse('atualizar-cards-trello', args=[999])  # ID inexistente
        response = self.client.post(url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"mensagem": "Erro durante a sincronização."})
        mock_sync_cards.assert_not_called()

    @mock.patch('trello.views.sync_trello_cards_for_employee')
    def test_atualizar_cards_view_sync_error(self, mock_sync_cards):
        """Testa o caso em que ocorre um erro durante a sincronização."""
        mock_sync_cards.side_effect = Exception("Erro simulado na sincronização")
        url = reverse('atualizar-cards-trello', args=[self.employee.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"mensagem": "Erro durante a sincronização."})
        mock_sync_cards.assert_called_once_with(self.employee)
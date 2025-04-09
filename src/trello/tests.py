from django.test import TestCase
from django.urls import reverse
from employees.models import Employee
from trello.models import BoardTrello
from accounts.models import UserModel
from django.contrib.auth.models import User

class BoardTrelloViewsTestCase(TestCase):
    def setUp(self):
        # Criação de usuário para autenticação
        self.user = User.objects.create_user(username="testuser", email="testuser@email.com", password="senha123")
        self.user_model = UserModel.objects.create(user=self.user, name="Empresa Teste", cnpj="95.027.986/0001-08", email=self.user.email)
        
        # Criação do funcionário com os campos obrigatórios (email e senha)
        self.employee = Employee.objects.create(
            user=self.user,
            accounts=self.user_model,
            name="Funcionário Teste",
            email="funcionario@email.com",
            password="senha456"
        )

        # Cria um board inicial
        self.board = BoardTrello.objects.create(
            nome_board='Board Inicial',
            trello_board_id='trello123',
            employee=self.employee
        )

    # def test_board_list_view(self):
    #     response = self.client.get(reverse('board-list'))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, 'Board Inicial')

    # def test_board_create_view(self):
    #     response = self.client.post(reverse('board-create'), {
    #         'nome_board': 'Novo Board',
    #         'trello_board_id': 'abc123xyz'
    #     })
    #     self.assertEqual(response.status_code, 302)
    #     self.assertTrue(BoardTrello.objects.filter(nome_board='Novo Board').exists())

    def test_board_update_view(self):
        response = self.client.post(reverse('board-update', args=[self.board.pk]), {
            'nome_board': 'Board Atualizado',
            'trello_board_id': 'novoID456'
        })
        self.assertEqual(response.status_code, 302)
        self.board.refresh_from_db()
        self.assertEqual(self.board.nome_board, 'Board Atualizado')
        self.assertEqual(self.board.trello_board_id, 'novoID456')

    def test_board_delete_view(self):
        response = self.client.post(reverse('board-delete', args=[self.board.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(BoardTrello.objects.filter(pk=self.board.pk).exists())

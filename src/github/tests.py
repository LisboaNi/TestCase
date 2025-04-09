from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from employees.models import Employee
from .models import RepositorioGitHub, AtividadeGitHub
from accounts.models import UserModel
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.test.client import RequestFactory
from unittest import mock


class GitHubCRUDTests(TestCase):

    def setUp(self):
        # Criar um usuário de teste
        self.test_user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword'
        )

        # Criar um UserModel associado ao usuário de teste
        try:
            self.company_account = UserModel.objects.get(user=self.test_user)
        except UserModel.DoesNotExist:
            self.company_account = UserModel.objects.create(user=self.test_user)

        # Criar um funcionário associado ao usuário e ao UserModel
        try:
            self.employee = Employee.objects.get(user=self.test_user)
        except Employee.DoesNotExist:
            self.employee = Employee.objects.create(
                user=self.test_user,
                accounts=self.company_account,  # Associe o UserModel aqui
                name='Test Employee',
                email='test@example.com',
                password='testpassword',
                function='Developer'
            )

        self.repositorio_data = {
            'nome_repositorio': 'meu-repositorio'
        }
        self.atividade_data = {
            'employee': self.employee.pk,
            'commit_mensagem': 'Adicionando nova funcionalidade',
            'data_commit': '2025-04-09T19:00:00-03:00'
        }
        self.factory = RequestFactory()

    def _authenticate_user(self):
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        auth_middleware = AuthenticationMiddleware(lambda x: x)
        auth_middleware.process_request(request)
        request.user = self.test_user
        return request

    def test_create_repositorio(self):
        """Testa a criação de um novo repositório."""
        request = self._authenticate_user()
        self.client.force_login(self.test_user)
        response = self.client.post(reverse('repositorio_create'), self.repositorio_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RepositorioGitHub.objects.count(), 1)
        repositorio = RepositorioGitHub.objects.first()
        self.assertEqual(repositorio.nome_repositorio, 'meu-repositorio')
        self.assertEqual(repositorio.employee, self.employee)

    def test_repositorio_list_view(self):
        """Testa a visualização da lista de repositórios do employee logado."""
        request = self._authenticate_user()
        self.client.force_login(self.test_user)
        RepositorioGitHub.objects.create(employee=self.employee, nome_repositorio='repo1')
        RepositorioGitHub.objects.create(employee=self.employee, nome_repositorio='repo2')
        response = self.client.get(reverse('repositorio_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'repo1')
        self.assertContains(response, 'repo2')
    
    def test_repositorio_update_view(self):
        """Testa a atualização de um repositório."""
        self.client.login(username='testuser@example.com', password='testpassword')

        # Criar um repositório para atualizar
        repositorio = RepositorioGitHub.objects.create(employee=self.employee, nome_repositorio='repositorio-antigo')
        old_nome = repositorio.nome_repositorio

        # Definir os dados para a atualização
        updated_data = {'nome_repositorio': 'repositorio-novo'}

        # Construir a URL para a view de atualização
        url = reverse('repositorio_update', args=[repositorio.pk])

        # Enviar uma requisição POST com os dados de atualização
        response = self.client.post(url, updated_data)

        # Verificar o status code (redirecionamento)
        self.assertEqual(response.status_code, 302)

        # Verificar se o repositório foi atualizado no banco de dados
        updated_repositorio = RepositorioGitHub.objects.get(pk=repositorio.pk)
        self.assertEqual(updated_repositorio.nome_repositorio, 'repositorio-novo')
        self.assertNotEqual(updated_repositorio.nome_repositorio, old_nome)

        # Verificar o redirecionamento para a lista de repositórios
        self.assertRedirects(response, reverse('repositorio_list'))

    def test_repositorio_delete_view(self):
        """Testa a exclusão de um repositório."""
        request = self._authenticate_user()
        self.client.force_login(self.test_user)
        repositorio = RepositorioGitHub.objects.create(employee=self.employee, nome_repositorio='repo_to_delete')
        response = self.client.post(reverse('repositorio_delete', args=[repositorio.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RepositorioGitHub.objects.count(), 0)
    
class AtualizarCommitsViewTests(TestCase):
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
            github_username='testgithubuser',
            github_token=self.encrypt_token('testgithubtoken'),
            name='Test Employee',
            email='test@example.com',
            password='testpassword',
            function='Developer'
        )
        self.repo1 = RepositorioGitHub.objects.create(employee=self.employee, nome_repositorio='repo1')
        self.repo2 = RepositorioGitHub.objects.create(employee=self.employee, nome_repositorio='repo2')
        self.factory = RequestFactory()

    def encrypt_token(self, token):
        return f"encrypted_{token}"

    def _authenticate_user(self):
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        auth_middleware = AuthenticationMiddleware(lambda x: x)
        auth_middleware.process_request(request)
        request.user = self.test_user
        return request

    @mock.patch('github.views.get_github_commits') # Substitua 'github.views' pelo caminho correto da sua função
    def test_atualizar_commits_view(self, mock_get_commits):
        # Configurar o comportamento mockado da get_github_commits
        mock_get_commits.side_effect = [
            [
                {"message": "Commit 1 from repo1", "date": "2025-04-09T10:00:00Z"},
                {"message": "Commit 2 from repo1", "date": "2025-04-09T11:00:00Z"},
            ],
            [
                {"message": "Commit 1 from repo2", "date": "2025-04-09T12:00:00Z"},
            ],
        ]

        request = self._authenticate_user()
        self.client.force_login(self.test_user) # Manter por segurança
        response = self.client.post(reverse('atualizar_todos_commits'), request=request) # Passando a requisição autenticada

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": "3 commits atualizados."})
        self.assertEqual(AtividadeGitHub.objects.count(), 3)

        # Verificar se as atividades foram criadas corretamente para o employee
        atividade1 = AtividadeGitHub.objects.get(employee=self.employee, commit_mensagem="Commit 1 from repo1")
        atividade2 = AtividadeGitHub.objects.get(employee=self.employee, commit_mensagem="Commit 2 from repo1")
        atividade3 = AtividadeGitHub.objects.get(employee=self.employee, commit_mensagem="Commit 1 from repo2")

        self.assertEqual(atividade1.data_commit.isoformat()[:-6] + 'Z', "2025-04-09T10:00:00Z") # Ajustar formato de data para comparação
        self.assertEqual(atividade2.data_commit.isoformat()[:-6] + 'Z', "2025-04-09T11:00:00Z")
        self.assertEqual(atividade3.data_commit.isoformat()[:-6] + 'Z', "2025-04-09T12:00:00Z")
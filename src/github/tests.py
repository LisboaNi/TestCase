from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from employees.models import Employee
from github.models import RepositorioGitHub
from accounts.models import UserModel

class RepositorioCRUDTestCase(TestCase):
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
        # Repositório existente para teste de Update/Delete/List
        self.repositorio = RepositorioGitHub.objects.create(
            employee=self.employee,
            nome_repositorio="Repositorio Teste",
        )

    # def test_create_repositorio_view(self):
    #     self.client.login(username="testuser", password="senha123")
    #     response = self.client.post(reverse("repositorio_create"), data={
    #         "nome_repositorio": "Novo Repositorio",
    #     })
    #     self.assertEqual(response.status_code, 302)  # Redireciona após criação

    def test_list_repositorios_view(self):
        self.client.login(username="testuser", password="senha123")
        response = self.client.get(reverse("repositorio_list"))
        self.assertEqual(response.status_code, 200)  # Página de listagem deve carregar

    def test_update_repositorio_view(self):
        self.client.login(username="testuser", password="senha123")
        response = self.client.post(reverse("repositorio_update", kwargs={"pk": self.repositorio.pk}), data={
            "nome_repositorio": "Repositorio Atualizado",
        })
        self.assertEqual(response.status_code, 302)  # Redireciona após atualização
        self.repositorio.refresh_from_db()

    def test_delete_repositorio_view(self):
        self.client.login(username="testuser", password="senha123")
        response = self.client.post(reverse("repositorio_delete", kwargs={"pk": self.repositorio.pk}))
        self.assertEqual(response.status_code, 302)  # Redireciona após exclusão
        self.assertFalse(RepositorioGitHub.objects.filter(pk=self.repositorio.pk).exists())
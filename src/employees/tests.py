from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from employees.models import Employee
from accounts.models import UserModel

class EmployeeCRUDTestCase(TestCase):
    def setUp(self):
        # Criação de usuário para autenticação
        self.user = User.objects.create_user(username="empresa_teste", email="empresa@email.com", password="senha123")
        self.user_model = UserModel.objects.create(user=self.user, name="Empresa Teste", cnpj="00.000.000/0001-00", email=self.user.email)

        # Criação de Employee
        self.employee = Employee.objects.create(
            user=self.user,
            accounts=self.user_model,
            name="Funcionário Teste",
            email="funcionario@email.com",
            password="senha456",
            function="Desenvolvedor"
        )

    def test_list_employees_view(self):
        self.client.login(username="empresa_teste", password="senha123")
        response = self.client.get(reverse("employee_list"))
        self.assertEqual(response.status_code, 200)  # Página de listagem deve carregar
        self.assertContains(response, self.employee.name)  # Nome do funcionário está listado

    def test_edit_employee_view(self):
        self.client.login(username="empresa_teste", password="senha123")
        response = self.client.post(reverse("employee_edit", kwargs={"pk": self.employee.pk}), data={
            "name": "Funcionário Atualizado",
            "email": "funcionario_atualizado@email.com",
            "password": "senha_atualizada",
            "function": "Gerente"
        })
        self.assertEqual(response.status_code, 302)  # Redireciona após edição
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.name, "Funcionário Atualizado")

    def test_delete_employee_view(self):
        self.client.login(username="empresa_teste", password="senha123")
        response = self.client.post(reverse("employee_delete", kwargs={"pk": self.employee.pk}))
        self.assertEqual(response.status_code, 302)  # Redireciona após exclusão
        self.assertFalse(Employee.objects.filter(pk=self.employee.pk).exists())
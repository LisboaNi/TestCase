from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import Employee
from accounts.models import UserModel
from .forms import EmployeeForm, EmployeeLoginForm, TokenForm  # Certifique-se que todos existem

class EmployeeCRUDTests(TestCase):

    def setUp(self):
        # Criar um UserModel para associar aos funcionários
        self.company_user = User.objects.create_user(
            username='company@example.com',
            email='company@example.com',
            password='companypassword'
        )
        self.company_account = UserModel.objects.create(
            user=self.company_user,
            name='Test Company',
            cnpj='00.000.000/0001-00',
            email='company@example.com'
        )

        self.employee_data = {
            'name': 'Test Employee',
            'email': 'employee@example.com',
            'password': 'employeepassword',
            'function': 'Developer'
        }
        self.client.login(username='company@example.com', password='companypassword')

    def test_create_employee(self):
        """Testa a criação de um novo funcionário."""
        self.assertEqual(Employee.objects.count(), 0)
        response = self.client.post(reverse('employee_create'), self.employee_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Employee.objects.count(), 1)
        employee = Employee.objects.last()
        self.assertEqual(employee.name, 'Test Employee')
        self.assertEqual(employee.email, 'employee@example.com')
        self.assertEqual(employee.function, 'Developer')
        self.assertIsNotNone(employee.user)
        self.assertEqual(employee.accounts, self.company_account)

    def test_employee_list_view(self):
        """Testa a visualização da lista de funcionários."""
        Employee.objects.create(
            accounts=self.company_account,
            name='Employee 1',
            email='employee1@example.com',
            user=User.objects.create_user(username='employee1@example.com', email='employee1@example.com', password='password1')
        )
        Employee.objects.create(
            accounts=self.company_account,
            name='Employee 2',
            email='employee2@example.com',
            user=User.objects.create_user(username='employee2@example.com', email='employee2@example.com', password='password2')
        )
        response = self.client.get(reverse('employee_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Employee 1')
        self.assertContains(response, 'Employee 2')

    def test_employee_profile_view(self):
        """Testa a visualização do perfil do funcionário logado."""
        employee = Employee.objects.create(
            accounts=self.company_account,
            name='Logged Employee',
            email='logged@example.com',
            user=User.objects.create_user(username='logged@example.com', email='logged@example.com', password='loggedpassword')
        )
        self.client.logout()
        self.client.login(username='logged@example.com', password='loggedpassword')
        response = self.client.get(reverse('employee_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Logged Employee')
        self.assertContains(response, 'logged@example.com')

    def test_employee_edit_view(self):
        """Testa a visualização e atualização do perfil do funcionário."""
        employee = Employee.objects.create(
            accounts=self.company_account,
            name='To Edit',
            email='edit@example.com',
            function='Tester',
            user=User.objects.create_user(username='edit@example.com', email='edit@example.com', password='editpassword')
        )
        updated_data = {
            'name': 'Edited Employee',
            'email': 'edited@example.com',
            'password': 'newpassword', # Inclua a senha se o formulário a tiver
            'function': 'Senior Developer'
        }
        response = self.client.post(reverse('employee_edit', kwargs={'pk': employee.pk}), updated_data)
        self.assertEqual(response.status_code, 302)
        employee.refresh_from_db()
        self.assertEqual(employee.name, 'Edited Employee')
        self.assertEqual(employee.email, 'edited@example.com')
        self.assertEqual(employee.function, 'Senior Developer')
        self.assertNotEqual(employee.password, 'newpassword') # Verifique se a senha foi criptografada
        employee.user.refresh_from_db()
        self.assertEqual(employee.user.email, 'edited@example.com')
        self.assertEqual(employee.user.username, 'edited@example.com')

    def test_employee_delete_view(self):
        """Testa a exclusão de um funcionário."""
        employee_to_delete = Employee.objects.create(
            accounts=self.company_account,
            name='To Delete',
            email='delete@example.com',
            user=User.objects.create_user(username='delete@example.com', email='delete@example.com', password='deletepassword')
        )
        self.assertEqual(Employee.objects.count(), 1)
        self.assertEqual(User.objects.count(), 2) # Inclui o company_user
        response = self.client.post(reverse('employee_delete', kwargs={'pk': employee_to_delete.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Employee.objects.count(), 0)
        self.assertEqual(User.objects.count(), 1) # Apenas o company_user deve sobrar

    def test_employee_login_view(self):
        """Testa o login de um funcionário."""
        Employee.objects.create(
            accounts=self.company_account,
            name='Login User',
            email='login@example.com',
            password='loginpassword',
            user=User.objects.create_user(username='login@example.com', email='login@example.com', password='loginpassword')
        )
        response = self.client.post(
            reverse('employee_login'),
            {'username': 'login@example.com', 'password': 'loginpassword'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get('_auth_user_id', False))

    def test_employee_login_invalid_credentials(self):
        """Testa o login com credenciais inválidas de funcionário."""
        self.client.logout()  # Desloga qualquer usuário logado antes do teste

        Employee.objects.create(
            accounts=self.company_account,
            name='Invalid Login',
            email='invalid@example.com',
            password='correctpassword',
            user=User.objects.create_user(username='invalid@example.com', email='invalid@example.com', password='correctpassword')
        )

        self.assertFalse(self.client.session.get('_auth_user_id', False))  # Verifique antes (agora deve ser False)

        response = self.client.post(
            reverse('employee_login'),
            {'username': 'invalid@example.com', 'password': 'wrongpassword'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Please enter a correct username and password', response.content.decode('utf-8'))
        self.assertFalse(self.client.session.get('_auth_user_id', False))  # Verifique depois (ainda deve ser False)
        
    def test_employee_logout_view(self):
        """Testa o logout de um funcionário."""
        Employee.objects.create(
            accounts=self.company_account,
            name='Logout User',
            email='logout@example.com',
            password='logoutpassword',
            user=User.objects.create_user(username='logout@example.com', email='logout@example.com', password='logoutpassword')
        )
        self.client.login(username='logout@example.com', password='logoutpassword')
        self.assertTrue(self.client.session.get('_auth_user_id', False))
        response = self.client.get(reverse('employee_logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.client.session.get('_auth_user_id', False))

    def test_token_update_view(self):
        """Testa a visualização e atualização dos tokens do funcionário."""
        employee = Employee.objects.create(
            accounts=self.company_account,
            name='Token User',
            email='token@example.com',
            user=User.objects.create_user(username='token@example.com', email='token@example.com', password='tokenpassword')
        )
        initial_token = 'initial_trello_token'
        initial_github_token = 'initial_github_token'
        employee.trello_token = initial_token
        employee.github_token = initial_github_token
        employee.save()

        updated_data = {
            'trello_username': 'new_trello_user',
            'trello_token': 'new_trello_token',
            'github_username': 'new_github_user',
            'github_token': 'new_github_token',
        }
        self.client.login(username='token@example.com', password='tokenpassword')
        response = self.client.post(reverse('token_edit'), updated_data)
        self.assertEqual(response.status_code, 302)
        employee.refresh_from_db()
        self.assertEqual(employee.trello_username, 'new_trello_user')
        self.assertNotEqual(employee.trello_token, 'new_trello_token') # Deve estar criptografado
        self.assertEqual(employee.github_username, 'new_github_user')
        self.assertNotEqual(employee.github_token, 'new_github_token') # Deve estar criptografado
        self.assertNotEqual(employee.trello_token, initial_token)
        self.assertNotEqual(employee.github_token, initial_github_token)
        self.client.logout()
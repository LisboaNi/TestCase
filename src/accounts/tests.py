from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserModel

class UserModelCRUDTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.user_model = UserModel.objects.create(
            user=self.user,
            name='Test User Profile',
            cnpj='11.222.333/0001-55',
            email='testuser@example.com'
        )
        self.user_model_data = {
            'name': 'New Test User',
            'cnpj': '12.345.678/0001-90',
            'email': 'newtestuser@example.com',
            'password': 'newpassword456'
        }

    def test_create_user(self):
        """Testa a criação de um novo usuário."""
        self.assertEqual(UserModel.objects.count(), 1)
        response = self.client.post(reverse('user_create'), self.user_model_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(UserModel.objects.count(), 2)
        new_user = UserModel.objects.last()
        self.assertEqual(new_user.name, 'New Test User')
        self.assertEqual(new_user.cnpj, '12.345.678/0001-90')
        self.assertEqual(new_user.email, 'newtestuser@example.com')
        self.assertNotEqual(new_user.password, 'newpassword456')

    def test_read_user_profile(self):
        """Testa a visualização do perfil do usuário."""
        self.client.login(username='testuser@example.com', password='testpassword123')
        response = self.client.get(reverse('user_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User Profile')
        self.assertContains(response, '11.222.333/0001-55')
        self.assertContains(response, 'testuser@example.com')
        self.client.logout()

    def test_update_user(self):
        """Testa a atualização do perfil do usuário."""
        self.client.login(username='testuser@example.com', password='testpassword123')
        updated_data = {
            'name': 'Updated Name',
            'cnpj': '11.222.333/0001-44',
            'email': 'updated@example.com',
            'password': 'updatedpassword789'
        }
        response = self.client.post(reverse('user_update', kwargs={'pk': self.user_model.pk}), updated_data)
        self.assertEqual(response.status_code, 302)
        self.user_model.refresh_from_db()
        self.assertEqual(self.user_model.name, 'Updated Name')
        self.assertEqual(self.user_model.cnpj, '11.222.333/0001-44')
        self.assertEqual(self.user_model.email, 'updated@example.com')
        self.assertNotEqual(self.user_model.password, 'updatedpassword789')
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')
        self.client.logout()

    def test_delete_user(self):
        """Testa a exclusão do usuário."""
        self.client.login(username='testuser@example.com', password='testpassword123')
        user_model_to_delete = UserModel.objects.create(
            user=User.objects.create_user(
                username='deleteuser@example.com',
                email='deleteuser@example.com',
                password='deletepassword'
            ),
            name='To Delete',
            cnpj='66.777.888/0001-55',
            email='delete@example.com'
        )
        self.assertEqual(UserModel.objects.count(), 2)
        self.assertEqual(User.objects.count(), 2)
        response = self.client.post(reverse('user_delete', kwargs={'pk': user_model_to_delete.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(UserModel.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_user(self):
        """Testa o processo de login do usuário."""
        response = self.client.post(
            reverse('login'),
            {'email': 'testuser@example.com', 'password': 'testpassword123'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get('_auth_user_id', False))

    def test_login_invalid_credentials(self):
        """Testa o login com credenciais inválidas."""
        response = self.client.post(
            reverse('login'),
            {'email': 'testuser@example.com', 'password': 'wrongpassword'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], None, 'Email ou senha inválidos.')
        self.assertFalse(self.client.session.get('_auth_user_id', False))
    
    def test_logout_user(self):
        """Testa o processo de logout do usuário."""
        self.client.login(username='testuser@example.com', password='testpassword123')
        self.assertTrue(self.client.session.get('_auth_user_id', False))
        response = self.client.post(reverse('user_logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.client.session.get('_auth_user_id', False))
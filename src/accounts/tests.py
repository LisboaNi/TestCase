from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserModel

class UserViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="testuser@email.com", password="senha123")
        self.user_model = UserModel.objects.create(
            user=self.user,
            name="Teste",
            cnpj="00.000.000/0001-00",
            email="testuser@email.com",
            password="senha123"
        )
        # Garantir a vinculação explícita
        self.user.usermodel = self.user_model
        self.user.save()
    
    def test_login_view(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
    
    def test_login_functionality(self):
        response = self.client.post(reverse("login"), data={
            "email": "testuser@email.com",
            "password": "senha123"
        })
        self.assertRedirects(response, reverse("user_profile"))
    
    def test_logout_view(self):
        self.client.login(username="testuser", password="senha123")
        response = self.client.post(reverse("user_logout"))
        self.assertRedirects(response, reverse("login"))
    
    # def test_user_profile_view(self):
    #     self.client.login(username="testuser", password="senha123")
    #     response = self.client.get(reverse("user_profile"))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, self.user_model.name)
    
    def test_create_user_view(self):
        response = self.client.post(reverse("user_create"), data={
            "name": "Novo Usuário",
            "cnpj": "11.111.111/1111-11",
            "email": "novo@email.com",
            "password": "senha456"
        })
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(UserModel.objects.filter(email="novo@email.com").exists())
        novo = UserModel.objects.get(email="novo@email.com")
        self.assertEqual(novo.name, "Novo Usuário")
    
    # def test_delete_user_view(self):
    #     self.client.login(username="testuser", password="senha123")
    #     response = self.client.post(reverse("user_delete", kwargs={"pk": self.user_model.pk}))
    #     self.assertRedirects(response, reverse("login"))
    #     self.assertFalse(UserModel.objects.filter(pk=self.user_model.pk).exists())
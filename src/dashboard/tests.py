import json
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone
from employees.models import Employee
from github.models import AtividadeGitHub
from trello.models import CardTrello
from accounts.models import UserModel  
from django.contrib.auth.models import User

class DashboardGeralViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.django_user1 = User.objects.create_user(username='test1@example.com', password='password')
        self.user1 = UserModel.objects.create(user=self.django_user1, email='test1@example.com', cnpj='TEST_CNPJ_1')
        self.employee1 = Employee.objects.create(user=self.django_user1, accounts=self.user1, name='Employee 1')

        self.django_user2 = User.objects.create_user(username='test2@example.com', password='password')
        self.user2 = UserModel.objects.create(user=self.django_user2, email='test2@example.com', cnpj='TEST_CNPJ_2')
        self.employee2 = Employee.objects.create(user=self.django_user2, accounts=self.user2, name='Employee 2')

        agora_utc = timezone.now()
        fuso_horario_local = timezone.get_current_timezone()
        agora_local = timezone.localtime(agora_utc, fuso_horario_local)

        AtividadeGitHub.objects.create(employee=self.employee1, data_commit=agora_local - timezone.timedelta(days=1))
        CardTrello.objects.create(employee=self.employee1, data_criacao=agora_local - timezone.timedelta(days=2), trello_card_id='TRELLO_CARD_1')
        AtividadeGitHub.objects.create(employee=self.employee2, data_commit=agora_local - timezone.timedelta(days=8))
        CardTrello.objects.create(employee=self.employee2, data_criacao=agora_local - timezone.timedelta(days=3), trello_card_id='TRELLO_CARD_2')


    def test_get_dashboard_geral_view(self):
        request = self.factory.get(reverse('dashboard_geral')) # Use 'dashboard_geral'
        response = self.client.get(reverse('dashboard_geral')) # Use 'dashboard_geral'
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/geral.html')
        self.assertIn('employees', response.context)
        self.assertIn('grafico_labels', response.context)
        self.assertIn('grafico_data', response.context)
        self.assertIn('grafico_cards', response.context)
        self.assertEqual(len(json.loads(response.context['grafico_labels'])), 2)
        self.assertEqual(len(json.loads(response.context['grafico_data'])), 2)
        self.assertEqual(len(json.loads(response.context['grafico_cards'])), 2)

    def test_get_dashboard_geral_view_filter_tipo_trello(self):
        response = self.client.get(reverse('dashboard_geral'), {'tipo': 'trello', 'data': 10}) # Aumentando o período para 10 dias
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.context['grafico_data'])[0], 0)
        self.assertEqual(json.loads(response.context['grafico_cards'])[0], 1)
        self.assertEqual(json.loads(response.context['grafico_data'])[1], 0)
        self.assertEqual(json.loads(response.context['grafico_cards'])[1], 1)
        
    def test_get_dashboard_geral_view_filter_tipo_github(self):
        request = self.factory.get(reverse('dashboard_geral'), {'tipo': 'github'}) # Use 'dashboard_geral'
        response = self.client.get(reverse('dashboard_geral'), {'tipo': 'github'}) # Use 'dashboard_geral'
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.context['grafico_data'])[0], 1)
        self.assertEqual(json.loads(response.context['grafico_cards'])[0], 0)
        self.assertEqual(json.loads(response.context['grafico_data'])[1], 0)
        self.assertEqual(json.loads(response.context['grafico_cards'])[1], 0)

    def test_get_dashboard_geral_view_filter_tipo_trello(self):
        request = self.factory.get(reverse('dashboard_geral'), {'tipo': 'trello'}) # Use 'dashboard_geral'
        response = self.client.get(reverse('dashboard_geral'), {'tipo': 'trello'}) # Use 'dashboard_geral'
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.context['grafico_data'])[0], 0)
        self.assertEqual(json.loads(response.context['grafico_cards'])[0], 1)
        self.assertEqual(json.loads(response.context['grafico_data'])[1], 0)
        self.assertEqual(json.loads(response.context['grafico_cards'])[1], 1)

class DashboardFuncionarioViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.django_user = User.objects.create_user(username='test@example.com', password='password')
        self.user = UserModel.objects.create(user=self.django_user, email='test@example.com', cnpj='TEST_CNPJ')
        self.employee = Employee.objects.create(user=self.django_user, accounts=self.user, name='Test Employee')
        agora = timezone.now()
        AtividadeGitHub.objects.create(employee=self.employee, data_commit=agora - timezone.timedelta(days=1))
        CardTrello.objects.create(employee=self.employee, data_criacao=agora - timezone.timedelta(days=2), trello_card_id='TRELLO_CARD_EMP')
        
    def test_get_dashboard_funcionario_view(self):
        url = reverse('dashboard_funcionario', args=[self.employee.pk]) # Use 'dashboard_funcionario'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/funcionario.html')
        self.assertIn('employee', response.context)
        self.assertIn('grafico_alert_labels', response.context)
        self.assertIn('grafico_alert_data', response.context)
        self.assertEqual(response.context['employee'].name, 'Test Employee')
        self.assertEqual(len(json.loads(response.context['grafico_alert_labels'])), 3)
        self.assertEqual(len(json.loads(response.context['grafico_alert_data'])), 3)

    def test_get_dashboard_funcionario_view(self):
        url = reverse('dashboard_funcionario', args=[self.employee.pk]) # Use 'dashboard_funcionario'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/funcionario.html')
        self.assertIn('employee', response.context)
        self.assertIn('grafico_alert_labels', response.context)
        self.assertIn('grafico_alert_data', response.context)
        self.assertEqual(response.context['employee'].name, 'Test Employee')
        self.assertEqual(len(json.loads(response.context['grafico_alert_labels'])), 3)
        self.assertEqual(len(json.loads(response.context['grafico_alert_data'])), 3)

    def test_get_dashboard_funcionario_view_not_found(self):
        url = reverse('dashboard_funcionario', args=[999]) # Use 'dashboard_funcionario'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_dashboard_funcionario_view_filter_data(self):
        url = reverse('dashboard_funcionario', args=[self.employee.pk]) # Use 'dashboard_funcionario'
        response = self.client.get(url, {'data': 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['employee'].total_commits, 1)
        self.assertEqual(response.context['employee'].total_cards, 1)

    def test_get_dashboard_funcionario_view_filter_tipo_github(self):
        url = reverse('dashboard_funcionario', args=[self.employee.pk]) # Use 'dashboard_funcionario'
        response = self.client.get(url, {'tipo': 'github'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['employee'].total_commits, 1)
        self.assertEqual(response.context['employee'].total_cards, 0)

    def test_get_dashboard_funcionario_view_filter_tipo_trello(self):
        url = reverse('dashboard_funcionario', args=[self.employee.pk]) # Use 'dashboard_funcionario'
        response = self.client.get(url, {'tipo': 'trello'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['employee'].total_commits, 0)
        self.assertEqual(response.context['employee'].total_cards, 1)
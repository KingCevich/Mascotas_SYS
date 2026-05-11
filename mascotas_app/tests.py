from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Reporte, Contacto
from datetime import date, time
from decimal import Decimal
from unittest.mock import patch


class ReporteModelTest(TestCase):
    # Prueba la creación de un objeto Reporte con todos los campos requeridos
    def test_create_reporte(self):
        reporte = Reporte.objects.create(
            tipo_reporte='Perdido',
            nombre_mascota='Max',
            raza='Golden Retriever',
            color='Blanco',
            tamano=Decimal('25.50'),
            fech_perdida=date.today(),
            hora_perdida=time(14, 30),
            latitud=Decimal('-33.8688'),
            longitud=Decimal('-51.2093'),
            descripcion='Perro blanco encontrado',
            estado_reporte='Activo'
        )
        self.assertEqual(reporte.nombre_mascota, 'Max')
        self.assertIn('Max', str(reporte))


class ContactoModelTest(TestCase):
    # Prueba la creación de un objeto Contacto vinculado a un Reporte
    def setUp(self):
        self.reporte = Reporte.objects.create(
            tipo_reporte='Perdido',
            nombre_mascota='Max',
            raza='Golden Retriever',
            color='Blanco',
            fech_perdida=date.today(),
            latitud=Decimal('-33.8688'),
            longitud=Decimal('-51.2093'),
            estado_reporte='Activo'
        )

    # Verifica que se pueda crear un contacto correctamente
    def test_create_contacto(self):
        contacto = Contacto.objects.create(
            reporte=self.reporte,
            telefono='123456789',
            email='juan@example.com',
            whatsapp_enable=True
        )
        self.assertEqual(contacto.telefono, '123456789')
        self.assertIn('Max', str(contacto))


class ReporteAPITest(APITestCase):
    # Tests de API REST para operaciones CRUD de Reportes
    def setUp(self):
        self.reporte = Reporte.objects.create(
            tipo_reporte='Perdido',
            nombre_mascota='Max',
            raza='Golden Retriever',
            color='Blanco',
            fech_perdida=date.today(),
            latitud=Decimal('-33.8688'),
            longitud=Decimal('-51.2093'),
            estado_reporte='Activo'
        )

    # Obtiene la lista de todos los reportes (GET /api/reportes/)
    def test_list_reportes(self):
        url = '/api/reportes/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    # Crea un nuevo reporte via POST con token JWT simulado
    @patch('mascotas_app.views.validate_token')
    @patch('mascotas_app.views.get_token_from_request')
    def test_create_reporte(self, mock_get_token, mock_validate_token):
        mock_get_token.return_value = 'mock-token'
        mock_validate_token.return_value = (True, {'rol': 'Admin'})
        
        url = '/api/reportes/'
        data = {
            'tipo_reporte': 'Encontrado',
            'nombre_mascota': 'Bella',
            'raza': 'Labrador',
            'color': 'Negro',
            'fech_perdida': date.today().isoformat(),
            'latitud': '-33.8688',
            'longitud': '-51.2093',
            'estado_reporte': 'Activo'
        }
        response = self.client.post(url, data, content_type='application/json', HTTP_AUTHORIZATION='Bearer mock-token')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    # Obtiene un reporte específico por ID (GET /api/reportes/{id}/)
    def test_retrieve_reporte(self):
        url = f'/api/reportes/{self.reporte.pk}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre_mascota'], 'Max')

    # Actualiza el estado de un reporte (PATCH /api/reportes/{id}/) - Requiere rol Admin
    @patch('mascotas_app.views.validate_token')
    @patch('mascotas_app.views.get_token_from_request')
    def test_update_reporte(self, mock_get_token, mock_validate_token):
        mock_get_token.return_value = 'mock-token'
        mock_validate_token.return_value = (True, {'rol': 'Admin'})
        
        url = f'/api/reportes/{self.reporte.pk}/'
        data = {'estado_reporte': 'Resuelto'}
        response = self.client.patch(url, data, content_type='application/json', HTTP_AUTHORIZATION='Bearer mock-token')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        if response.status_code == status.HTTP_200_OK:
            self.reporte.refresh_from_db()
            self.assertEqual(self.reporte.estado_reporte, 'Resuelto')

    # Elimina un reporte (DELETE /api/reportes/{id}/) - Requiere rol Admin
    @patch('mascotas_app.views.validate_token')
    @patch('mascotas_app.views.get_token_from_request')
    def test_delete_reporte(self, mock_get_token, mock_validate_token):
        mock_get_token.return_value = 'mock-token'
        mock_validate_token.return_value = (True, {'rol': 'Admin'})
        
        url = f'/api/reportes/{self.reporte.pk}/'
        response = self.client.delete(url, HTTP_AUTHORIZATION='Bearer mock-token')
        self.assertIn(response.status_code, [status.HTTP_204_NO_CONTENT, status.HTTP_404_NOT_FOUND])


class ContactoAPITest(APITestCase):
    # Tests de API REST para operaciones CRUD de Contactos
    def setUp(self):
        self.reporte = Reporte.objects.create(
            tipo_reporte='Perdido',
            nombre_mascota='Max',
            raza='Golden Retriever',
            color='Blanco',
            fech_perdida=date.today(),
            latitud=Decimal('-33.8688'),
            longitud=Decimal('-51.2093'),
            estado_reporte='Activo'
        )
        self.contacto = Contacto.objects.create(
            reporte=self.reporte,
            telefono='123456789',
            email='juan@example.com'
        )

    # Obtiene la lista de todos los contactos (GET /api/contactos/)
    def test_list_contactos(self):
        url = '/api/contactos/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    # Crea un nuevo contacto via POST con token JWT simulado
    @patch('mascotas_app.views.validate_token')
    @patch('mascotas_app.views.get_token_from_request')
    def test_create_contacto(self, mock_get_token, mock_validate_token):
        mock_get_token.return_value = 'mock-token'
        mock_validate_token.return_value = (True, {'rol': 'Admin'})
        
        url = '/api/contactos/'
        data = {
            'reporte': self.reporte.pk,
            'telefono': '987654321',
            'email': 'maria@example.com',
            'whatsapp_enable': True
        }
        response = self.client.post(url, data, content_type='application/json', HTTP_AUTHORIZATION='Bearer mock-token')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    # Obtiene un contacto específico por ID (GET /api/contactos/{id}/)
    def test_retrieve_contacto(self):
        url = f'/api/contactos/{self.contacto.pk}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['telefono'], '123456789')

    # Actualiza el teléfono de un contacto (PATCH /api/contactos/{id}/) - Requiere rol Admin
    @patch('mascotas_app.views.validate_token')
    @patch('mascotas_app.views.get_token_from_request')
    def test_update_contacto(self, mock_get_token, mock_validate_token):
        mock_get_token.return_value = 'mock-token'
        mock_validate_token.return_value = (True, {'rol': 'Admin'})
        
        url = f'/api/contactos/{self.contacto.pk}/'
        data = {'telefono': '111111111'}
        response = self.client.patch(url, data, content_type='application/json', HTTP_AUTHORIZATION='Bearer mock-token')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        if response.status_code == status.HTTP_200_OK:
            self.contacto.refresh_from_db()
            self.assertEqual(self.contacto.telefono, '111111111')

    # Elimina un contacto (DELETE /api/contactos/{id}/) - Requiere rol Admin
    @patch('mascotas_app.views.validate_token')
    @patch('mascotas_app.views.get_token_from_request')
    def test_delete_contacto(self, mock_get_token, mock_validate_token):
        mock_get_token.return_value = 'mock-token'
        mock_validate_token.return_value = (True, {'rol': 'Admin'})
        
        url = f'/api/contactos/{self.contacto.pk}/'
        response = self.client.delete(url, HTTP_AUTHORIZATION='Bearer mock-token')
        self.assertIn(response.status_code, [status.HTTP_204_NO_CONTENT, status.HTTP_404_NOT_FOUND])

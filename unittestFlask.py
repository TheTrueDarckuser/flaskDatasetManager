import io
import unittest
import json
from app import app

class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_user_registration(self):
        # Тест регистрации пользователя
        data = {
            'username': 'test_user',
            'password': 'test_password'
        }
        response = self.app.post('/register', json=data)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['message'], 'User registered successfully')

    def test_user_login(self):
        # Тест входа пользователя
        data = {
            'username': 'test_user',
            'password': 'test_password'
        }
        response = self.app.post('/login', json=data)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('access_token' in data)
        self.assertEqual(data['message'], 'Logged in as test_user')

    def test_protected_resource(self):
        # Тест доступа к защищенному ресурсу
        data = {
            'username': 'test_user',
            'password': 'test_password'
        }
        # Регистрируем пользователя
        self.app.post('/register', json=data)
        # Входим в систему и получаем токен доступа
        login_response = self.app.post('/login', json=data)
        login_data = json.loads(login_response.data)
        access_token = login_data['access_token']

        # Запрашиваем защищенный ресурс с токеном доступа
        response = self.app.get('/protected', headers={'Authorization': f'Bearer {access_token}'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'This is a protected resource')
        self.assertEqual(data['user'], 'test_user')

    def test_upload_file(self):
        # Тест загрузки файла
        data = {
            'username': 'test_user',
            'password': 'test_password'
        }
        # Регистрируем пользователя
        self.app.post('/register', json=data)
        # Входим в систему и получаем токен доступа
        login_response = self.app.post('/login', json=data)
        login_data = json.loads(login_response.data)
        access_token = login_data['access_token']

        # Загружаем файл
        data['file'] = (io.BytesIO(b"abcdef"), 'test.csv')
        response = self.app.post('/upload', data=data,
                                 headers={'Authorization': f'Bearer {access_token}'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['message'], 'File uploaded successfully')

    def test_get_files_info(self):
        # Тест получения информации о файлах
        data = {
            'username': 'test_user',
            'password': 'test_password'
        }
        # Регистрируем пользователя
        self.app.post('/register', json=data)
        # Входим в систему и получаем токен доступа
        login_response = self.app.post('/login', json=data)
        login_data = json.loads(login_response.data)
        access_token = login_data['access_token']

        # Загружаем файл
        data['file'] = (io.BytesIO(b"abcdef"), 'test.csv')
        self.app.post('/upload', data=data,
                      headers={'Authorization': f'Bearer {access_token}'})

        # Получаем информацию о файлах
        response = self.app.get('/info', headers={'Authorization': f'Bearer {access_token}'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue('Report' in data)

    def test_get_file_data(self):
        # Тест получения данных из файла
        data = {
            'username': 'test_user',
            'password': 'test_password'
        }
        # Регистрируем пользователя
        self.app.post('/register', json=data)
        # Входим в систему и получаем токен доступа
        login_response = self.app.post('/login', json=data)
        login_data = json.loads(login_response.data)
        access_token = login_data['access_token']

        # Загружаем файл
        self.app.post('/upload', data=data,
                      headers={'Authorization': f'Bearer {access_token}'})

        # Получаем данные из файла
        response = self.app.get('/get-file-data/test.csv', headers={'Authorization': f'Bearer {access_token}'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('data' in data)

if __name__ == '__main__':
    unittest.main()
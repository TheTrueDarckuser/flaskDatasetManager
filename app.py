from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import pandas as pd
import json

# Создание каталога с датасетами
if not os.path.exists("files"):
    os.makedirs("files")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'  # Замените на свой секретный ключ
app.config['UPLOAD_FOLDER'] = 'files'  # Папка для загрузки CSV-файлов
mongo = MongoClient('localhost', 27017)
api = Api(app)
jwt = JWTManager(app)

# Коллекция для пользователей в MongoDB
users_collection = mongo['users-data']['users-data']

# Создадим парсер для обработки данных JSON в запросах
parser = reqparse.RequestParser()
parser.add_argument('username', help='This field cannot be blank', required=True)
parser.add_argument('password', help='This field cannot be blank', required=True)

# Функция для проверки разрешенных расширений файлов
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv'}

# Ресурс для регистрации нового пользователя
class UserRegistration(Resource):
    def post(self):
        data = parser.parse_args()

        # Проверяем, есть ли пользователь с таким именем
        if users_collection.find_one({'username': data['username']}):
            return {'message': 'User with this username already exists'}, 400
        print({'username': data['username'], 'password': data['password']})
        # Создаем нового пользователя
        user_id = users_collection.insert_one({'username': data['username'], 'password': data['password']})
        return {'message': 'User registered successfully', 'user_id': str(user_id)}, 201

# Ресурс для входа пользователя
class UserLogin(Resource):
    def post(self):
        data = parser.parse_args()
        current_user = users_collection.find_one({'username': data['username']})

        if not current_user:
            return {'message': 'User {} doesn\'t exist'.format(data['username'])}, 400

        if data['password'] == current_user['password']:
            access_token = create_access_token(identity=data['username'])
            return {'message': 'Logged in as {}'.format(current_user['username']), 'access_token': access_token}, 200
        else:
            return {'message': 'Wrong credentials'}, 401

# Защищенный ресурс, который требует токен авторизации
class ProtectedResource(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        return {'message': 'This is a protected resource', 'user': current_user}, 200

class FileUpload(Resource):
    @jwt_required()
    def post(self):
        if 'file' not in request.files:
            return jsonify({'message': 'No file part'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return {'message': 'File uploaded successfully'}, 201
        else:
            return {'message': 'Invalid file format. Allowed formats: CSV'}, 400

class GetFilesInfo(Resource):
    @jwt_required()
    def get(self):
        info = []
        listdir = os.listdir(app.config['UPLOAD_FOLDER'])
        for i in listdir:
            df = pd.read_csv(f"{app.config['UPLOAD_FOLDER']}/{i}", encoding="windows-1251").dtypes
            df = str(df).split('\n')
            # print(str(df))
            info += [{"filename": i, "fileinfo": df}]
        # print(jsonify({info}))
        return {"Report": info}, 201

class GetFileData(Resource):
    @jwt_required()
    def get(self, filename):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(file_path):
            return jsonify({'message': 'File not found'}), 404

        # Читаем CSV-файл с помощью pandas
        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            return jsonify({'message': 'File is empty'}), 400

        # Применяем фильтрацию, если заданы параметры фильтрации
        filters = request.args.getlist('filter')
        if filters:
            for filter_expr in filters:
                try:
                    df = df.query(filter_expr)
                except pd.errors.ParserError:
                    return jsonify({'message': 'Invalid filter expression'}), 400

        # Применяем сортировку, если заданы параметры сортировки
        sort_columns = request.args.getlist('sort')
        if sort_columns:
            try:
                df = df.sort_values(by=sort_columns)
            except KeyError:
                return jsonify({'message': 'Invalid column name for sorting'}), 400

        # Преобразуем данные в формат JSON и возвращаем их
        data_json = df.to_json(orient='records', date_format='iso')
        return jsonify({'data': json.loads(data_json)})

api.add_resource(UserRegistration, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(ProtectedResource, '/protected')
api.add_resource(FileUpload, '/upload')
api.add_resource(GetFilesInfo, '/info')
api.add_resource(GetFileData, '/get-file-data/<filename>')


if __name__ == '__main__':
    app.run(debug=True)
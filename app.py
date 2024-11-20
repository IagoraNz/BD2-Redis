# ---------------------------------------------------------------------------------------------------------- #

# Importando as bibliotecas necessárias

from flask import Flask, redirect, url_for, request, render_template_string
import redis
import os

# ---------------------------------------------------------------------------------------------------------- #

app = Flask(__name__)

'''
    Esse trecho de código é responsável por criar uma conexão com o Redis
'''
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
server = redis.Redis.from_url(redis_url)

# ---------------------------------------------------------------------------------------------------------- #

'''
    summary
        Essa função é responsável por renderizar a página inicial da aplicação, incluindo
        o menu de opções para criar, inserir, consultar e deletar dados.
    param
        Nenhum
    return
        render_template_string: Retorna o HTML renderizado com o menu de opções
'''
@app.route('/')
def index():
    return render_template_string('''
    <!doctype html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Aplicação com Redis</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
        <div class="container">
            <!-- Substituindo o título pelo logo do Redis -->
            <img src="{{ url_for('static', filename='Redis-Logo.wine.png') }}" alt="Redis Logo" width="200">
            <ul>
                <li><a href="{{ url_for('create_db') }}" class="button">Criar banco de dados</a></li>
                <li><a href="{{ url_for('insert_doc') }}" class="button">Inserir dados</a></li>
                <li><a href="{{ url_for('query_data') }}" class="button">Consultar dados</a></li>
                <li><a href="{{ url_for('delete_data') }}" class="button">Deletar dados</a></li>
                <li><a href="{{ url_for('drop_db') }}" class="button">Deletar banco de dados</a></li>
            </ul>
        </div>
    </body>
    </html>
    ''')
    
# ---------------------------------------------------------------------------------------------------------- #

'''
    summary
        Essa função é responsável por criar um banco de dados no Redis
    param
        Nenhum
    return
        render_template_string: Retorna o HTML renderizado com o formulário para criar um banco de dados        
'''
@app.route('/create_db', methods=['GET', 'POST'])
def create_db():
    if request.method == 'POST':
        db_name = request.form.get('db_name')
        if server.exists(f"{db_name}:exists"):
            success_message = "Banco de dados já existe"
        else:
            server.set(f"{db_name}:exists", 1)  # Marca o banco como existente
            success_message = f'Banco de dados {db_name} preparado para uso'
        return render_success_message(success_message)
    return render_template_string('''
    <!doctype html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Criar banco de dados</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
        <div class="container">
            <h1>Criar banco de dados</h1>
            <form method="post">
                <input type="text" name="db_name" placeholder="Digite o nome do banco de dados">
                <input type="submit" value="Criar">
            </form>
        </div>
    </body>
    </html>
    ''')
    
# ---------------------------------------------------------------------------------------------------------- #

'''
    summary
        Essa função é responsável por inserir um documento no banco de dados, para isso
        é necessário informar o nome do banco de dados, o ID do documento, o nome do filme/serie,
        a duração e o tipo.
    param
        Nenhum
    return
        render_template_string: Retorna o HTML renderizado com o formulário para inserir um documento
'''
@app.route('/insert_doc', methods=['GET', 'POST'])
def insert_doc():
    if request.method == 'POST':
        db_name = request.form.get('db_name')
        key_id = request.form.get('key_id')
        
        # Verificar se o banco de dados existe
        if not any(server.keys(f"{db_name}:*")):
            return render_success_message("Banco de dados não encontrado")
        
        # Verificar se o documento já existe
        if server.hexists(f"{db_name}:docs", key_id):
            return render_success_message("Documento já existe")
        
        # Coletando os dados do formulário
        filmeserie = request.form.get('filmeserie')
        duracao = request.form.get('duracao')
        tipo = request.form.get('tipo')
        # mensagem = request.form.get('mensagem')

        # Armazenando os dados no Redis como uma hash
        try:
            # A chave será "db_name:docs" e o campo da hash será o "key_id"
            server.hset(f"{db_name}:docs", key_id, f"Nome do filme/serie: {filmeserie}, Duracao: {duracao}, Tipo: {tipo}")
            return render_success_message(f'Documento inserido com sucesso no banco de dados {db_name}')
        except redis.RedisError as e:
            return render_success_message(f'Erro ao inserir documento no banco de dados {db_name}: {e}')
    
    return render_template_string('''
    <!doctype html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Inserir documento</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
        <div class="container">
            <h1>Inserir documento</h1>
            <form method="post">
                <input type="text" name="db_name" placeholder="Digite o nome do banco de dados">
                <input type="text" name="key_id" placeholder="Digite o ID do documento">
                <input type="text" name="filmeserie" placeholder="Digite o nome do filme ou série">
                <input type="text" name="duracao" placeholder="Digite a duracao em XX:XX">
                <input type="text" name="tipo" placeholder="Digite o tipo do filme">
                <input type="submit" value="Inserir midia">
            </form>
        </div>
    </body>
    </html>
    ''')
    
# ---------------------------------------------------------------------------------------------------------- #

'''
    summary
        Essa função é responsável por consultar um documento no banco de dados, para isso
        é necessário informar o nome do banco de dados e o ID do documento.
    param
        Nenhum
    return
        render_template_string: Retorna o HTML renderizado com o formulário para consultar um documento
'''
@app.route('/query_data', methods=['GET', 'POST'])
def query_data():
    if request.method == 'POST':
        db_name = request.form.get('db_name')
        key_id = request.form.get('key_id')
        key = f"{db_name}:docs"  # Chave da hash onde os documentos são armazenados

        # Verificar se o documento existe no hash
        if not server.hexists(key, key_id):
            return render_success_message("Documento não encontrado")
        
        # Recuperar os dados usando hget e decodificar
        data = server.hget(key, key_id).decode('utf-8')
        
        # Dividir os dados para exibir na tabela
        # Usa um dicionário para exibir os campos e valores corretamente
        data_dict = {}
        for item in data.split(","):
            key_value = item.split(":", 1)  # Divide apenas no primeiro ":" para evitar problemas
            if len(key_value) == 2:
                data_dict[key_value[0].strip()] = key_value[1].strip()

        # Renderizar os dados em uma tabela HTML
        table_html = '''
        <!doctype html>
        <html lang="pt">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dados do Documento</title>
            <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
        </head>
        <body>
            <div class="container">
                <h1>Dados</h1>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Dado</th>
                            <th>Conteúdo</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for field, value in data_dict.items() %}
                        <tr>
                            <td>{{ field }}</td>
                            <td>{{ value }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                <a class="back-button" href="{{ url_for('index') }}">Voltar ao início</a>
            </div>
        </body>
        </html>
        '''
        
        # Renderizar a tabela usando o render_template_string com o dicionário de dados
        return render_template_string(table_html, data_dict=data_dict)
    
    return render_template_string('''
    <!doctype html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Consultar dados</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
        <div class="container">
            <h1>Consultar dados</h1>
            <form method="post">
                <input type="text" name="db_name" placeholder="Digite o nome do banco de dados">
                <input type="text" name="key_id" placeholder="Digite o ID do documento">
                <input type="submit" value="Consultar">
            </form>
        </div>
    </body>
    </html>
    ''')
    
# ---------------------------------------------------------------------------------------------------------- #

'''
    summary
        Essa função é responsável por deletar um documento no banco de dados, para isso
        é necessário informar o nome do banco de dados e o ID do documento.
    param
        Nenhum
    return
        render_template_string: Retorna o HTML renderizado com o formulário para deletar um documento
'''
@app.route('/delete_data', methods=['GET', 'POST'])
def delete_data():
    if request.method == 'POST':
        db_name = request.form.get('db_name')
        key_id = request.form.get('key_id')
        key = f"{db_name}:docs"  # A chave correta é o nome da hash

        # Verificar se o hash do banco de dados existe
        if not server.hexists(key, key_id):
            return render_success_message("Documento não encontrado")
        
        # Deletar o campo específico dentro do hash
        server.hdel(key, key_id)
        return render_success_message("Documento deletado com sucesso")
    return render_template_string('''
    <!doctype html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Deletar dados</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
        <div class="container">
            <h1>Deletar dados</h1>
            <form method="post">
                <input type="text" name="db_name" placeholder="Digite o nome do banco de dados">
                <input type="text" name="key_id" placeholder="Digite o ID do documento">
                <input type="submit" value="Deletar">
            </form>
        </div>
    </body>
    </html>
    ''')
    
# ---------------------------------------------------------------------------------------------------------- #

'''
    summary
        Essa função é responsável por deletar um banco de dados no Redis
    param
        Nenhum
    return
        render_template_string: Retorna o HTML renderizado com o formulário para deletar um banco de dados
'''
@app.route('/drop_db', methods=['GET', 'POST'])
def drop_db():
    if request.method == 'POST':
        db_name = request.form.get('db_name')
        
        keys = server.keys(f"{db_name}:*")
        if not keys:
            return render_success_message("Banco de dados não encontrado")
        
        for key in keys:
            server.delete(key)
        return render_success_message(f"Banco de dados {db_name} deletado com sucesso")
    
    return render_template_string('''
    <!doctype html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Deletar banco de dados</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
        <div class="container">
            <h1>Deletar banco de dados</h1>
            <form method="post">
                <input type="text" name="db_name" placeholder="Digite o nome do banco de dados">
                <input type="submit" value="Deletar banco de dados">
            </form>
        </div>
    </body>
    </html>
    ''')
    
# ---------------------------------------------------------------------------------------------------------- #

'''
    summary
        Essa função é responsável por renderizar uma mensagem de sucesso
    param
        message: Mensagem a ser exibida, normalmente uma ação realizada com sucesso
    return
        render_template_string: Retorna o HTML renderizado com a mensagem de sucesso
'''
def render_success_message(message):
    return render_template_string(f'''
    <!doctype html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ação realizada</title>
        <link rel="stylesheet" href="{{{{ url_for('static', filename='style.css') }}}}"/>
    </head>
    <body>
        <div class="container">
            <div class="success-message">{message}</div>
            <a class="back-button" href="{{{{ url_for('index') }}}}">Voltar ao início</a>
        </div>
    </body>
    </html>
    ''')
    
# ---------------------------------------------------------------------------------------------------------- #

'''
    summary
        Essa função é responsável por renderizar a aplicação
'''
if __name__ == '__main__':
    app.run(debug=True)
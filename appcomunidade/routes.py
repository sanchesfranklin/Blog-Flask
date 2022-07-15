from flask import render_template, redirect, url_for, flash, request
from appcomunidade import app, database, bcrypt
from appcomunidade.forms import FormLogin, FormCriarConta, FormEditarPerfil, FormCriarPost
from appcomunidade.models import Usuario, Post
from flask_login import login_user, logout_user, current_user, login_required
import secrets
import os
from PIL import Image

@app.route("/")
def home():
    posts = Post.query.order_by(Post.id.desc())
    path_foto_perfil = url_for('static', filename='fotos_perfil/')
    return render_template('home.html', posts = posts, path_foto_perfil = path_foto_perfil)

@app.route("/contato")
def contato():
    return render_template('contato.html')

@app.route("/usuarios")
@login_required
def usuarios():
    path_foto_perfil = url_for('static', filename='fotos_perfil/')
    lista_usuarios = Usuario.query.all()
    return render_template('usuarios.html', lista_usuarios=lista_usuarios, path_foto_perfil=path_foto_perfil)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form_login = FormLogin()
    form_criarConta = FormCriarConta()

    if form_login.validate_on_submit() and 'botao_submit_login' in request.form:
        usuario = Usuario.query.filter_by(email=form_login.email.data).first()
        if usuario and bcrypt.check_password_hash(usuario.senha, form_login.senha.data):
            login_user(usuario, remember=form_login.lembrar_dados.data)
            flash(f'Login feito com sucesso no email: {form_login.email.data}', 'alert-success')
            pag_next = request.args.get('next')
            if pag_next:
                return redirect(pag_next)
            else:
                return redirect(url_for('home'))
        else:
            flash('Falha no login. Email ou Senha incorretos!', 'alert-danger')
    if form_criarConta.validate_on_submit() and 'botao_submit_criarconta' in request.form:
        # Declarando variáveis
        username = form_criarConta.username.data
        email = form_criarConta.email.data
        senha_crypt = bcrypt.generate_password_hash(form_criarConta.senha.data)
        # Criar usuário
        usuario = Usuario(username=username, email=email, senha=senha_crypt)
        # Adicionar a sessão do banco de dados
        database.session.add(usuario)
        # Dar um commit na sessão
        database.session.commit()
        flash(f'Conta criada com sucesso no email: {form_criarConta.email.data}', 'alert-success')
        return redirect(url_for('home'))

    return render_template('login.html', form_login = form_login, form_criarConta = form_criarConta)

@app.route('/sair')
@login_required
def sair():
    logout_user()
    flash('Logout feito com sucesso!', 'alert-success')
    return redirect(url_for('home'))

@app.route('/perfil')
@login_required
def perfil():
    foto_perfil = url_for('static', filename='fotos_perfil/{}'.format(current_user.foto_perfil))
    return render_template('perfil.html', foto_perfil=foto_perfil)


def salvar_imagem(imagem):
    # Adicionar o código no nome da imagem
    codigo = secrets.token_hex(8)
    nome, extensao = os.path.splitext(imagem.filename)
    nome_arquivo = nome + codigo + extensao
    caminho_completo = os.path.join(app.root_path, 'static/fotos_perfil', nome_arquivo)
    # Reduzir a imagem
    tamanho = (200, 200)
    imagem_reduzida = Image.open(imagem)
    imagem_reduzida.thumbnail(tamanho)
    # salvar a imagem
    imagem_reduzida.save(caminho_completo)
    return nome_arquivo

def atualizar_cursos(form):
    lista_cursos = []
    for campo in form:
        if 'curso_' in campo.name:
            if campo.data:
                lista_cursos.append(campo.label.text)

    print(lista_cursos)
    return ';'.join(lista_cursos)

@app.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    form = FormEditarPerfil()
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.username = form.username.data
        if form.foto_perfil.data:
            nome_imagem = salvar_imagem(form.foto_perfil.data)
            current_user.foto_perfil = nome_imagem
        current_user.cursos = atualizar_cursos(form)
        database.session.commit()
        flash(f'Perfil atualizado com sucesso', 'alert-success')
        return redirect(url_for('perfil'))
    elif request.method =="GET":
        form.email.data = current_user.email
        form.username.data = current_user.username
    foto_perfil = url_for('static', filename='fotos_perfil/{}'.format(current_user.foto_perfil))
    return render_template('editarperfil.html', foto_perfil=foto_perfil, form=form)

@app.route('/post/criar', methods=['GET', 'POST'])
@login_required
def criar_post():
    form = FormCriarPost()
    if form.validate_on_submit():
        post = Post(titulo = form.titulo.data, corpo = form.corpo.data, autor = current_user)
        database.session.add(post)
        database.session.commit()
        flash('Post criado com sucesso!', 'alert-success')
        return redirect(url_for('home'))
    return render_template('criarpost.html', form=form)



@app.route('/post/<post_id>')
def exibir_post(post_id):
    post = Post.query.get(post_id)
    path_foto_perfil = url_for('static', filename='fotos_perfil/')
    if current_user == post.autor:
        form = FormCriarPost()
    else:
        form = None
    return render_template('post.html', post=post, path_foto_perfil = path_foto_perfil, form = form)


@app.route('/post/editar/<post_id>', methods=['GET', 'POST'])
@login_required
def editar_post(post_id):
    post = Post.query.get(post_id)
    path_foto_perfil = url_for('static', filename='fotos_perfil/')
    if current_user == post.autor:
        form = FormCriarPost()
        if request.method == 'GET':
            form.titulo.data = post.titulo
            form.corpo.data = post.corpo
        elif form.validate_on_submit():
            post.titulo = form.titulo.data
            post.corpo = form.corpo.data
            database.session.commit()
            flash('Post atualizado com sucesso!', 'alert-success')
            return redirect(url_for('home'))
    else:
        form = None
    return render_template('editarpost.html', post=post, form = form, path_foto_perfil = path_foto_perfil)


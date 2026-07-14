# Gostoteca

Catálogo de preferências de mídia — jogos, filmes e livros — com uma camada de rede social.

Cada usuário registra suas preferências a partir de um catálogo de itens, atribui nota e opinião, e pode comentar as preferências de outros usuários. Há dois papéis: **usuário comum**, que gerencia as próprias preferências, comenta as dos outros e consulta o catálogo; e **administrador**, que gerencia o catálogo de itens e modera comentários e usuários.

Trabalho da disciplina Tópicos Avançados XI (UFPB) — Atividade 03: Aplicação CRUD.
Autores: Arthur Vieira e André Lopes.

## Tecnologias

- Python 3.13 e Django 6.0
- SQLite (banco padrão do Django)
- Tailwind CSS v4 via Play CDN — **as telas só aparecem estilizadas com acesso à internet**
- Modelo de usuário customizado (`usuarios.Usuario`), com autorização via Groups/Permissions do Django

## Como rodar

Todos os comandos partem desta pasta (a que contém o `manage.py`).

### 1. Ambiente virtual

Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Se o PowerShell bloquear a ativação, rode `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` e tente de novo.

### 2. Dependências

```bash
pip install -r requirements.txt
```

### 3. Banco de dados

```bash
python manage.py migrate
```

Isso cria o `db.sqlite3`, que não vai para o repositório — cada pessoa tem o seu.

### 4. Superusuário

```bash
python manage.py createsuperuser
```

O comando pede username, e-mail e senha. O **e-mail é obrigatório** aqui, diferente do Django padrão.

### 5. Subir o servidor

```bash
python manage.py runserver
```

Disponível em `http://127.0.0.1:8000/`.

## Rotas

| Rota | O que é |
|---|---|
| `/cadastro/` | Criar conta |
| `/login/` | Entrar |
| `/logout/` | Sair (aceita apenas POST) |
| `/admin/` | Django Admin (exige superusuário) |
| `/catalogo/` | Ainda não existe — retorna 404 |

## Testes

```bash
python manage.py test
```

São 10 testes cobrindo cadastro, login, logout, hash de senha e as validações de e-mail. Rodam automaticamente no GitHub Actions a cada push e pull request na `main` (`.github/workflows/ci.yml`).

## Docker

```bash
docker compose up --build
```

Sobe a aplicação em `http://localhost:8000/`. É um serviço só, já que o banco é um arquivo SQLite — não um container à parte.

A pasta do projeto é montada dentro do container, então o `db.sqlite3` é o mesmo do host. Se você já rodou o passo 3, não precisa migrar de novo. Se está começando direto pelo Docker:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

## Documentação de projeto

- `docs/superpowers/specs/` — decisões de design, divergências em relação ao documento da atividade e riscos aceitos
- `docs/superpowers/plans/` — plano de implementação das telas de autenticação

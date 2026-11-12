# OwlConvenial

Aplicação web em Flask para cadastro e login de pacientes, consulta de hospitais, agendamento de consultas e doações via Mercado Pago.

## Requisitos

- Python 3.10 ou superior.
- PostgreSQL 18 (ou compatível) para o banco de dados.
- Git, caso vá clonar o repositório.

## Instalação local no Windows

Abra o PowerShell na pasta do projeto e execute:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente virtual, execute nesta janela:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

O `requirements.txt` instala as bibliotecas usadas pelo app: Flask, Flask-SQLAlchemy, Flask-Mail, `psycopg2-binary`, bcrypt, requests, python-dotenv e itsdangerous. Para PostgreSQL, o projeto usa `psycopg2-binary`; não é necessário instalar o pacote `psycopg` (versão 3) nem a biblioteca de sistema `libpq`.

## Configuração do PostgreSQL

Inicie o serviço do PostgreSQL e crie o banco `convenio_db`. Pelo terminal, com as ferramentas do PostgreSQL no `PATH`:

```powershell
createdb -U postgres -h localhost -p 5432 convenio_db
psql -U postgres -h localhost -p 5432 -d convenio_db -f database.sql
```

O segundo comando cria as tabelas e índices definidos em [database.sql](database.sql). Se o banco já existir, pule `createdb`; o script usa `IF NOT EXISTS` para as tabelas e índices. O usuário do PostgreSQL precisa ter permissão para criar objetos no banco.

Crie seu arquivo de configuração local a partir do exemplo:

```powershell
Copy-Item .env.example .env
```

No `.env`, defina a conexão usando o driver do projeto. Exemplo para a configuração local informada:

```dotenv
DATABASE_URL=postgresql+psycopg2://postgres:SUA_SENHA@localhost:5432/convenio_db
```

Substitua `SUA_SENHA` pela senha configurada para o usuário PostgreSQL. Se a senha tiver caracteres especiais, use a forma codificada para URL. O `.env` contém segredos e é ignorado pelo Git; não o comite. O `.env.example` é apenas um modelo sem credenciais reais.

O Flask também chama `db.create_all()` ao iniciar e acrescenta o campo de telefone a uma tabela local antiga quando necessário. Para mudanças futuras no esquema, use migrações versionadas com Flask-Migrate/Alembic; `create_all()` não atualiza automaticamente todas as colunas existentes.

## Iniciar o app

Com o ambiente virtual ativado e o `.env` configurado:

```powershell
py app.py
```

Acesse <http://localhost:5000>. No Linux/macOS, os comandos equivalentes são `python3 -m venv .venv`, `source .venv/bin/activate` e `python app.py`.

## Esquema do banco

### `usuarios`

| Coluna | Tipo PostgreSQL | Regras e uso |
| --- | --- | --- |
| `id` | `SERIAL` | Chave primária. |
| `nome` | `VARCHAR(150)` | Obrigatório. |
| `cpf` | `VARCHAR(14)` | Obrigatório e único. |
| `genero` | `VARCHAR(30)` | Obrigatório. |
| `data_nascimento` | `DATE` | Obrigatório. |
| `email` | `VARCHAR(200)` | Opcional e único; pode ser usado como identificador. |
| `telefone` | `VARCHAR(20)` | Opcional e único; armazenado como dígitos e pode ser usado como identificador. |
| `senha` | `VARCHAR(255)` | Obrigatório; armazenado como hash bcrypt. |
| `email_verificado` | `BOOLEAN` | Obrigatório, padrão `FALSE`; o cadastro atual marca a conta como liberada para entrar. |

O formulário exige ao menos um contato: e-mail ou telefone. A conta pode ser usada imediatamente após o cadastro; o login aceita e-mail ou telefone junto com a senha.

### `agendamentos`

| Coluna | Tipo PostgreSQL | Regras e uso |
| --- | --- | --- |
| `id` | `SERIAL` | Chave primária. |
| `usuario_id` | `INTEGER` | Obrigatório; chave estrangeira para `usuarios.id`, com exclusão em cascata. |
| `hospital` | `VARCHAR(300)` | Obrigatório. |
| `data_consulta` | `DATE` | Obrigatório. |
| `horario` | `VARCHAR(10)` | Obrigatório. |
| `especialidade` | `VARCHAR(100)` | Obrigatório. |

Há um índice para buscar agendamentos por paciente e data.

### `doacoes`

| Coluna | Tipo PostgreSQL | Regras e uso |
| --- | --- | --- |
| `id` | `SERIAL` | Chave primária. |
| `usuario_id` | `INTEGER` | Obrigatório; chave estrangeira para `usuarios.id`, com exclusão em cascata. |
| `valor_centavos` | `INTEGER` | Obrigatório; valor da doação em centavos. |
| `status` | `VARCHAR(30)` | Obrigatório; padrão `pending`. |
| `mercado_pago_preference_id` | `VARCHAR(100)` | Opcional e único; preferência criada no Mercado Pago. |
| `mercado_pago_payment_id` | `VARCHAR(100)` | Opcional e único; pagamento confirmado. |
| `criado_em` | `TIMESTAMP` | Obrigatório; padrão `CURRENT_TIMESTAMP`. |

Há um índice para buscar doações por paciente.

## Serviços externos opcionais

### E-mail

As rotas antigas de confirmação e reenvio por e-mail usam Flask-Mail. Para enviar e-mails, configure `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD` e `MAIL_DEFAULT_SENDER` no `.env`. A confirmação por e-mail não é atualmente requisito para entrar após cadastro.

### Mercado Pago

Para habilitar doações, configure `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_WEBHOOK_SECRET` e `APP_BASE_URL`. No painel do Mercado Pago, aponte o webhook HTTPS para `https://SEU_DOMINIO/doacoes/webhook` e habilite o evento de pagamentos. Comece com credenciais de teste e só use credenciais de produção após publicar e validar a aplicação.

## O que falta para completar e publicar

- **Confirmação de contato:** escolher se haverá confirmação real por link de e-mail, código SMS ou ambos. SMS exige uma conta e credenciais de um provedor; o fluxo atual permite usar telefone como identificador, mas não envia códigos SMS.
- **Agendamentos:** definir como verificar disponibilidade e evitar dois pacientes reservarem o mesmo horário; validar datas/horários no servidor e definir cancelamento e confirmação.
- **Hospitais:** confirmar a fonte dos dados, cobertura geográfica, atualização e tratamento de falhas da busca externa.
- **Privacidade:** documentar o uso de dados pessoais, retenção e exclusão de contas, e revisar os requisitos legais aplicáveis.
- **Segurança de produção:** substituir a chave secreta de desenvolvimento, habilitar HTTPS, revisar cookies e permissões do banco e guardar segredos nas variáveis seguras do provedor de hospedagem.
- **Migrações:** adicionar Flask-Migrate/Alembic antes de evoluir o esquema em bancos já usados.
- **Operação:** escolher hospedagem para Flask e PostgreSQL, configurar domínio, logs, backups e monitoramento.
- **Validação:** executar e revisar os fluxos de cadastro, login por e-mail/telefone, agendamento, área do paciente, doações e webhook no ambiente configurado.

## Rotas principais

- `/` — página inicial.
- `/cadastro`, `/login`, `/logout` — conta e sessão.
- `/hospitais`, `/agendamento`, `/agendar`, `/paciente` — hospitais e consultas.
- `/doacoes` e `/doacoes/webhook` — doações e notificações do Mercado Pago.
- `/sobrenos` — informações do projeto.

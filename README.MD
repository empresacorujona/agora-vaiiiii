# OwlConvenial

Aplicação web em Flask para localizar hospitais próximos, registrar solicitações de horário e apoiar o projeto com doações. A busca de hospitais usa dados públicos do OpenStreetMap. As solicitações de horário ainda não são confirmadas pelo hospital.

## Requisitos

- Python 3.10 ou superior.
- SQLite para desenvolvimento local ou PostgreSQL para uma instalação compartilhada.
- Git é opcional.

## Instalação local no Windows

No PowerShell, abra a pasta do projeto e execute:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Se o PowerShell bloquear a ativação do ambiente virtual, libere-a somente nesta janela:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Gere uma chave para as sessões e substitua o valor de exemplo em `SECRET_KEY` no `.env`:

```powershell
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

Para SQLite local, defina no `.env`:

```dotenv
DATABASE_URL=sqlite:///owlconvenial.db
```

Para PostgreSQL, crie o banco `convenio_db`, aplique o esquema inicial e informe a conexão em `DATABASE_URL`:

```powershell
createdb -U postgres -h localhost -p 5432 convenio_db
psql -U postgres -h localhost -p 5432 -d convenio_db -f database.sql
```

```dotenv
DATABASE_URL=postgresql+psycopg2://postgres:SUA_SENHA@localhost:5432/convenio_db
```

Se a senha do banco tiver caracteres especiais, codifique-os para URL. O arquivo `.env` contém credenciais e não deve ser compartilhado ou enviado ao Git. O `.env.example` é somente um modelo.

Inicie o servidor local:

```powershell
py app.py
```

Abra <http://localhost:5000>. O servidor integrado do Flask é para desenvolvimento, não para publicação.

## Configuração de e-mail

O SMTP é necessário para confirmar o e-mail no cadastro e enviar códigos de acesso nos logins. Configure no `.env`:

```dotenv
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app
MAIL_DEFAULT_SENDER=seu-email@gmail.com
```

No Gmail, use uma senha de app, não a senha normal da conta. No cadastro com e-mail, a pessoa informa um código de seis dígitos e entra após confirmá-lo. Nos próximos logins, a senha é seguida por outro código. Os códigos expiram em 10 minutos. Contas cadastradas somente com telefone ainda não têm verificação por SMS.

## Doações

Sem `MERCADOPAGO_ACCESS_TOKEN`, a página informa que o checkout está indisponível. Para habilitá-lo, configure as credenciais de teste no `.env` e valide a integração antes de usar credenciais de produção:

```dotenv
MERCADOPAGO_ACCESS_TOKEN=SEU_ACCESS_TOKEN
MERCADOPAGO_WEBHOOK_SECRET=SEGREDO_DO_WEBHOOK
APP_BASE_URL=https://sua-url-publica
```

O Mercado Pago precisa acessar uma URL pública HTTPS para enviar notificações. Configure no painel o webhook `https://sua-url-publica/doacoes/webhook` e habilite o evento de pagamentos. Para desenvolvimento local, use um túnel HTTPS temporário; `localhost` não recebe webhooks externos.

## Fluxos atuais e limitações

- Cadastro por e-mail: confirmação por código e entrada automática após a confirmação.
- Login com e-mail confirmado: senha e código de acesso. Contas sem e-mail não conseguem receber código e ainda entram somente com senha.
- Agendamentos: valida os campos enviados, rejeita horários passados e duplicados quando o índice correspondente existe. O sistema registra uma solicitação, não consulta a disponibilidade nem recebe confirmação do hospital.
- Hospitais: busca pública do OpenStreetMap com localização aproximada por IP. Se a localização falhar, são mostrados resultados da região de São Paulo.
- Doações: checkout permanece desabilitado até configurar o Access Token do Mercado Pago.
- O esquema é criado pelo app e alguns campos novos são acrescentados ao iniciar. `db.create_all()` não substitui migrações versionadas para futuras mudanças.

## Correções e decisões pendentes

1. **Confirmar solicitações com hospitais:** escolher uma fonte de disponibilidade real, integração ou processo de confirmação; definir status, cancelamento e horários válidos por unidade.
2. **Resolver autenticação de contas sem e-mail:** implementar verificação por SMS ou exigir e confirmar um endereço de e-mail antes de permitir login sem código.
3. **Testar entrega real de e-mail:** validar SMTP, entrega, expiração, reenvio e recuperação de contas num ambiente controlado. Os fluxos da aplicação não substituem um teste de entrega com a conta configurada.
4. **Preparar migrações do banco:** adotar Flask-Migrate/Alembic e aplicar com segurança as colunas de código e o índice único de horários em bancos existentes; verificar duplicatas e fazer backup antes da migração.
5. **Completar privacidade e proteção dos dados:** documentar uso, retenção e exclusão de CPF, nascimento, gênero, telefone e e-mail; revisar permissões e requisitos da LGPD.
6. **Validar e publicar o Mercado Pago:** obter credenciais, testar checkout e webhook com HTTPS, validar estados de pagamento e só então habilitar produção.
7. **Preparar produção:** escolher hospedagem, configurar servidor WSGI, domínio e HTTPS, guardar segredos no provedor, além de configurar logs, backups e monitoramento.
8. **Criar testes automatizados persistentes:** cobrir cadastro, códigos, login, solicitações, cancelamentos, doações e webhooks com banco de teste e serviços externos simulados.
9. **Revisar a busca de hospitais:** confirmar cobertura e regras de uso do OpenStreetMap/Nominatim, considerar busca por cidade ou localização escolhida pela pessoa e informar a origem dos resultados.

## Rotas principais

- `/` — página inicial.
- `/cadastro`, `/login`, `/logout` — conta e sessão.
- `/verificar-email-codigo` — confirmação do e-mail no cadastro.
- `/verificar-codigo` — código de acesso do login.
- `/reenviar-verificacao` — reenviar código de confirmação do e-mail.
- `/hospitais`, `/agendamento`, `/agendar`, `/paciente` — busca, solicitação de horário e área do paciente.
- `/doacoes`, `/doacoes/webhook` — doações e notificações do Mercado Pago.
- `/sobrenos` — informações do projeto.

-- Schema inicial do OwlConvenial para PostgreSQL.
-- Execute conectado ao banco convenio_db (por exemplo, usando psql).

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    genero VARCHAR(30) NOT NULL,
    data_nascimento DATE NOT NULL,
    email VARCHAR(200) UNIQUE,
    telefone VARCHAR(20) UNIQUE,
    senha VARCHAR(255) NOT NULL,
    email_verificado BOOLEAN NOT NULL DEFAULT FALSE,
    login_code_hash VARCHAR(64),
    login_code_expires_at TIMESTAMP,
    login_code_sent_at TIMESTAMP,
    login_code_attempts INTEGER NOT NULL DEFAULT 0,
    email_verification_code_hash VARCHAR(64),
    email_verification_code_expires_at TIMESTAMP,
    email_verification_code_sent_at TIMESTAMP,
    email_verification_code_attempts INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS agendamentos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    hospital VARCHAR(300) NOT NULL,
    data_consulta DATE NOT NULL,
    horario VARCHAR(10) NOT NULL,
    especialidade VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS doacoes (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    valor_centavos INTEGER NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    mercado_pago_preference_id VARCHAR(100) UNIQUE,
    mercado_pago_payment_id VARCHAR(100) UNIQUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_agendamentos_usuario_data
    ON agendamentos (usuario_id, data_consulta);
CREATE UNIQUE INDEX IF NOT EXISTS uq_agendamento_slot
    ON agendamentos (hospital, data_consulta, horario);
CREATE INDEX IF NOT EXISTS ix_doacoes_usuario
    ON doacoes (usuario_id);

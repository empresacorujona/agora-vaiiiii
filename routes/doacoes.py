import hashlib
import hmac
import uuid
from decimal import Decimal, InvalidOperation

import requests
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for

from models import Doacao, db

doacao_bp = Blueprint("doacoes", __name__)

STATUS_LABELS = {
    "pending": "Aguardando pagamento",
    "in_process": "Em análise",
    "paid": "Confirmada",
    "rejected": "Recusada",
    "cancelled": "Cancelada",
    "refunded": "Estornada",
    "checkout_error": "Não foi possível iniciar o pagamento",
}


def _usuario_id():
    user_id = session.get("usuario_id")
    if not user_id:
        return None
    return user_id


def _mercadopago_headers():
    token = current_app.config.get("MERCADOPAGO_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("MERCADOPAGO_ACCESS_TOKEN não está configurado.")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@doacao_bp.route("/doacoes", methods=["GET", "POST"])
def pagina_doacoes():
    user_id = _usuario_id()
    if not user_id:
        flash("Entre na sua conta para realizar uma doação.", "info")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        try:
            valor = Decimal(request.form.get("valor", "").replace(",", "."))
            centavos = int(valor * 100)
        except (InvalidOperation, ValueError, OverflowError):
            flash("Informe um valor válido para a doação.", "danger")
            return redirect(url_for("doacoes.pagina_doacoes"))
        if valor != Decimal(centavos) / 100:
            flash("Informe um valor com no máximo duas casas decimais.", "danger")
            return redirect(url_for("doacoes.pagina_doacoes"))
        if centavos < 100 or centavos > 10000000:
            flash("O valor deve estar entre R$ 1,00 e R$ 100.000,00.", "danger")
            return redirect(url_for("doacoes.pagina_doacoes"))
        if not current_app.config.get("MERCADOPAGO_ACCESS_TOKEN"):
            flash("O checkout ainda não está configurado. Consulte as instruções de configuração.", "warning")
            return redirect(url_for("doacoes.pagina_doacoes"))

        doacao = Doacao(usuario_id=user_id, valor_centavos=centavos, status="pending")
        db.session.add(doacao)
        db.session.commit()

        base_url = current_app.config["APP_BASE_URL"]
        back_url = f"{base_url}{url_for('doacoes.retorno')}?doacao_id={doacao.id}"
        payload = {
            "items": [{
                "id": f"doacao-{doacao.id}",
                "title": "Doação para o OwlConvenial",
                "description": "Contribuição voluntária ao projeto OwlConvenial",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": centavos / 100,
            }],
            "payer": {"email": session.get("usuario_email")},
            "external_reference": str(doacao.id),
            "back_urls": {
                "success": f"{back_url}&resultado=sucesso",
                "pending": f"{back_url}&resultado=pendente",
                "failure": f"{back_url}&resultado=falha",
            },
            "auto_return": "approved",
            "statement_descriptor": "OWLCONVENIAL",
        }
        if base_url.startswith("https://"):
            payload["notification_url"] = f"{base_url}{url_for('doacoes.webhook')}"

        try:
            response = requests.post(
                f"{current_app.config['MERCADOPAGO_API_URL']}/checkout/preferences",
                json=payload,
                headers={**_mercadopago_headers(), "X-Idempotency-Key": str(uuid.uuid4())},
                timeout=20,
            )
            response.raise_for_status()
            preference = response.json()
            checkout_url = preference.get("init_point")
            if not checkout_url:
                raise RuntimeError("O Mercado Pago não retornou o link do checkout.")
            doacao.mercado_pago_preference_id = preference.get("id")
            db.session.commit()
            return redirect(checkout_url)
        except (requests.RequestException, ValueError, RuntimeError) as error:
            current_app.logger.exception("Falha ao criar preferência no Mercado Pago")
            doacao.status = "checkout_error"
            db.session.commit()
            flash("Não foi possível abrir o checkout agora. Tente novamente mais tarde.", "danger")
            return redirect(url_for("doacoes.pagina_doacoes"))

    doacoes = Doacao.query.filter_by(usuario_id=user_id).order_by(Doacao.criado_em.desc()).all()
    return render_template("doacoes.html", doacoes=doacoes, status_labels=STATUS_LABELS)


@doacao_bp.route("/doacoes/retorno")
def retorno():
    user_id = _usuario_id()
    if not user_id:
        return redirect(url_for("auth.login"))
    doacao_id = request.args.get("doacao_id", type=int)
    doacao = Doacao.query.filter_by(id=doacao_id, usuario_id=user_id).first_or_404()
    payment_id = request.args.get("payment_id")
    if payment_id and current_app.config.get("MERCADOPAGO_ACCESS_TOKEN"):
        try:
            response = requests.get(
                f"{current_app.config['MERCADOPAGO_API_URL']}/v1/payments/{payment_id}",
                headers=_mercadopago_headers(),
                timeout=15,
            )
            response.raise_for_status()
            pagamento = response.json()
            amount = int(Decimal(str(pagamento.get("transaction_amount", 0))) * 100)
            if (str(pagamento.get("external_reference")) == str(doacao.id)
                    and amount == doacao.valor_centavos
                    and pagamento.get("currency_id") == "BRL"):
                status = pagamento.get("status")
                doacao.status = {
                    "approved": "paid", "pending": "pending", "in_process": "in_process",
                    "authorized": "in_process", "rejected": "rejected", "cancelled": "cancelled",
                    "refunded": "refunded", "charged_back": "refunded",
                }.get(status, doacao.status)
                doacao.mercado_pago_payment_id = str(pagamento.get("id"))
                db.session.commit()
        except (requests.RequestException, ValueError, InvalidOperation):
            current_app.logger.exception("Falha ao atualizar o retorno da doação")
    flash("Retorno do checkout recebido. O status é atualizado após confirmação do Mercado Pago.", "info")
    return redirect(url_for("doacoes.pagina_doacoes"))


def _validar_assinatura_webhook(data_id):
    secret = current_app.config.get("MERCADOPAGO_WEBHOOK_SECRET")
    assinatura = request.headers.get("x-signature", "")
    request_id = request.headers.get("x-request-id", "")
    if not secret or not assinatura or not request_id or not data_id:
        return False
    partes = dict(
        item.strip().split("=", 1)
        for item in assinatura.split(",")
        if "=" in item
    )
    ts, assinatura_recebida = partes.get("ts"), partes.get("v1")
    if not ts or not assinatura_recebida:
        return False
    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    assinatura_esperada = hmac.new(
        secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(assinatura_esperada, assinatura_recebida)


@doacao_bp.route("/doacoes/webhook", methods=["POST"])
def webhook():
    if not current_app.config.get("MERCADOPAGO_WEBHOOK_SECRET"):
        return "Webhook não configurado", 503
    body = request.get_json(silent=True) or {}
    data_id = request.args.get("data.id") or (body.get("data") or {}).get("id")
    if body.get("type") not in (None, "payment") or not _validar_assinatura_webhook(str(data_id or "")):
        return "Assinatura inválida", 401

    try:
        response = requests.get(
            f"{current_app.config['MERCADOPAGO_API_URL']}/v1/payments/{data_id}",
            headers=_mercadopago_headers(),
            timeout=20,
        )
        response.raise_for_status()
        pagamento = response.json()
    except (requests.RequestException, ValueError, RuntimeError):
        current_app.logger.exception("Não foi possível consultar o pagamento notificado")
        return "Falha ao consultar pagamento", 502

    doacao_id = pagamento.get("external_reference")
    doacao = Doacao.query.filter_by(id=doacao_id).first() if str(doacao_id or "").isdigit() else None
    if not doacao:
        return "Doação não encontrada", 404
    try:
        valor_pago = int(Decimal(str(pagamento.get("transaction_amount", 0))) * 100)
    except (InvalidOperation, ValueError):
        return "Valor inválido", 400
    if valor_pago != doacao.valor_centavos or pagamento.get("currency_id") != "BRL":
        current_app.logger.error("Valor do pagamento diverge da doação %s", doacao.id)
        return "Valor divergente", 409

    status = pagamento.get("status")
    status_map = {
        "approved": "paid",
        "pending": "pending",
        "in_process": "in_process",
        "authorized": "in_process",
        "rejected": "rejected",
        "cancelled": "cancelled",
        "refunded": "refunded",
        "charged_back": "refunded",
    }
    if status in status_map:
        doacao.status = status_map[status]
        doacao.mercado_pago_payment_id = str(pagamento.get("id"))
        db.session.commit()
    return "OK", 200

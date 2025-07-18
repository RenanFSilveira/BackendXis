import smtplib
import os
import psycopg2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import json
import requests
import pytz

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fuso horário do Brasil (Brasília)
br_tz = pytz.timezone('America/Sao_Paulo')
hora_brasil = datetime.now(br_tz).strftime('%d/%m/%Y às %H:%M:%S')

email_bp = Blueprint('email', __name__)

@email_bp.route('/processa-leads-pendentes', methods=['POST'])
def processa_leads_pendentes():
    # 1) Autentica a chamada do cron job
    cron_key = request.headers.get('X-CRON-KEY')
    if cron_key != os.getenv('CRON_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')

        headers = {
            "apikey": SUPABASE_API_KEY,
            "Authorization": f"Bearer {SUPABASE_API_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        # 2) Buscar os leads não notificados
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/form_submissions?email_enviado=eq.false",
            headers=headers
        )
        if response.status_code != 200:
            logging.error(f"Erro ao buscar leads: {response.text}")
            return jsonify({'error': 'Erro ao buscar leads'}), 500

        leads = response.json()
        processed = 0

        # 3) Envia os emails e marca como enviado
        for lead in leads:
            subject = f"Novo Lead – {lead['name']}"
            br_tz = pytz.timezone('America/Sao_Paulo')
            data_hora = datetime.now(br_tz).strftime('%d/%m/%Y %H:%M')
            body = f"""
            <html><body>
              <h2>Novo Lead Recebido</h2>
              <p><strong>Data/Hora:</strong> {data_hora}</p>
              <p><strong>Nome:</strong> {lead['name']}</p>
              <p><strong>E‑mail:</strong> {lead['email']}</p>
              <p><strong>Telefone:</strong> {lead['phone']}</p>
              <p><strong>Mensagem:</strong> {lead['message'] or '—'}</p>
            </body></html>
            """
            success, msg = send_email(
                to_email=os.getenv('NOTIFICATION_EMAIL'),
                subject=subject,
                body=body
            )

            if success:
                # Atualiza o campo email_enviado
                update_response = requests.patch(
                    f"{SUPABASE_URL}/rest/v1/form_submissions?id=eq.{lead['id']}",
                    headers=headers,
                    json={"email_enviado": True}
                )
                if update_response.status_code in [200, 204]:
                    processed += 1
                else:
                    logging.error(f"Erro ao atualizar lead {lead['id']}: {update_response.text}")
            else:
                logging.error(f"Falha ao notificar lead {lead['id']}: {msg}")

        return jsonify({'processed': processed}), 200

    except Exception as e:
        logging.exception("Erro ao processar leads pendentes")
        return jsonify({'error': str(e)}), 500

def send_email(to_email, subject, body, smtp_server=None, smtp_port=None, smtp_user=None, smtp_password=None):
    """
    Função para enviar e-mail usando SMTP
    """
    if not to_email:
        logging.error("E-mail de destino não especificado.")
        return False, "E-mail de destino não especificado"
    try:
        # Configurações padrão do Gmail (pode ser alterado via variáveis de ambiente)
        smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        smtp_user = smtp_user or os.getenv('SMTP_USER')
        smtp_password = smtp_password or os.getenv('SMTP_PASSWORD')
        
        logging.info(f"Tentando enviar e-mail para: {to_email}")
        logging.info(f"SMTP Server: {smtp_server}, Port: {smtp_port}, User: {smtp_user}")

        if not smtp_user or not smtp_password:
            logging.error("Credenciais SMTP não configuradas. Verifique SMTP_USER e SMTP_PASSWORD.")
            raise ValueError("Credenciais SMTP não configuradas")
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Adicionar corpo do e-mail
        msg.attach(MIMEText(body, 'html'))
        
        # Conectar ao servidor SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Habilitar segurança
        server.login(smtp_user, smtp_password)
        
        # Enviar e-mail
        text = msg.as_string()
        server.sendmail(smtp_user, to_email, text)
        server.quit()
        
        logging.info("E-mail enviado com sucesso!")
        return True, "E-mail enviado com sucesso"
        
    except Exception as e:
        logging.error(f"Erro ao enviar e-mail: {e}", exc_info=True) # exc_info=True para logar o traceback completo
        return False, str(e)

import json
from flask import request, jsonify
from datetime import datetime
import logging

@email_bp.route('/send-lead-notification', methods=['POST'])
def send_lead_notification():
    """
    Endpoint para enviar notificação de novo lead, agora aceitando texto bruto
    e convertendo com json.loads independentemente do Content-Type.
    """
    try:
        # 1) Leitura do corpo bruto como texto
        raw = request.get_data(as_text=True)
        logging.info(f"RAW BODY: {raw}")

        # 2) Parse manual do JSON
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logging.error("Falha ao decodificar JSON do corpo da requisição.")
            return jsonify({'error': 'Payload inválido: não é um JSON válido'}), 400

        logging.info(f"Requisição recebida para /send-lead-notification com dados: {data}")

        # 3) Validação de campos obrigatórios
        required_fields = ['name', 'email', 'phone']
        for field in required_fields:
            if field not in data:
                logging.warning(f"Campo obrigatório ausente: {field}")
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400

        # 4) Extrair dados do lead
        lead_name    = data['name']
        lead_email   = data['email']
        lead_phone   = data['phone']
        lead_message = data.get('message', 'Não informado')

        # 5) Verificar e-mail de notificação
        notification_email = os.getenv('NOTIFICATION_EMAIL')
        if not notification_email:
            logging.error("E-mail de notificação não configurado. Verifique NOTIFICATION_EMAIL.")
            return jsonify({'error': 'E-mail de notificação não configurado'}), 500

        # 6) Montar e enviar o e-mail
        subject = f"Novo Lead - {lead_name}"
        body = f"""
        <html>
        <body>
            <h2>Novo Lead Recebido!</h2>
            <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
            <hr>
            <p><strong>Nome:</strong> {lead_name}</p>
            <p><strong>E-mail:</strong> {lead_email}</p>
            <p><strong>Telefone:</strong> {lead_phone}</p>
            <p><strong>Mensagem:</strong> {lead_message}</p>
            <hr>
            <p><em>Este e-mail foi enviado automaticamente pelo sistema de notificação de leads.</em></p>
        </body>
        </html>
        """

        success, message = send_email(notification_email, subject, body)
        if success:
            logging.info("Notificação de lead enviada com sucesso.")
            return jsonify({'message': 'Notificação enviada com sucesso'}), 200
        else:
            logging.error(f"Falha ao enviar notificação de lead: {message}")
            return jsonify({'error': f'Erro ao enviar e-mail: {message}'}), 500

    except Exception as e:
        logging.error(f"Erro inesperado no endpoint /send-lead-notification: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@email_bp.route('/test-email', methods=['POST'])
def test_email():
    """
    Endpoint para testar o envio de e-mail
    """
    try:
        data = request.get_json()
        test_email = data.get('email')
        
        logging.info(f"Requisição recebida para /test-email com e-mail: {test_email}")

        if not test_email:
            logging.warning("E-mail de teste é obrigatório.")
            return jsonify({'error': 'E-mail de teste é obrigatório'}), 400
        
        subject = "Teste de Envio de E-mail"
        br_tz = pytz.timezone('America/Sao_Paulo')
        data_hora = datetime.now(br_tz).strftime('%d/%m/%Y às %H:%M:%S')
        body = f"""
        <html>
        <body>
            <h2>Teste de Configuração</h2>
            <p>Se você recebeu este e-mail, a configuração está funcionando corretamente!</p>
            <p><strong>Data/Hora do teste:</strong> {data_hora}</p>
        </body>
        </html>
        """.format(datetime.now().strftime('%d/%m/%Y às %H:%M:%S'))
        
        success, message = send_email(test_email, subject, body)
        
        if success:
            logging.info("E-mail de teste enviado com sucesso.")
            return jsonify({'message': 'E-mail de teste enviado com sucesso'}), 200
        else:
            logging.error(f"Falha ao enviar e-mail de teste: {message}")
            return jsonify({'error': f'Erro ao enviar e-mail de teste: {message}'}), 500
            
    except Exception as e:
        logging.error(f"Erro inesperado no endpoint /test-email: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


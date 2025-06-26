# Sistema de Notificação por E-mail para Leads

## Visão Geral

Este documento apresenta a implementação completa de um sistema de notificação por e-mail que é automaticamente disparado quando novos leads são cadastrados através do formulário de contato do seu site React integrado com Supabase.

## Arquitetura da Solução

O sistema foi desenvolvido com uma arquitetura simples e eficiente, composta por três componentes principais:

1. **Frontend React**: Seu site existente com formulário de contato integrado ao Supabase
2. **Backend Python/Flask**: Serviço responsável pelo envio de e-mails
3. **Supabase Webhook**: Trigger que conecta a inserção de dados ao backend

### Fluxo de Funcionamento

1. Usuário preenche e envia o formulário no site
2. Dados são inseridos na tabela `form_submissions` do Supabase
3. Webhook do Supabase é disparado automaticamente
4. Backend Flask recebe os dados e envia e-mail de notificação
5. Você recebe o e-mail com as informações do novo lead

## Componentes Desenvolvidos

### Backend Flask

O backend foi desenvolvido em Python usando Flask, seguindo as melhores práticas de desenvolvimento. Os principais arquivos criados foram:

#### Estrutura do Projeto
```
email_notification_backend/
├── src/
│   ├── main.py                    # Arquivo principal da aplicação
│   ├── routes/
│   │   └── email_notification.py  # Rotas para envio de e-mail
│   └── models/                    # Modelos de dados (existente)
├── venv/                          # Ambiente virtual Python
├── requirements.txt               # Dependências do projeto
└── .env.example                   # Exemplo de configuração
```

#### Endpoints Disponíveis

**POST /api/send-lead-notification**
- Recebe dados do lead via webhook do Supabase
- Envia e-mail de notificação formatado
- Retorna status de sucesso ou erro

**POST /api/test-email**
- Endpoint para testar a configuração de e-mail
- Útil para validar credenciais SMTP antes da implementação

### Configuração do Webhook no Supabase

Foi criado um script SQL que configura automaticamente o webhook no Supabase para disparar sempre que uma nova linha for inserida na tabela `form_submissions`.

## Configuração e Instalação

### Pré-requisitos

1. Python 3.11 ou superior
2. Conta de e-mail com SMTP habilitado (Gmail recomendado)
3. Acesso ao painel do Supabase do seu projeto

### Configuração do E-mail

Para usar o Gmail como provedor SMTP, você precisará:

1. **Ativar a verificação em duas etapas** na sua conta Google
2. **Gerar uma senha de app** específica para este sistema
3. **Configurar as variáveis de ambiente** com suas credenciais

#### Gerando Senha de App no Gmail

1. Acesse [myaccount.google.com](https://myaccount.google.com)
2. Vá em "Segurança" → "Verificação em duas etapas"
3. Role até "Senhas de app" e clique em "Gerar"
4. Escolha "Outro" e digite "Sistema de Notificação de Leads"
5. Use a senha gerada (16 caracteres) no lugar da sua senha normal

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto backend com as seguintes configurações:

```env
# Configurações de E-mail SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_de_app_de_16_caracteres

# E-mail onde você quer receber as notificações
NOTIFICATION_EMAIL=seu_email_de_notificacao@gmail.com
```

### Instalação Local

1. **Clone ou extraia o projeto backend**
2. **Ative o ambiente virtual**:
   ```bash
   cd email_notification_backend
   source venv/bin/activate
   ```
3. **Configure as variáveis de ambiente** (arquivo `.env`)
4. **Execute o servidor**:
   ```bash
   python src/main.py
   ```

### Configuração do Webhook no Supabase

1. **Acesse o SQL Editor** no painel do Supabase
2. **Execute o seguinte comando SQL** (substitua `YOUR_BACKEND_URL` pela URL do seu backend):

```sql
create trigger "lead_notification_webhook" 
after insert
on "public"."form_submissions" 
for each row
execute function "supabase_functions"."http_request"(
  'YOUR_BACKEND_URL/api/send-lead-notification',
  'POST',
  '{"Content-Type":"application/json"}',
  '{}',
  '5000'
);
```

## Teste do Sistema

### Teste Local

1. **Inicie o backend Flask** localmente
2. **Teste o endpoint de e-mail**:
   ```bash
   curl -X POST http://localhost:5000/api/test-email \
   -H "Content-Type: application/json" \
   -d '{"email":"seu_email@gmail.com"}'
   ```

### Teste de Integração

1. **Configure o webhook** no Supabase apontando para seu backend
2. **Insira um registro de teste** na tabela:
   ```sql
   INSERT INTO form_submissions (name, email, phone, message) 
   VALUES ('Teste', 'teste@email.com', '(11) 99999-9999', 'Mensagem de teste');
   ```
3. **Verifique se o e-mail foi recebido**

## Deploy em Produção

### Opções de Deploy

1. **Heroku** (recomendado para simplicidade)
2. **Railway**
3. **DigitalOcean App Platform**
4. **AWS/Google Cloud** (para maior controle)

### Preparação para Deploy

1. **Atualize o requirements.txt**:
   ```bash
   pip freeze > requirements.txt
   ```

2. **Configure as variáveis de ambiente** na plataforma escolhida

3. **Atualize a URL do webhook** no Supabase com a URL de produção

## Formato do E-mail de Notificação

O sistema envia e-mails HTML formatados com as seguintes informações:

- **Assunto**: "Novo Lead - [Nome do Lead]"
- **Data e hora** do cadastro
- **Nome completo** do lead
- **E-mail** para contato
- **Telefone** para contato
- **Mensagem** (se fornecida)

### Exemplo de E-mail

```
Assunto: Novo Lead - João Silva

Novo Lead Recebido!

Data/Hora: 26/06/2025 às 14:30:15

Nome: João Silva
E-mail: joao.silva@email.com
Telefone: (11) 99999-9999
Mensagem: Gostaria de saber mais sobre os produtos

Este e-mail foi enviado automaticamente pelo sistema de notificação de leads.
```

## Monitoramento e Manutenção

### Logs do Sistema

O Flask gera logs automáticos que incluem:
- Requisições recebidas
- Status de envio de e-mails
- Erros de configuração ou conectividade

### Troubleshooting Comum

**E-mails não estão sendo enviados:**
1. Verifique as credenciais SMTP
2. Confirme que a senha de app está correta
3. Teste a conectividade com o servidor SMTP

**Webhook não está disparando:**
1. Verifique se o trigger foi criado corretamente no Supabase
2. Confirme se a URL do backend está acessível
3. Verifique os logs do webhook no Supabase

**Erros de CORS:**
1. Confirme que o Flask-CORS está instalado
2. Verifique se o CORS está habilitado no main.py

## Segurança

### Boas Práticas Implementadas

1. **Variáveis de ambiente** para credenciais sensíveis
2. **Timeout configurado** para requisições HTTP (5 segundos)
3. **Validação de dados** nos endpoints
4. **CORS habilitado** para integração frontend-backend

### Recomendações Adicionais

1. **Use HTTPS** em produção
2. **Configure rate limiting** se necessário
3. **Monitore logs** regularmente
4. **Mantenha dependências atualizadas**

## Próximos Passos

### Melhorias Possíveis

1. **Templates de e-mail personalizáveis**
2. **Múltiplos destinatários** de notificação
3. **Integração com CRM** (HubSpot, Pipedrive, etc.)
4. **Dashboard de analytics** dos leads
5. **Notificações por WhatsApp** (usando APIs como Twilio)

### Expansão do Sistema

O sistema atual pode ser facilmente expandido para:
- Enviar diferentes tipos de notificação baseados no conteúdo do formulário
- Integrar com sistemas de automação de marketing
- Adicionar resposta automática para o lead
- Implementar sistema de follow-up automatizado

## Conclusão

O sistema de notificação por e-mail foi desenvolvido seguindo as melhores práticas de desenvolvimento, com foco na simplicidade, confiabilidade e facilidade de manutenção. A arquitetura modular permite futuras expansões e integrações, enquanto a documentação completa facilita a manutenção e troubleshooting.

A implementação garante que você seja notificado imediatamente sempre que um novo lead se cadastrar através do seu site, permitindo um atendimento mais rápido e eficiente dos potenciais clientes.


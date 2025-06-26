-- Script para configurar webhook no Supabase
-- Este script deve ser executado no SQL Editor do Supabase

-- Substitua 'YOUR_BACKEND_URL' pela URL do seu backend Flask
-- Exemplo: 'https://seu-backend.herokuapp.com/api/send-lead-notification'

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

-- Explicação dos parâmetros:
-- 1. URL do endpoint: onde o webhook será enviado
-- 2. Método HTTP: POST
-- 3. Headers: Content-Type como application/json
-- 4. Parâmetros adicionais: {} (vazio)
-- 5. Timeout: 5000ms (5 segundos)

-- Para testar se o webhook está funcionando, você pode inserir um registro de teste:
-- INSERT INTO form_submissions (name, email, phone, message) 
-- VALUES ('Teste', 'teste@email.com', '(11) 99999-9999', 'Mensagem de teste');

-- Para remover o webhook (se necessário):
-- DROP TRIGGER IF EXISTS "lead_notification_webhook" ON "public"."form_submissions";


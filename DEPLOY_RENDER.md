# 🚀 Guia de Deploy no Render.com

## 1️⃣ Pré-requisitos

✅ Projeto versionado no GitHub  
✅ Supabase configurado com as tabelas criadas  
✅ Conta no Render.com (free ou paga)

## 2️⃣ Criar Tabelas no Supabase

Execute o SQL do arquivo `supabase_table.sql` no editor SQL do Supabase:

Tabelas criadas:

- `medicoes` - Registros individuais de leitura
- `colecoes` - Sessões/coletas (com items em JSON)

```sql
-- Execute o conteúdo de supabase_table.sql
```

## 3️⃣ Gerar Variáveis de Ambiente

### SECRET_KEY (obrigatória)

```bash
python -c "import os; print(os.urandom(24).hex())"
```

Copie a saída e guarde para usar no Render.

### SUPABASE_URL e SUPABASE_KEY

No dashboard do Supabase:

1. Vá para **Settings → API**
2. Copie:
   - `Project URL` → **SUPABASE_URL**
   - `anon public` → **SUPABASE_KEY**

## 4️⃣ Conectar GitHub no Render

1. Acesse [render.com](https://render.com)
2. Clique em **New +** → **Web Service**
3. Selecione seu repositório do GitHub
4. Configure:
   - **Name**: `app-scan-meter`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn server:app`
   - **Region**: Singapore/Oregon (choose one)
   - **Plan**: Free (ou Starter)

## 5️⃣ Configurar Variáveis de Ambiente

No painel do Render, vá para **Environment**:

```
FLASK_ENV=production
FLASK_DEBUG=False
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon-aqui
SUPABASE_TABLE=medicoes
SECRET_KEY=sua-chave-gerada-aqui
API_KEY=                          # (deixe vazio ou coloque uma chave segura)
```

**Importante**: Use valores individuais, não crie um arquivo `.env`

## 6️⃣ Deploy

1. Clique em **Create Web Service**
2. Render começará a fazer o build automaticamente
3. Aguarde até ver "Your service is live"
4. Copie o URL: `https://seu-app.onrender.com`

## 7️⃣ Testar Aplicação

```bash
curl https://seu-app.onrender.com
# Deve retornar a página HTML
```

## 📋 Verificação de Variáveis

No Render dashboard, clique em **Logs** para ver erros:

```
⚠️  SUPABASE_URL and SUPABASE_KEY not configured!
```

Se vir esta mensagem, as variáveis não foram configuradas corretamente.

## 🔄 Re-deploy

Toda vez que fizer push no GitHub:

- Render faz rebuild automaticamente
- ✅ Dados do Supabase persistem
- ✅ PDFs são gerados sob demanda

## 🐛 Debug

### Ver logs em tempo real

```bash
# No Render dashboard → Logs
```

### Conectar manualmente (SSH)

```bash
# Disponível no plano Starter+
```

### Verificar saúde da API

```bash
curl https://seu-app.onrender.com/api/report/test
# Retorna JSON error se não houver coleta
```

## 📊 Monitoramento

- **Logs**: Render → Logs
- **Banco**: Supabase Dashboard
- **CPU/Memória**: Render → Metrics (plano Starter+)

## ⚠️ Limites Free Plan

- App _sleeps_ após 15 min de inatividade
- 0.5 GB RAM
- Reinicia automaticamente no horário
- Disk é efêmero (mas dados estão no Supabase ✅)

## 📞 Problemas Comuns

### "ModuleNotFoundError: No module named 'supabase'"

→ Verificar `requirements.txt` - tem `supabase` listado?

### "Connection refused" ao Supabase

→ SUPABASE_URL e SUPABASE_KEY corretos?

### "Relation 'colecoes' does not exist"

→ Executar SQL em supabase_table.sql

### "secret_key is not set"

→ Ver SECRET_KEY nas Environment Variables

## 🎉 Pronto!

Seu app está rodando em produção 🚀

- Web: `https://seu-app.onrender.com`
- Mobile: `https://seu-app.onrender.com/mobile`
- API: `https://seu-app.onrender.com/api/...`

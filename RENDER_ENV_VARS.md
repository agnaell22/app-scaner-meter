# ✅ Checklist Variáveis de Ambiente - Render

## 🔍 Variáveis Obrigatórias

### 1. SUPABASE_URL

**O que é**: URL do seu projeto Supabase  
**Onde encontrar**: Supabase Dashboard → Settings → API → Project URL  
**Exemplo**: `https://abcdefgh1234.supabase.co`  
**Status**: ⚠️ OBRIGATÓRIA

```bash
# Testar no Render:
curl https://seu-app.onrender.com/
# Se der erro "SUPABASE_URL and SUPABASE_KEY not configured!", check isso
```

### 2. SUPABASE_KEY

**O que é**: Chave pública (anon) do Supabase  
**Onde encontrar**: Supabase Dashboard → Settings → API → anon public  
**Exemplo**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`  
**Status**: ⚠️ OBRIGATÓRIA

### 3. SECRET_KEY

**O que é**: Chave secreta para criptografia de sessão Flask  
**Como gerar**:

```bash
python -c "import os; print(os.urandom(24).hex())"
```

**Exemplo saída**: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`  
**Status**: ⚠️ OBRIGATÓRIA (gerar valor novo para produção)  
**Importante**: Use SEMPRE um valor aleatório diferente entre dev/prod!

---

## 🟢 Variáveis Opcionais

### 4. API_KEY

**O que é**: Chave para proteger endpoints `/api/*`  
**Padrão**: Vazio (nenhuma autenticação necessária)  
**Para ativar**:

```bash
# Gere uma chave aleatória:
python -c "import os; print(os.urandom(16).hex())"
# Coloque o valor em API_KEY
```

**Como usar**:

```bash
curl -H "X-API-KEY: seu-valor-aqui" https://seu-app.onrender.com/api/start
```

**Status**: ✅ OPCIONAL

### 5. SUPABASE_TABLE

**O que é**: Nome da tabela de leituras  
**Padrão**: `medicoes` (não mude a menos que necessary)  
**Status**: ✅ OPCIONAL (já definido em render.yaml)

### 6. FLASK_ENV

**O que é**: Ambiente Flask  
**Valores**: `production`, `development`  
**Padrão**: `production` (já definido em render.yaml)  
**Status**: ✅ OPCIONAL

### 7. FLASK_DEBUG

**O que é**: Modo debug (hot reload, stack traces)  
**Padrão**: `False` (já definido em render.yaml)  
**Importante**: NUNCA use `True` em produção!  
**Status**: ✅ OPCIONAL

### 8. PORT

**O que é**: Porta da aplicação  
**Padrão**: Render define automaticamente (lido de PORT env var)  
**Status**: ✅ OPCIONAL

---

## 🚀 Como Configurar no Render Dashboard

### Passo a Passo

1. **Acesse seu serviço** no Render  
   `https://dashboard.render.com`

2. **Clique em seu serviço** (ex: `app-scan-meter`)

3. **Vá para "Environment"**  
   Sidebar esquerdo → Environment Variables

4. **Adicione cada variável** clicando em "Add Environment Variable"

### Formato Correto

**NUNCA faça assim** ❌

```
SUPABASE_URL=https://...
SUPABASE_KEY=ey...
```

**SEMPRE assim** ✅

```
Key:   SUPABASE_URL
Value: https://...

Key:   SUPABASE_KEY
Value: ey...
```

### Exemplo Completo

```
FLASK_ENV            production
FLASK_DEBUG          False
SUPABASE_URL         https://abc123.supabase.co
SUPABASE_KEY         ey123abc456def...
SUPABASE_TABLE       medicoes
SECRET_KEY           a1b2c3d4e5f6...
API_KEY              (deixar vazio ou adicionar chave)
```

---

## ✅ Validação Pós-Deploy

### 1. Verificar Logs

```bash
Render Dashboard → Logs
# Procure por: "Set environment variables before running"
# Se NÃO aparecer, as variáveis estão OK ✅
# Se aparecer, duas variáveis faltam ❌
```

### 2. Testar Aplicação

```bash
curl https://seu-app.onrender.com/
# Deve retornar HTML (página inicial)
```

### 3. Testar API

```bash
curl -X POST https://seu-app.onrender.com/api/start \
  -H "Content-Type: application/json" \
  -d '{"equipe":"test","operador":"user1"}'
# Deve retornar JSON com collection_id
```

### 4. Verificar Banco

- Supabase Dashboard → SQL Editor
- Execute: `SELECT COUNT(*) FROM medicoes;`
- Deve retornar 0 (nenhuma leitura ainda)

---

## 🐛 Problemas Comuns

### ❌ "Erro: supabase module not found"

**Causa**: requirements.txt sem `supabase`  
**Solução**: Verificado ✅ (requirements.txt está correto)

### ❌ "Erro: SUPABASE_URL and SUPABASE_KEY not configured"

**Causa**: Variáveis não definidas ou vazias  
**Solução**:

1. Verificar se foram adicionadas no Render dashboard
2. Confirmar valores (não espaços extras!)
3. Faz novo deploy (botão "Manual Deploy")

### ❌ "Erro: relation 'colecoes' does not exist"

**Causa**: Tabelas não criadas no Supabase  
**Solução**:

1. Supabase Dashboard → SQL Editor
2. Colar todo o conteúdo de `supabase_table.sql`
3. Executar

### ❌ "Erro: 401 Unauthorized" na API

**Causa**: API_KEY ativada mas não enviada na requisição  
**Solução**:

- Se quer desativar: deixar API_KEY vazio
- Se quer manter: adicionar `-H "X-API-KEY: valor"` nas requisições

---

## 📋 Resumo Rápido

**3 variáveis essenciais**:

```
SUPABASE_URL  = https://seu-projeto.supabase.co
SUPABASE_KEY  = ey123...
SECRET_KEY    = a1b2c3...
```

**Depois do deploy**, verificar se:
✅ App carrega em `https://seu-app.onrender.com`  
✅ Log não mostra "not configured"  
✅ API responde a requisições  
✅ Dados aparecem no Supabase

🎉 Pronto!

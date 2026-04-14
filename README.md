# Coleta de Medidores

Aplicativo em Python para coletar dados de medidores de energia elétrica, registrar em planilha mestre e permitir coleta remota via celular.

## Funcionalidades

- Registro de data, equipe, medidor, tipo, status e observações
- Tipos de medidor: Monofásico, Bifásico, Trifásico
- Coleta pelo computador ou por celular via navegador
- Grava automaticamente em `master.xlsx`
- Grava também em `planilha_<equipe>.xlsx`
- Gera relatório de cada coleta em PDF ou texto
- Histórico de coletas e comprovante de entrega

## Instalação

1. Instale Python 3.10+.
2. No terminal, navegue até a pasta do app:
   ```powershell
   cd "c:\app nosvos"
   ```
3. Instale dependências:
   ```powershell
   python -m pip install -r requirements.txt
   ```

## Uso

### Modo web (recomendado)

1. Execute o servidor:
   ```powershell
   python server.py
   ```
2. No PC, abra `http://localhost:5000`.
3. No celular, abra `http://<IP_do_PC_na_mesa>:5000` na mesma rede Wi-Fi.
4. Ou abra `http://<IP_do_PC_na_mesa>:5000/mobile` para usar a interface mobile otimizada.
5. Inicie a coleta indicando `Equipe` e `Operador`.
6. Leia o código de barras do medidor ou digite manualmente.
7. Selecione `Tipo` e `Status`, e clique em `Registrar`.
8. Ao final, clique em `Encerrar coleta e gerar relatório`.
9. Use o botão de WhatsApp para compartilhar o link do relatório ou configure o SMTP em `Configurar email` para enviar o relatório por email.

### Deploy no Render

1. Crie um repositório Git com os arquivos do projeto.
2. Conecte o repositório ao Render.
3. O Render detectará o `render.yaml` e instalará as dependências de `requirements.txt`.
4. O comando de inicialização é:
   ```bash
   gunicorn server:app
   ```
5. O aplicativo ficará disponível em um domínio público do Render.

> Atenção: no Render o disco é efêmero. Os arquivos `master.xlsx`, `collections.json`, `reports/` e `planilha_<equipe>.xlsx` são gravados localmente no container e podem ser perdidos em novo deploy. Para produção, é recomendado migrar o armazenamento para um banco de dados ou serviço de arquivos na nuvem.

### Backend Supabase

Para gravar dados em um backend na nuvem usando Supabase, defina as variáveis de ambiente:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_TABLE` (opcional, padrão: `medicoes`)

No Render, defina estas variáveis no painel de configurações do serviço ou em `render.yaml`.

Use a seguinte tabela no Supabase (SQL):

```sql
create table medicoes (
  id uuid primary key default gen_random_uuid(),
  collection_id text not null,
  equipe text not null,
  operador text not null,
  medidor text not null,
  tipo text not null,
  status text not null,
  observacoes text,
  collection_start timestamp with time zone,
  recorded_at timestamp with time zone default now()
);
```

Você também pode usar o arquivo `supabase_table.sql` deste projeto para criar a tabela.

Quando o Supabase estiver configurado, cada entrada registrada no app também será enviada para o backend na nuvem.

### Modo API / servidor na nuvem

- A página `mobile` funciona como um app web simples.
- Para usar via 4G, hospede o servidor em um host público ou VPS e abra o URL do servidor no celular.
- Se você usar um serviço de nuvem, o celular acessa o servidor pelo endereço público em vez da rede local.
- É possível proteger o envio de dados com `API Key` no menu `Configurar email`.

### Configuração de email

1. Abra a página `Configurar email` no menu principal.
2. Preencha o servidor SMTP, porta, usuário, senha e o endereço de remetente.
3. Salve e use a opção de envio por email na página de relatório.

### Modo desktop (fallback)

1. Execute o app Tkinter:
   ```powershell
   python app.py
   ```
2. Informe a `Equipe`.
3. Leia o código de barras do medidor ou digite o número em `Medidor / Código de barras`.
4. Selecione `Tipo` e `Status`.
5. Clique em `Registrar entrada`.

## Arquivos gerados

- `master.xlsx` - planilha mestre com todos os registros
- `planilha_<equipe>.xlsx` - planilha própria de cada equipe
- `reports/relatorio_<id>.pdf` - relatório de cada coleta (ou `.txt` se não houver `reportlab`)

## Observações

- Para usar o celular como coletor, conecte o celular e o PC à mesma rede Wi-Fi e abra o endereço do servidor.
- Use um scanner que envie `Enter` após a leitura para acelerar o registro.
- Se `reportlab` não estiver instalado, o relatório será gerado em texto simples.
- Para compartilhar por WhatsApp, use o botão na página de relatório. O celular precisa conseguir acessar o servidor pelo IP do PC.
- Para envio por email, configure o servidor SMTP nas configurações e preencha o destinatário na página de relatório.

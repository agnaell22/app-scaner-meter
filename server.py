import json
import os
import uuid
import datetime
from io import BytesIO

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from supabase import create_client

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ==================== SUPABASE CONFIGURATION ====================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
SUPABASE_TABLE = os.environ.get("SUPABASE_TABLE", "medicoes").strip()
SUPABASE_CLIENT = None
if SUPABASE_URL and SUPABASE_KEY:
    SUPABASE_CLIENT = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== FLASK CONFIGURATION ====================
app = Flask(__name__)
# Secret key from environment variable (REQUIRED in production)
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    # Development fallback - generate random if not in development mode
    if os.environ.get("FLASK_ENV") == "development":
        SECRET_KEY = "dev-secret-key-change-in-production"
    else:
        SECRET_KEY = os.urandom(24).hex()
app.secret_key = SECRET_KEY

# ==================== API CONFIGURATION ====================
API_KEY = os.environ.get("API_KEY", "").strip()


# ==================== HELPER FUNCTIONS ====================

def is_supabase_enabled() -> bool:
    """Check if Supabase is properly configured."""
    return SUPABASE_CLIENT is not None


def load_collections() -> dict:
    """Load collections from Supabase. Returns dict of collections."""
    if not SUPABASE_CLIENT:
        return {}
    
    try:
        response = SUPABASE_CLIENT.table("colecoes").select("*").execute()
        collections = {}
        for row in response.data:
            collections[row["id"]] = {
                "id": row["id"],
                "equipe": row["equipe"],
                "operador": row["operador"],
                "start": row["start_time"],
                "updated": row["updated_time"],
                "end": row.get("end_time"),
                "status": row["status"],
                "items": json.loads(row["items"]) if row.get("items") else [],
            }
        return collections
    except Exception as e:
        print(f"Error loading collections from Supabase: {e}")
        return {}


def save_collection(collection: dict) -> None:
    """Save or update collection in Supabase."""
    if not SUPABASE_CLIENT:
        return
    
    try:
        # Check if collection already exists
        response = SUPABASE_CLIENT.table("colecoes").select("id").eq("id", collection["id"]).execute()
        
        payload = {
            "id": collection["id"],
            "equipe": collection["equipe"],
            "operador": collection["operador"],
            "start_time": collection["start"],
            "updated_time": collection.get("updated", collection["start"]),
            "end_time": collection.get("end"),
            "status": collection.get("status", "aberta"),
            "items": json.dumps(collection.get("items", [])),
        }
        
        if response.data:
            # Update existing collection
            SUPABASE_CLIENT.table("colecoes").update(payload).eq("id", collection["id"]).execute()
        else:
            # Insert new collection
            SUPABASE_CLIENT.table("colecoes").insert(payload).execute()
            
    except Exception as e:
        print(f"Error saving collection to Supabase: {e}")
        raise RuntimeError(f"Erro ao salvar coleta no Supabase: {e}")


def api_key_required() -> bool:
    """Check if request has valid API key."""
    if not API_KEY:
        return True  # No API key configured, allow all requests
    
    key = request.headers.get("X-API-KEY") or request.args.get("api_key", "")
    return key == API_KEY


def require_api_auth():
    """Check API key authorization. Returns error tuple if unauthorized."""
    if API_KEY and not api_key_required():
        return jsonify({"error": "API key required"}), 401
    return None


def get_collection_or_404(collection_id: str):
    """Get collection by ID or return 404 error."""
    collections = load_collections()
    collection = collections.get(collection_id)
    if not collection:
        return jsonify({"error": "Coleta não encontrada"}), 404
    return collection


def create_pdf_report(collection: dict) -> bytes:
    """Generate PDF report in memory. Returns PDF bytes."""
    buffer = BytesIO()
    
    if not REPORTLAB_AVAILABLE:
        # Fallback to text report
        text = "Relatório de Coleta de Medidores\n"
        text += f"Equipe: {collection['equipe']}\n"
        text += f"Operador: {collection['operador']}\n"
        text += f"Início: {collection['start']}\n"
        text += f"Término: {collection.get('end', 'em andamento')}\n"
        text += f"Total de registros: {len(collection['items'])}\n\n"
        for item in collection["items"]:
            text += f"{item['timestamp']} | {item['medidor']} | {item['tipo']} | {item['status']} | {item['observacoes']}\n"
        return text.encode("utf-8")
    
    # Generate PDF report
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Relatório de Coleta de Medidores")
    c.setFont("Helvetica", 11)
    y -= 30
    
    lines = [
        f"Equipe: {collection['equipe']}",
        f"Operador: {collection['operador']}",
        f"Início: {collection['start']}",
        f"Término: {collection.get('end', 'em andamento')}",
        f"Total de registros: {len(collection['items'])}",
        "",
    ]
    for line in lines:
        c.drawString(40, y, line)
        y -= 18

    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Data / Hora")
    c.drawString(160, y, "Medidor")
    c.drawString(300, y, "Tipo")
    c.drawString(380, y, "Status")
    c.drawString(460, y, "Observações")
    y -= 18
    c.setFont("Helvetica", 9)

    for item in collection["items"]:
        if y < 70:
            c.showPage()
            y = height - 40
            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, y, "Data / Hora")
            c.drawString(160, y, "Medidor")
            c.drawString(300, y, "Tipo")
            c.drawString(380, y, "Status")
            c.drawString(460, y, "Observações")
            y -= 18
            c.setFont("Helvetica", 9)

        c.drawString(40, y, item["timestamp"])
        c.drawString(160, y, item["medidor"][:16])
        c.drawString(300, y, item["tipo"])
        c.drawString(380, y, item["status"])
        c.drawString(460, y, item["observacoes"][:30])
        y -= 16

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def create_entry(collection: dict, medidor: str, tipo: str, status: str, observacoes: str) -> None:
    """Create entry in collection and save to Supabase."""
    now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    item = {
        "timestamp": now,
        "medidor": medidor,
        "tipo": tipo,
        "status": status,
        "observacoes": observacoes,
    }
    collection["items"].append(item)
    collection["updated"] = now

    # Save collection with new item to Supabase
    save_collection(collection)

    # Also save entry to medicoes table (readings log)
    if is_supabase_enabled():
        try:
            payload = {
                "collection_id": collection["id"],
                "equipe": collection["equipe"],
                "operador": collection["operador"],
                "medidor": medidor,
                "tipo": tipo,
                "status": status,
                "observacoes": observacoes,
                "collection_start": collection["start"],
                "recorded_at": now,
            }
            SUPABASE_CLIENT.table(SUPABASE_TABLE).insert(payload).execute()
        except Exception as e:
            print(f"Warning: Could not save entry to {SUPABASE_TABLE}: {e}")


# ==================== ROUTES ====================

@app.route("/")
def index():
    """Home page - list active collections."""
    collections = load_collections()
    active = [c for c in collections.values() if c.get("status") != "finalizada"]
    return render_template("index.html", active=active)


@app.route("/mobile")
def mobile():
    """Mobile interface."""
    return render_template("mobile.html")


@app.route("/start", methods=["POST"])
def start_collection():
    """Start a new collection."""
    equipe = request.form.get("equipe", "").strip()
    operador = request.form.get("operador", "").strip()
    if not equipe or not operador:
        flash("Informe equipe e operador para iniciar a coleta.", "warning")
        return redirect(url_for("index"))

    collection_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    collection = {
        "id": collection_id,
        "equipe": equipe,
        "operador": operador,
        "start": now,
        "updated": now,
        "items": [],
        "status": "aberta",
    }
    
    try:
        save_collection(collection)
        flash("Coleta iniciada. Escaneie medidores pelo celular ou pelo PC.", "success")
    except Exception as e:
        flash(f"Erro ao iniciar coleta: {e}", "danger")
        return redirect(url_for("index"))
    
    return redirect(url_for("collect", collection_id=collection_id))


@app.route("/collect/<collection_id>", methods=["GET", "POST"])
def collect(collection_id):
    """Collect meter readings."""
    collections = load_collections()
    collection = collections.get(collection_id)
    if not collection:
        flash("Coleta não encontrada.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        medidor = request.form.get("medidor", "").strip()
        tipo = request.form.get("tipo", "").strip()
        status = request.form.get("status", "").strip()
        observacoes = request.form.get("observacoes", "").strip()
        if not medidor or not tipo or not status:
            flash("Preencha medidor, tipo e status antes de enviar.", "warning")
            return redirect(url_for("collect", collection_id=collection_id))

        try:
            create_entry(collection, medidor, tipo, status, observacoes)
            flash("Registro salvo em tempo real.", "success")
        except Exception as exc:
            flash(f"Erro ao salvar o registro: {exc}", "danger")
        return redirect(url_for("collect", collection_id=collection_id))

    last_items = list(reversed(collection["items"]))[:10]
    return render_template(
        "collector.html",
        collection=collection,
        last_items=last_items,
        reportlab_available=REPORTLAB_AVAILABLE,
    )


@app.route("/finalize/<collection_id>", methods=["POST"])
def finalize(collection_id):
    """Finalize collection and generate report."""
    collections = load_collections()
    collection = collections.get(collection_id)
    if not collection:
        flash("Coleta não encontrada.", "danger")
        return redirect(url_for("index"))
    
    if collection.get("status") == "finalizada":
        flash("Coleta já foi finalizada.", "info")
        return redirect(url_for("report", collection_id=collection_id))

    collection["end"] = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    collection["status"] = "finalizada"
    
    try:
        save_collection(collection)
        flash("Coleta finalizada. Relatório gerado.", "success")
    except Exception as e:
        flash(f"Erro ao finalizar coleta: {e}", "danger")
    
    return redirect(url_for("report", collection_id=collection_id))


@app.route("/report/<collection_id>")
def report(collection_id):
    """View and download report."""
    collections = load_collections()
    collection = collections.get(collection_id)
    if not collection:
        flash("Coleta não encontrada.", "danger")
        return redirect(url_for("index"))

    # Generate share URL for PDF download
    share_url = request.host_url.rstrip("/") + url_for("download_report", collection_id=collection_id)
    
    return render_template(
        "report.html",
        collection=collection,
        reportlab_available=REPORTLAB_AVAILABLE,
        share_url=share_url,
    )


@app.route("/download/<collection_id>")
def download_report(collection_id):
    """Download PDF report."""
    collections = load_collections()
    collection = collections.get(collection_id)
    if not collection:
        flash("Coleta não encontrada.", "danger")
        return redirect(url_for("index"))
    
    try:
        pdf_bytes = create_pdf_report(collection)
        filename = f"relatorio_{collection['equipe'].replace(' ', '_')}_{collection['id'][:8]}.pdf"
        return send_file(
            BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f"Erro ao gerar relatório: {e}", "danger")
        return redirect(url_for("index"))


@app.route("/history")
def history():
    """View collection history."""
    collections = load_collections()
    ordered = sorted(collections.values(), key=lambda c: c["start"], reverse=True)
    return render_template("history.html", collections=ordered)


# ==================== API ROUTES ====================

@app.route("/api/start", methods=["POST"])
def api_start():
    """API: Start a new collection."""
    auth = require_api_auth()
    if auth:
        return auth

    data = request.get_json(silent=True) or {}
    equipe = data.get("equipe", "").strip()
    operador = data.get("operador", "").strip()
    if not equipe or not operador:
        return jsonify({"error": "Informe equipe e operador."}), 400

    collection_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    collection = {
        "id": collection_id,
        "equipe": equipe,
        "operador": operador,
        "start": now,
        "updated": now,
        "items": [],
        "status": "aberta",
    }
    
    try:
        save_collection(collection)
        return jsonify({"collection_id": collection_id, "start": now}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/collect/<collection_id>", methods=["POST"])
def api_collect(collection_id):
    """API: Add reading to collection."""
    auth = require_api_auth()
    if auth:
        return auth

    collection = get_collection_or_404(collection_id)
    if isinstance(collection, tuple):
        return collection

    data = request.get_json(silent=True) or {}
    medidor = data.get("medidor", "").strip()
    tipo = data.get("tipo", "").strip()
    status = data.get("status", "").strip()
    observacoes = data.get("observacoes", "").strip()
    
    if not medidor or not tipo or not status:
        return jsonify({"error": "Preencha medidor, tipo e status."}), 400

    try:
        create_entry(collection, medidor, tipo, status, observacoes)
        return jsonify({"message": "Registro salvo."}), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/finalize/<collection_id>", methods=["POST"])
def api_finalize(collection_id):
    """API: Finalize collection."""
    auth = require_api_auth()
    if auth:
        return auth

    collection = get_collection_or_404(collection_id)
    if isinstance(collection, tuple):
        return collection

    if collection.get("status") == "finalizada":
        return jsonify({"message": "Coleta já finalizada."}), 200

    collection["end"] = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    collection["status"] = "finalizada"
    
    try:
        save_collection(collection)
        return jsonify({"message": "Coleta finalizada.", "collection_id": collection["id"]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/report/<collection_id>")
def api_get_report(collection_id):
    """API: Get report URL."""
    collections = load_collections()
    collection = collections.get(collection_id)
    if not collection:
        return jsonify({"error": "Coleta não encontrada"}), 404
    
    share_url = request.host_url.rstrip("/") + url_for("download_report", collection_id=collection_id)
    return jsonify({
        "collection_id": collection_id,
        "status": collection.get("status"),
        "report_url": share_url
    }), 200


# ==================== MAIN ====================

if __name__ == "__main__":
    if not SUPABASE_CLIENT:
        print("⚠️  SUPABASE_URL and SUPABASE_KEY not configured!")
        print("Set environment variables before running in production.")
    
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)
import json
import os
import uuid
import datetime
from io import BytesIO

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from supabase import create_client

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ==================== SUPABASE CONFIGURATION ====================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
SUPABASE_TABLE = os.environ.get("SUPABASE_TABLE", "medicoes").strip()
SUPABASE_CLIENT = None
if SUPABASE_URL and SUPABASE_KEY:
    SUPABASE_CLIENT = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== FLASK CONFIGURATION ====================
app = Flask(__name__)
# Secret key from environment variable (REQUIRED in production)
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    # Development fallback - generate random if not in development mode
    if os.environ.get("FLASK_ENV") == "development":
        SECRET_KEY = "dev-secret-key-change-in-production"
    else:
        SECRET_KEY = os.urandom(24).hex()
app.secret_key = SECRET_KEY

# ==================== API CONFIGURATION ====================
API_KEY = os.environ.get("API_KEY", "").strip()


# ==================== HELPER FUNCTIONS ====================

def is_supabase_enabled() -> bool:
    """Check if Supabase is properly configured."""
    return SUPABASE_CLIENT is not None


def load_collections() -> dict:
    """Load collections from Supabase. Returns dict of collections."""
    if not SUPABASE_CLIENT:
        return {}
    
    try:
        response = SUPABASE_CLIENT.table("colecoes").select("*").execute()
        collections = {}
        for row in response.data:
            collections[row["id"]] = {
                "id": row["id"],
                "equipe": row["equipe"],
                "operador": row["operador"],
                "start": row["start_time"],
                "updated": row["updated_time"],
                "end": row.get("end_time"),
                "status": row["status"],
                "items": json.loads(row["items"]) if row.get("items") else [],
            }
        return collections
    except Exception as e:
        print(f"Error loading collections from Supabase: {e}")
        return {}


def save_collection(collection: dict) -> None:
    """Save or update collection in Supabase."""
    if not SUPABASE_CLIENT:
        return
    
    try:
        # Check if collection already exists
        response = SUPABASE_CLIENT.table("colecoes").select("id").eq("id", collection["id"]).execute()
        
        payload = {
            "id": collection["id"],
            "equipe": collection["equipe"],
            "operador": collection["operador"],
            "start_time": collection["start"],
            "updated_time": collection.get("updated", collection["start"]),
            "end_time": collection.get("end"),
            "status": collection.get("status", "aberta"),
            "items": json.dumps(collection.get("items", [])),
        }
        
        if response.data:
            # Update existing collection
            SUPABASE_CLIENT.table("colecoes").update(payload).eq("id", collection["id"]).execute()
        else:
            # Insert new collection
            SUPABASE_CLIENT.table("colecoes").insert(payload).execute()
            
    except Exception as e:
        print(f"Error saving collection to Supabase: {e}")
        raise RuntimeError(f"Erro ao salvar coleta no Supabase: {e}")


def api_key_required() -> bool:
    """Check if request has valid API key."""
    if not API_KEY:
        return True  # No API key configured, allow all requests
    
    key = request.headers.get("X-API-KEY") or request.args.get("api_key", "")
    return key == API_KEY


def require_api_auth():
    """Check API key authorization. Returns error tuple if unauthorized."""
    if API_KEY and not api_key_required():
        return jsonify({"error": "API key required"}), 401
    return None


def get_collection_or_404(collection_id: str):
    """Get collection by ID or return 404 error."""
    collections = load_collections()
    collection = collections.get(collection_id)
    if not collection:
        return jsonify({"error": "Coleta não encontrada"}), 404
    return collection


def create_pdf_report(collection: dict) -> bytes:
    """Generate PDF report in memory. Returns PDF bytes."""
    buffer = BytesIO()
    
    if not REPORTLAB_AVAILABLE:
        # Fallback to text report
        text = "Relatório de Coleta de Medidores\n"
        text += f"Equipe: {collection['equipe']}\n"
        text += f"Operador: {collection['operador']}\n"
        text += f"Início: {collection['start']}\n"
        text += f"Término: {collection.get('end', 'em andamento')}\n"
        text += f"Total de registros: {len(collection['items'])}\n\n"
        for item in collection["items"]:
            text += f"{item['timestamp']} | {item['medidor']} | {item['tipo']} | {item['status']} | {item['observacoes']}\n"
        return text.encode("utf-8")
    
    # Generate PDF report
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Relatório de Coleta de Medidores")
    c.setFont("Helvetica", 11)
    y -= 30
    
    lines = [
        f"Equipe: {collection['equipe']}",
        f"Operador: {collection['operador']}",
        f"Início: {collection['start']}",
        f"Término: {collection.get('end', 'em andamento')}",
        f"Total de registros: {len(collection['items'])}",
        "",
    ]
    for line in lines:
        c.drawString(40, y, line)
        y -= 18

    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Data / Hora")
    c.drawString(160, y, "Medidor")
    c.drawString(300, y, "Tipo")
    c.drawString(380, y, "Status")
    c.drawString(460, y, "Observações")
    y -= 18
    c.setFont("Helvetica", 9)

    for item in collection["items"]:
        if y < 70:
            c.showPage()
            y = height - 40
            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, y, "Data / Hora")
            c.drawString(160, y, "Medidor")
            c.drawString(300, y, "Tipo")
            c.drawString(380, y, "Status")
            c.drawString(460, y, "Observações")
            y -= 18
            c.setFont("Helvetica", 9)

        c.drawString(40, y, item["timestamp"])
        c.drawString(160, y, item["medidor"][:16])
        c.drawString(300, y, item["tipo"])
        c.drawString(380, y, item["status"])
        c.drawString(460, y, item["observacoes"][:30])
        y -= 16

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def create_entry(collection: dict, medidor: str, tipo: str, status: str, observacoes: str) -> None:
    """Create entry in collection and save to Supabase."""
    now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    item = {
        "timestamp": now,
        "medidor": medidor,
        "tipo": tipo,
        "status": status,
        "observacoes": observacoes,
    }
    collection["items"].append(item)
    collection["updated"] = now

    # Save collection with new item to Supabase
    save_collection(collection)

    # Also save entry to medicoes table (readings log)
    if is_supabase_enabled():
        try:
            payload = {
                "collection_id": collection["id"],
                "equipe": collection["equipe"],
                "operador": collection["operador"],
                "medidor": medidor,
                "tipo": tipo,
                "status": status,
                "observacoes": observacoes,
                "collection_start": collection["start"],
                "recorded_at": now,
            }
            SUPABASE_CLIENT.table(SUPABASE_TABLE).insert(payload).execute()
        except Exception as e:
            print(f"Warning: Could not save entry to {SUPABASE_TABLE}: {e}")


# ==================== ROUTES ====================

@app.route("/")
def index():
    """Home page - list active collections."""
    collections = load_collections()
    active = [c for c in collections.values() if c.get("status") != "finalizada"]
    return render_template("index.html", active=active)


@app.route("/mobile")
def mobile():
    """Mobile interface."""
    return render_template("mobile.html")


@app.route("/start", methods=["POST"])
def start_collection():
    """Start a new collection."""
    equipe = request.form.get("equipe", "").strip()
    operador = request.form.get("operador", "").strip()
    if not equipe or not operador:
        flash("Informe equipe e operador para iniciar a coleta.", "warning")
        return redirect(url_for("index"))

    collection_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    collection = {
        "id": collection_id,
        "equipe": equipe,
        "operador": operador,
        "start": now,
        "updated": now,
        "items": [],
        "status": "aberta",
    }
    
    try:
        save_collection(collection)
        flash("Coleta iniciada. Escaneie medidores pelo celular ou pelo PC.", "success")
    except Exception as e:
        flash(f"Erro ao iniciar coleta: {e}", "danger")
        return redirect(url_for("index"))
    
    return redirect(url_for("collect", collection_id=collection_id))


@app.route("/collect/<collection_id>", methods=["GET", "POST"])
def collect(collection_id):
    """Collect meter readings."""
    collections = load_collections()
    collection = collections.get(collection_id)
    if not collection:
        flash("Coleta não encontrada.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        medidor = request.form.get("medidor", "").strip()
        tipo = request.form.get("tipo", "").strip()
        status = request.form.get("status", "").strip()
        observacoes = request.form.get("observacoes", "").strip()
        if not medidor or not tipo or not status:
            flash("Preencha medidor, tipo e status antes de enviar.", "warning")
            return redirect(url_for("collect", collection_id=collection_id))

        try:
            create_entry(collection, medidor, tipo, status, observacoes)
            flash("Registro salvo em tempo real.", "success")
        except Exception as exc:
            flash(f"Erro ao salvar o registro: {exc}", "danger")
        return redirect(url_for("collect", collection_id=collection_id))

    last_items = list(reversed(collection["items"]))[:10]
    return render_template(
        "collector.html",
        collection=collection,
        last_items=last_items,
        reportlab_available=REPORTLAB_AVAILABLE,
    )


@app.route("/finalize/<collection_id>", methods=["POST"])
def finalize(collection_id):
    """Finalize collection and generate report."""
    collections = load_collections()
    collection = collections.get(collection_id)
    if not collection:
        flash("Coleta não encontrada.", "danger")
        return redirect(url_for("index"))
    
    if collection.get("status") == "finalizada":
        flash("Coleta já foi finalizada.", "info")
        return redirect(url_for("report", collection_id=collection_id))

    collection["end"] = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    collection["status"] = "finalizada"
    
    try:
        save_collection(collection)
        flash("Coleta finalizada. Relatório gerado.", "success")
    except Exception as e:
        flash(f"Erro ao finalizar coleta: {e}", "danger")
    
    return redirect(url_for("report", collection_id=collection_id))


@app.route("/report/<collection_id>")
def report(collection_id):
    """View and download report."""
    collections = load_collections()
    collection = collections.get(collection_id)
    if not collection:
        flash("Coleta não encontrada.", "danger")
        return redirect(url_for("index"))

    # Generate share URL for PDF download
    share_url = request.host_url.rstrip("/") + url_for("download_report", collection_id=collection_id)
    
    return render_template(
        "report.html",
        collection=collection,
        reportlab_available=REPORTLAB_AVAILABLE,
        share_url=share_url,
    )


@app.route("/download/<collection_id>")
def download_report(collection_id):
    """Download PDF report."""
    collections = load_collections()
    collection = collections.get(collection_id)
    if not collection:
        flash("Coleta não encontrada.", "danger")
        return redirect(url_for("index"))
    
    try:
        pdf_bytes = create_pdf_report(collection)
        filename = f"relatorio_{collection['equipe'].replace(' ', '_')}_{collection['id'][:8]}.pdf"
        return send_file(
            BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f"Erro ao gerar relatório: {e}", "danger")
        return redirect(url_for("index"))


@app.route("/history")
def history():
    """View collection history."""
    collections = load_collections()
    ordered = sorted(collections.values(), key=lambda c: c["start"], reverse=True)
    return render_template("history.html", collections=ordered)


# ==================== API ROUTES ====================

@app.route("/api/start", methods=["POST"])
def api_start():
    """API: Start a new collection."""
    auth = require_api_auth()
    if auth:
        return auth

    data = request.get_json(silent=True) or {}
    equipe = data.get("equipe", "").strip()
    operador = data.get("operador", "").strip()
    if not equipe or not operador:
        return jsonify({"error": "Informe equipe e operador."}), 400

    collection_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    collection = {
        "id": collection_id,
        "equipe": equipe,
        "operador": operador,
        "start": now,
        "updated": now,
        "items": [],
        "status": "aberta",
    }
    
    try:
        save_collection(collection)
        return jsonify({"collection_id": collection_id, "start": now}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/collect/<collection_id>", methods=["POST"])
def api_collect(collection_id):
    """API: Add reading to collection."""
    auth = require_api_auth()
    if auth:
        return auth

    collection = get_collection_or_404(collection_id)
    if isinstance(collection, tuple):
        return collection

    data = request.get_json(silent=True) or {}
    medidor = data.get("medidor", "").strip()
    tipo = data.get("tipo", "").strip()
    status = data.get("status", "").strip()
    observacoes = data.get("observacoes", "").strip()
    
    if not medidor or not tipo or not status:
        return jsonify({"error": "Preencha medidor, tipo e status."}), 400

    try:
        create_entry(collection, medidor, tipo, status, observacoes)
        return jsonify({"message": "Registro salvo."}), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/finalize/<collection_id>", methods=["POST"])
def api_finalize(collection_id):
    """API: Finalize collection."""
    auth = require_api_auth()
    if auth:
        return auth

    collection = get_collection_or_404(collection_id)
    if isinstance(collection, tuple):
        return collection

    if collection.get("status") == "finalizada":
        return jsonify({"message": "Coleta já finalizada."}), 200

    collection["end"] = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    collection["status"] = "finalizada"
    
    try:
        save_collection(collection)
        return jsonify({"message": "Coleta finalizada.", "collection_id": collection["id"]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/report/<collection_id>")
def api_get_report(collection_id):
    """API: Get report URL."""
    collections = load_collections()
    collection = collections.get(collection_id)
    if not collection:
        return jsonify({"error": "Coleta não encontrada"}), 404
    
    share_url = request.host_url.rstrip("/") + url_for("download_report", collection_id=collection_id)
    return jsonify({
        "collection_id": collection_id,
        "status": collection.get("status"),
        "report_url": share_url
    }), 200


# ==================== MAIN ====================

if __name__ == "__main__":
    if not SUPABASE_CLIENT:
        print("⚠️  SUPABASE_URL and SUPABASE_KEY not configured!")
        print("Set environment variables before running in production.")
    
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)

import os, json, smtplib, datetime as dt
from flask import Flask, render_template, request, redirect, url_for, flash, abort, Response
import requests
from pdf import render_invoice_pdf
from weather import weather_widget

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET", "dev")

DB = {"clients": {}, "invoices": {}}
_seq = {"client": 0, "invoice": 0}


def _next(kind):
    _seq[kind] += 1
    return _seq[kind]


NAV = [
    ("dashboard", "Dashboard"), ("invoices", "Invoices"), ("clients", "Clients"),
    ("reports", "Reports"), ("templates", "Templates"), ("taxes", "Taxes"),
    ("integrations", "Integrations"), ("audit", "Audit log"), ("settings", "Settings"),
]


@app.context_processor
def inject_nav():
    return {"nav": NAV}


@app.route("/")
def dashboard():
    month = dt.date.today().strftime("%Y-%m")
    invoices = [i for i in DB["invoices"].values() if i["issued"].startswith(month)]
    # monthly income = everything that has left the drafts
    income = sum(i["total"] for i in invoices if i["status"] == "sent")
    return render_template(
        "dashboard.html",
        invoices=invoices,
        income=income,
        weather=weather_widget(request.remote_addr),
    )


@app.route("/invoices")
def invoices():
    return render_template("invoices.html", invoices=list(DB["invoices"].values()))


@app.route("/invoices/new", methods=["GET", "POST"])
def invoice_new():
    if request.method == "POST":
        client = DB["clients"].get(int(request.form.get("client_id") or 0))
        if not client:
            flash("Pick a client first.", "error")
            return render_template("invoice_form.html", clients=DB["clients"].values())
        try:
            total = float(request.form["total"])
        except (KeyError, ValueError):
            flash("Total must be a number.", "error")
            return render_template("invoice_form.html", clients=DB["clients"].values())
        iid = _next("invoice")
        DB["invoices"][iid] = {
            "id": iid, "client": client, "total": total, "status": "draft",
            "issued": dt.date.today().isoformat(), "paid_at": None,
        }
        return redirect(url_for("invoices"))
    return render_template("invoice_form.html", clients=DB["clients"].values())


@app.route("/invoices/<int:iid>/send", methods=["POST"])
def invoice_send(iid):
    inv = DB["invoices"].get(iid) or abort(404)
    url = os.environ.get("SMTP_URL")
    if not url:
        raise RuntimeError("SMTP_URL not configured")
    with smtplib.SMTP(url) as s:
        s.sendmail("billing@ledgerly.app", inv["client"]["email"], f"Invoice #{iid}: {inv['total']}")
    inv["status"] = "sent"
    return redirect(url_for("invoices"))


@app.route("/invoices/<int:iid>/paid", methods=["POST"])
def invoice_paid(iid):
    inv = DB["invoices"].get(iid) or abort(404)
    inv["status"] = "paid"
    inv["paid_at"] = dt.date.today().isoformat()
    flash(f"Invoice #{iid} marked as paid.", "ok")
    return redirect(url_for("invoices"))


@app.route("/invoices/<int:iid>/pdf")
def invoice_pdf(iid):
    inv = DB["invoices"].get(iid) or abort(404)
    return Response(render_invoice_pdf(inv), mimetype="application/pdf")


@app.route("/clients", methods=["GET", "POST"])
def clients():
    if request.method == "POST":
        name, email = request.form.get("name", "").strip(), request.form.get("email", "").strip()
        if not name or "@" not in email:
            flash("Name and a valid email are required.", "error")
        else:
            cid = _next("client")
            DB["clients"][cid] = {"id": cid, "name": name, "email": email}
            flash(f"Client {name} added.", "ok")
        return redirect(url_for("clients"))
    return render_template("clients.html", clients=DB["clients"].values())


for _page in ("reports", "templates", "taxes", "integrations", "audit", "settings"):
    app.add_url_rule(f"/{_page}", _page, (lambda p: lambda: render_template("stub.html", page=p))(_page))


@app.errorhandler(500)
def internal(e):
    return Response(json.dumps({"error": str(e.original_exception if hasattr(e, "original_exception") else e)}),
                    status=500, mimetype="application/json")

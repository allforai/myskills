# Ledgerly

Invoicing for freelancers. Create clients, write invoices, send them by email, mark them paid, export PDF.

## Run

    pip install -r requirements.txt
    flask --app app run

Set `SMTP_URL` for sending. Without it, `send` fails with a 500.

After cloning the repo

Install Requirements
```bash
pip install flask flask_sqlalchemy
```
```bash
python app.py
```
This will start the server at:
http://127.0.0.1:5000/

📡 Available Endpoints
1) GET /
Returns a health check message.
2) Create a Loan
POST /lend
Request JSON:
{
  "customer_id": 1,
  "principal": 50000,
  "interest_rate": 10,
  "period_years": 2
}
3) Make a Payment
POST /payment
Request JSON:
{
  "loan_id": 3,
  "amount": 2500,
  "payment_type": "emi"
}
4) Get Loan Ledger
GET /ledger/<loan_id>
Shows all payments, balance, EMIs left.
5) Get Account Overview
GET /account_overview/<customer_id>
Lists all loans, balances, EMIs left, total paid etc.

The custommer creating and listing endpoints have been commented out. Please uncomment them to create cutomers and test the apis

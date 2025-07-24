from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    loans = db.relationship('Loan', backref='customer', lazy=True)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    principal = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    period_years = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    emi_amount = db.Column(db.Float, nullable=False)
    total_interest = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    payments = db.relationship('Payment', backref='loan', lazy=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Bank System API is running."

# @app.route('/customer', methods=['POST'])
# def create_customer():
#     data = request.get_json()
#     name = data.get('name')
#     if not name:
#         return jsonify({'error': 'Name is required.'}), 400
#     customer = Customer(name=name)
#     db.session.add(customer)
#     db.session.commit()
#     return jsonify({'id': customer.id, 'name': customer.name}), 201

# @app.route('/customers', methods=['GET'])
# def list_customers():
#     customers = Customer.query.all()
#     result = [{'id': c.id, 'name': c.name} for c in customers]
#     return jsonify(result), 200

@app.route('/lend', methods=['POST'])
def lend():
    data = request.get_json()
    customer_id = data.get('customer_id')
    principal = data.get('principal')
    period_years = data.get('period_years')
    interest_rate = data.get('interest_rate')

    if not all([customer_id, principal, period_years, interest_rate]):
        return jsonify({'error': 'Missing required fields.'}), 400

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found.'}), 404

    total_interest = principal * period_years * interest_rate / 100
    total_amount = principal + total_interest
    emi_amount = round(total_amount / (period_years * 12), 2)

    loan = Loan(
        customer_id=customer_id,
        principal=principal,
        interest_rate=interest_rate,
        period_years=period_years,
        total_amount=total_amount,
        emi_amount=emi_amount,
        total_interest=total_interest
    )
    db.session.add(loan)
    db.session.commit()

    return jsonify({
        'loan_id': loan.id,
        'total_amount': round(total_amount, 2),
        'emi_amount': emi_amount
    }), 201

@app.route('/payment', methods=['POST'])
def payment():
    data = request.get_json()
    loan_id = data.get('loan_id')
    amount = data.get('amount')
    payment_type = data.get('payment_type') 

    if not all([loan_id, amount, payment_type]):
        return jsonify({'error': 'Missing required fields.'}), 400

    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({'error': 'Loan not found.'}), 404
    if loan.status != 'active':
        return jsonify({'error': 'Loan is not active.'}), 400

    payment = Payment(
        loan_id=loan_id,
        amount=amount,
        payment_type=payment_type
    )
    db.session.add(payment)

    total_paid = sum(p.amount for p in loan.payments) + amount
    balance = loan.total_amount - total_paid
    balance = round(balance, 2)
    emi_amount = loan.emi_amount

    if emi_amount > 0:
        emis_left = max(0, int(balance // emi_amount + (1 if balance % emi_amount > 0 else 0)))
    else:
        emis_left = 0

    if balance <= 0:
        loan.status = 'closed'
        balance = 0
        emis_left = 0

    db.session.commit()

    return jsonify({
        'loan_id': loan.id,
        'updated_balance': balance,
        'emi_amount': emi_amount,
        'emis_left': emis_left
    }), 200

@app.route('/ledger/<int:loan_id>', methods=['GET'])
def ledger(loan_id):
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({'error': 'Loan not found.'}), 404

    transactions = [
        {
            'payment_id': p.id,
            'amount': p.amount,
            'payment_type': p.payment_type,
            'payment_date': p.payment_date.strftime('%Y-%m-%d %H:%M:%S')
        }
        for p in loan.payments
    ]

    total_paid = sum(p.amount for p in loan.payments)
    balance = round(loan.total_amount - total_paid, 2)
    emi_amount = loan.emi_amount

    if emi_amount > 0:
        emis_left = max(0, int(balance // emi_amount + (1 if balance % emi_amount > 0 else 0)))
    else:
        emis_left = 0

    return jsonify({
        'loan_id': loan.id,
        'transactions': transactions,
        'balance': balance,
        'emi_amount': emi_amount,
        'emis_left': emis_left
    }), 200

@app.route('/account_overview/<int:customer_id>', methods=['GET'])
def account_overview(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found.'}), 404

    loans_info = []
    for loan in customer.loans:
        total_paid = sum(p.amount for p in loan.payments)
        balance = round(loan.total_amount - total_paid, 2)
        emi_amount = loan.emi_amount
        if emi_amount > 0:
            emis_left = max(0, int(balance // emi_amount + (1 if balance % emi_amount > 0 else 0)))
        else:
            emis_left = 0
        loans_info.append({
            'loan_id': loan.id,
            'principal': loan.principal,
            'total_amount': loan.total_amount,
            'emi_amount': emi_amount,
            'total_interest': loan.total_interest,
            'amount_paid': round(total_paid, 2),
            'emis_left': emis_left,
            'status': loan.status
        })

    return jsonify({
        'customer_id': customer.id,
        'loans': loans_info
    }), 200

if __name__ == '__main__':
    app.run(debug=True) 
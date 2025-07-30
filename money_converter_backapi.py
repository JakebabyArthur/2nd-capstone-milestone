from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:010911@localhost:5432/testdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'

    # id is now a VARCHAR(20) primary key, not Integer
    id            = db.Column(db.String(20), primary_key=True)
    date          = db.Column(db.Date,   nullable=False)
    from_currency = db.Column(db.String(3), nullable=False)
    to_currency   = db.Column(db.String(3), nullable=False)
    rate          = db.Column(db.Float, nullable=False)

    __table_args__ = (
        # ensure one rate per day per currency pair
        db.UniqueConstraint('from_currency','to_currency','date',
                            name='uq_currency_pair_date'),
    )

with app.app_context():
    db.create_all()


def make_id(src: str, tgt: str, dt: datetime.date) -> str:
    # USD + EUR + 20250729  →  USDEUR20250729
    return f"{src.upper()}{tgt.upper()}{dt.strftime('%Y%m%d')}"


@app.route('/rates', methods=['GET'])
def get_rates():
    rates = ExchangeRate.query.order_by(ExchangeRate.date, ExchangeRate.to_currency).all()
    return jsonify([
        {
            'id': r.id,
            'date': r.date.isoformat(),
            'from': r.from_currency,
            'to': r.to_currency,
            'rate': r.rate
        }
        for r in rates
    ])

@app.route('/rates/<string:rate_id>', methods=['GET'])
def get_rate(rate_id):
    r = ExchangeRate.query.get(rate_id)
    if not r:
        return jsonify({'message': 'Rate not found'}), 404
    return jsonify({
        'id': r.id,
        'date': r.date.isoformat(),
        'from': r.from_currency,
        'to': r.to_currency,
        'rate': r.rate
    })

@app.route('/rates', methods=['POST'])
def create_rate():
    data = request.get_json() or {}
    for key in ('from','to','date','rate'):
        if key not in data:
            return jsonify({'message': f"Missing '{key}' field"}), 400

    # parse & validate
    try:
        dt = datetime.strptime(data['date'], '%Y-%m-%d').date()
        rate_val = float(data['rate'])
        src = data['from'].upper()
        tgt = data['to'].upper()
    except Exception as e:
        return jsonify({'message': 'Invalid payload', 'error': str(e)}), 400

    new_id = make_id(src, tgt, dt)
    r = ExchangeRate(
        id=new_id,
        date=dt,
        from_currency=src,
        to_currency=tgt,
        rate=rate_val
    )

    db.session.add(r)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Could not create rate', 'error': str(e)}), 400

    return jsonify({
        'id': r.id,
        'date': r.date.isoformat(),
        'from': r.from_currency,
        'to': r.to_currency,
        'rate': r.rate
    }), 201

@app.route('/rates/<string:rate_id>', methods=['PUT'])
def update_rate(rate_id):
    r = ExchangeRate.query.get(rate_id)
    if not r:
        return jsonify({'message': 'Rate not found'}), 404

    data = request.get_json() or {}
    changed = False

    # Update date, from or to → need to recalc PK
    try:
        if 'date' in data:
            new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            r.date = new_date
            changed = True

        if 'from' in data:
            r.from_currency = data['from'].upper()
            changed = True

        if 'to' in data:
            r.to_currency = data['to'].upper()
            changed = True

        if 'rate' in data:
            r.rate = float(data['rate'])

        # If any of the key pieces changed, regenerate the id
        if changed:
            new_id = make_id(r.from_currency, r.to_currency, r.date)
            r.id = new_id

        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'message': 'Invalid data format', 'error': str(e)}), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'message': 'Could not update rate', 'error': str(e.orig)}), 400

    return jsonify({
        'id': r.id,
        'date': r.date.isoformat(),
        'from': r.from_currency,
        'to': r.to_currency,
        'rate': r.rate
    })


@app.route('/rates/<string:rate_id>', methods=['DELETE'])
def delete_rate(rate_id):
    r = ExchangeRate.query.get(rate_id)
    if not r:
        return jsonify({'message': 'Rate not found'}), 404

    db.session.delete(r)
    db.session.commit()
    return '', 204


if __name__ == '__main__':
    app.run(debug=True)

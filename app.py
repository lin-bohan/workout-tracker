import sqlite3
from flask import Flask, request, jsonify, render_template, g

app = Flask(__name__)
DB_PATH = 'workouts.db'


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                date   TEXT    NOT NULL,
                name   TEXT    NOT NULL,
                weight TEXT    NOT NULL DEFAULT '',
                reps   TEXT    NOT NULL
            )
        ''')
        db.commit()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/day/<date>')
def get_day(date):
    rows = get_db().execute(
        'SELECT id, name, weight, reps FROM exercises WHERE date = ? ORDER BY id',
        (date,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/week-dots')
def week_dots():
    start = request.args['start']
    end   = request.args['end']
    rows  = get_db().execute(
        'SELECT DISTINCT date FROM exercises WHERE date >= ? AND date <= ?',
        (start, end)
    ).fetchall()
    return jsonify([r['date'] for r in rows])


@app.route('/api/exercises', methods=['POST'])
def add_exercise():
    data = request.get_json()
    db   = get_db()
    cur  = db.execute(
        'INSERT INTO exercises (date, name, weight, reps) VALUES (?, ?, ?, ?)',
        (data['date'], data['name'], data.get('weight', ''), data['reps'])
    )
    db.commit()
    row = db.execute(
        'SELECT id, name, weight, reps FROM exercises WHERE id = ?', (cur.lastrowid,)
    ).fetchone()
    return jsonify(dict(row)), 201


@app.route('/api/exercises/<int:exercise_id>', methods=['PUT'])
def update_exercise(exercise_id):
    data = request.get_json()
    db   = get_db()
    db.execute(
        'UPDATE exercises SET name = ?, weight = ?, reps = ? WHERE id = ?',
        (data['name'], data.get('weight', ''), data['reps'], exercise_id)
    )
    db.commit()
    return '', 204


@app.route('/api/exercises/<int:exercise_id>', methods=['DELETE'])
def delete_exercise(exercise_id):
    db = get_db()
    db.execute('DELETE FROM exercises WHERE id = ?', (exercise_id,))
    db.commit()
    return '', 204


if __name__ == '__main__':
    init_db()
    app.run(port=3000, debug=True, use_reloader=False)

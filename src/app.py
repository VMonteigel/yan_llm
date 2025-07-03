import uuid
from flask import Flask, render_template, request, jsonify, session
from models import AsSetting, AsHistory, db, gen_img, reply, validator, reviewer


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db.init_app(app)
app.secret_key = 'your_secret_service_here'


@app.route("/")
def home():
    # session.clear()
    session.permanent = True
    if 'user_id' not in session:
        session['user_id'] = f"user_{uuid.uuid4().hex[:8]}"
        AsSetting.add_user(AsSetting, session['user_id'])
    session['cr_status'] = False
    chat_history = AsHistory.query.filter_by(user_id=session['user_id']).order_by(AsHistory.timestamp.asc()).all()
    templ = AsSetting.templ(AsSetting, session['user_id'])
    return render_template('index.html', chat_history=chat_history, **templ)


@app.route('/promt', methods=['GET', 'POST'])
def handle_promt():
    if request.method == 'GET':
        if session['cr_status'] is True:
            session['cr_status'] = False
            return jsonify({'status': 'ready'})
        else:
            return jsonify({'status': 'wait'})
    elif request.method == 'POST':
        try:
            json_str = request.get_json()
            AsHistory.clean(AsHistory, session['user_id'])
            chek = validator(json_str.get("valid"), json_str.get("promt"))
            if chek:
                json_str["img"] = gen_img(json_str)
                AsSetting.add_form(AsSetting, session['user_id'], json_str)
            else:
                reviewer(session['user_id'], json_str.get("promt"), json_str.get("valid"))
            session['cr_status'] = True
            return jsonify({'status': 'success'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message")
    llm_reply = reply(session['user_id'], user_message)
    return jsonify({"reply": llm_reply})


@app.route("/clear", methods=["POST"])
def clear():
    data = request.get_json()
    if data.get("key") == 'clear':
        AsHistory.clean(AsHistory, session['user_id'])
    return jsonify({'status': 'ready'})


if __name__ == "__main__":
    with app.app_context():
        # db.drop_all()
        db.create_all()
        app.run(debug=True)

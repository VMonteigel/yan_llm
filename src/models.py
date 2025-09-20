from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


class AsSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), index=True)
    gender = db.Column(db.String(36))
    age = db.Column(db.String(36))
    tllm = db.Column(db.Float)
    valid = db.Column(db.String(36))
    promt = db.Column(db.Text)
    img = db.Column(db.String(255))

    @classmethod
    def add_user(cls, user_id):
        try:
            if cls.query.filter_by(user_id=user_id).first():
                print(f"Пользователь {user_id} уже существует")
                return False

            new_entry = cls(
                user_id=user_id,
                gender='Мужчина',
                age='26',
                tllm=0.6,
                valid='hard',
                promt='Ты специалист YandexGPT. Твоя цель помочь пользователю ' +
                      'составить правильный текст системного промта для ИИ ассистента.',
                img='static/images/yandex.jpg'
            )

            db.session.add(new_entry)
            db.session.commit()
            print(f"Пользователь {user_id} успешно добавлен")
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при добавлении пользователя {user_id}: {str(e)}")
            return False

    @classmethod
    def add_form(cls, user_id, json_data):
        entry = cls.query.filter(cls.user_id == user_id).first()
        if 'gender' in json_data:
            entry.gender = json_data['gender']
        if 'age' in json_data:
            entry.age = json_data['age']
        if 'tllm' in json_data:
            entry.tllm = float(json_data['tllm'])
        if 'promt' in json_data:
            entry.promt = json_data['promt']
        if 'valid' in json_data:
            entry.valid = json_data['valid']
        if 'img' in json_data:
            entry.img = json_data['img']
        db.session.commit()

    @classmethod
    def templ(cls, user_id):
        entry = cls.query.filter(cls.user_id == user_id).first()
        resp = {
            'gender': entry.gender,
            'age': entry.age,
            'tllm': entry.tllm,
            'promt': entry.promt,
            'valid': entry.valid,
            'img': entry.img
            }
        return resp


class AsHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), nullable=False, index=True)
    user_t = db.Column(db.Text, nullable=True)
    llm_t = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now(), index=True)

    @classmethod
    def add_message(cls, user_id, message, reply):
        count = cls.query.filter_by(user_id=user_id).count()
        if count >= 13:
            subquery = (cls.query
                        .filter_by(user_id=user_id)
                        .order_by(cls.timestamp.asc())
                        .limit(1))
            oldest_subq = subquery.with_entities(cls.id).scalar_subquery()
            cls.query.filter(cls.id == oldest_subq).delete(synchronize_session=False)

        new_entry = cls(
            user_id=user_id,
            user_t=message,
            llm_t=reply
        )
        db.session.add(new_entry)
        db.session.commit()

    @classmethod
    def history(cls, user_id):
        history = []
        his_table = cls.query.filter_by(user_id=user_id).order_by(cls.timestamp.asc()).all()
        for entry in his_table:
            history.extend([
                {"role": "user", "text": entry.user_t},
                {"role": "assistant", "text": entry.llm_t},
            ])
        return history

    @classmethod
    def clean(cls, user_id):
        try:
            deleted_count = cls.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            print(f"Удалено {deleted_count} записей для user_id {user_id}")
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при удалении: {str(e)}")

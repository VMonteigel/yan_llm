import uuid
import pathlib
import requests
from yandex_cloud_ml_sdk import YCloudML
from flask_sqlalchemy import SQLAlchemy
from dotenv import dotenv_values
db = SQLAlchemy()

env = dotenv_values()

sdk = YCloudML(folder_id=env['FOLDER_ID'], auth=env['API_KEY'])
model = sdk.models.completions("yandexgpt", model_version="rc")
model_img = sdk.models.image_generation(model_name="yandex-art", model_version="latest")
model_img = model_img.configure(width_ratio=1, height_ratio=1, seed=50)


def yan_gpt(data):
    response = requests.post(
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        headers={
            "Accept": "application/json",
            "Authorization": f"Api-Key {env['API_KEY']}"
        },
        json=data,
    ).json()
    message = response['result']['alternatives'][0]['message']['text']
    return message


def make_gpt(promt, his_mes, tllm=0.5, max=100):
    data = {}
    data["modelUri"] = f"gpt://{env['FOLDER_ID']}/yandexgpt"
    data["completionOptions"] = {"temperature": tllm, "maxTokens": max}
    data["messages"] = [
        {"role": "system", "text": promt},
    ]
    if his_mes:
        data["messages"].extend(his_mes)
    return data


def validator(rigor, promt):
    his_mes = []
    his_mes.extend([
        {"role": "user", "text": promt}
    ])
    if rigor == 'light':
        role = "Определи: есть ли в тексте упоминание человека или его " \
            "качестава или его черты характера или его профессии или " \
            "рода деятельности. Ответь да или нет."
        data = make_gpt(tllm=0.5, promt=role, his_mes=his_mes, max=1)
        ansver = yan_gpt(data)
        if ansver.lower() == 'да':
            return True
        else:
            return False

    else:
        role = "Оцени пригодность этого текста для промта ИИ ассистента. "\
            "Поставь этому тексту оценку по пятибальной шкале, где 1 балл - " \
            "это вообще несвязный текст, 5 баллов - хороший, рабочий вариант. " \
            "Твой ответ - одна цифра оценки"
        data = make_gpt(tllm=0.5, promt=role, his_mes=his_mes, max=2)
        ansver = yan_gpt(data)
        if int(ansver) > 3:
            return True
        else:
            return False


def reviewer(user_id, promt, valid):
    men = {
        'gender': 'Мужчина',
        'age': '62',
        'tllm': '0.6',
        'valid': 'hard',
        'promt': (
            'Ты специалист YandexGPT по созданию ИИ ассистентов.'
            'Первым вопросом пользователь отправляет тебе свой вариант промта. '
            'Ты объсняешь ему почему он не подходит и дальше продолжаешь '
            'беседу с целью улучшить его навыки в написании промтов'
        ),
        'img': '/static/images/men.jpg'
    }
    girl = {
        'gender': 'Женщина',
        'age': '33',
        'tllm': '0.8',
        'valid': 'light',
        'promt': (
            'Ты консультант YandexGPT по настройке цифрового собеседника - '
            'Вымышленного лица от чьего имени chat YandexGPT будет вести беседу. '
            'Первым вопросом пользователь отправляет тебе свой вариант промта. '
            'Ты объсняешь ему почему он не подходит и дальше продолжаешь '
            'беседу с целью улучшить его навыки в написании промтов'
        ),
        'img': '/static/images/girl.jpg'
    }
    if valid == 'light':
        js_str = girl
    else:
        js_str = men
    his_mes = []
    his_mes.extend([
        {"role": "user", "text": promt}
    ])
    head = make_gpt(js_str.get("promt"), his_mes, 0.8, max=180)
    llm_reply = yan_gpt(head)
    AsHistory.add_message(AsHistory, user_id, promt, llm_reply)
    AsSetting.add_form(AsSetting, user_id, js_str)


class AsSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36),index=True)
    gender = db.Column(db.String(36))
    age = db.Column(db.String(36))
    tllm = db.Column(db.Float)
    valid = db.Column(db.String(36))
    promt = db.Column(db.Text)
    img = db.Column(db.String(255))

    def add_user(self, user_id):
        try:
            if AsSetting.query.filter_by(user_id=user_id).first():
                print(f"Пользователь {user_id} уже существует")
                return False

            new_entry = AsSetting(
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

    def add_form(self, user_id, json_data):
        entry = self.query.filter(AsSetting.user_id == user_id).first()
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

    def templ(self, user_id):
        entry = self.query.filter(AsSetting.user_id == user_id).first()
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

    def add_message(self, user_id, message, reply):
        count = self.query.filter_by(user_id=user_id).count()
        if count >= 13:
            subquery = (self.query
                        .filter_by(user_id=user_id)
                        .order_by(AsHistory.timestamp.asc())
                        .limit(1))
            oldest_subq = subquery.with_entities(AsHistory.id).scalar_subquery()
            self.query.filter(AsHistory.id == oldest_subq).delete(synchronize_session=False)

        new_entry = AsHistory(
            user_id=user_id,
            user_t=message,
            llm_t=reply
        )
        db.session.add(new_entry)
        db.session.commit()

    def history(self, user_id):
        history = []
        his_table = self.query.filter_by(user_id=user_id).order_by(AsHistory.timestamp.asc()).all()
        for entry in his_table:
            history.extend([
                {"role": "user", "text": entry.user_t},
                {"role": "assistant", "text": entry.llm_t},
            ])
        return history

    def clean(self, user_id):
        try:
            deleted_count = AsHistory.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            print(f"Удалено {deleted_count} записей для user_id {user_id}")
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при удалении: {str(e)}")


def reply(user_id, user_message):
    templ = AsSetting.templ(AsSetting, user_id)
    history = AsHistory.history(AsHistory, user_id)
    history.extend([
        {"role": "user", "text": user_message}
    ])
    head = make_gpt(templ['promt'], history, templ['tllm'], max=100)
    llm_reply = yan_gpt(head)
    AsHistory.add_message(AsHistory, user_id, user_message, llm_reply)
    return llm_reply


def gen_img(json_data):
    required_fields = ['gender', 'age', 'promt']
    for field in required_fields:
        if field not in json_data:
            raise ValueError(f"Отсутствует обязательное поле: {field}")

    filename = uuid.uuid4().hex[:8] + '.jpg'
    save_path = pathlib.Path("static/images") / filename

    make = f"Тебе нужно создать промт для YandexArt, чтобы сгенерировать поясной портрет ассистента " \
        f"в подходящей для контекста одежде и на подходящем фоне по его промту. " \
        f"Его описание: пол - {json_data['gender']}, возраст - {json_data['age']}. " \
        f"Его промт: {json_data['promt']}"

    try:
        messages = model.run(make)
        operation = model_img.run_deferred(messages)
        result = operation.wait()

        save_path.write_bytes(result.image_bytes)
        return f"/static/images/{filename}"
    except Exception as e:
        return f"Произошла ошибка: {str(e)}"

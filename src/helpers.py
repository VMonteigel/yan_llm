import uuid
import pathlib
from llm import yan_gpt, make_gpt, model, model_img
from models import AsSetting, AsHistory


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


def gen_img(json_data):
    required_fields = ['gender', 'age', 'promt']
    for field in required_fields:
        if field not in json_data:
            error_msg = f"Отсутствует обязательное поле: {field}"
            print(error_msg)
            raise ValueError(error_msg)

    # Создаем директорию
    image_dir = pathlib.Path("static/images")
    filename = uuid.uuid4().hex[:8] + '.jpg'
    save_path = image_dir / filename
    # print(f"Save path: {save_path.absolute()}")

    make = f"Тебе нужно создать промт для YandexArt, чтобы сгенерировать поясной портрет ассистента " \
        f"в подходящей для контекста одежде и на подходящем фоне по его промту. " \
        f"Его описание: пол - {json_data['gender']}, возраст - {json_data['age']}. " \
        f"Его промт: {json_data['promt']}"

    try:
        messages = model.run(make)
        operation = model_img.run_deferred(messages)
        result = operation.wait()

        if hasattr(result, 'image_bytes') and result.image_bytes:
            save_path.write_bytes(result.image_bytes)
            return f"/static/images/{filename}"
        else:
            return "Результат не содержит image_bytes или он пустой"

    except Exception as e:
        return f"Произошла ошибка: {str(e)}"


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
    head = make_gpt(js_str.get("promt"), his_mes, 0.8, max=888)
    llm_reply = yan_gpt(head)
    AsHistory.add_message(user_id, promt, llm_reply)
    AsSetting.add_form(user_id, js_str)


def reply(user_id, user_message):
    templ = AsSetting.templ(user_id)
    history = AsHistory.history(user_id)
    history.extend([
        {"role": "user", "text": user_message}
    ])
    promt = f"Ты - {templ['gender']}, твой возраст - {templ['age']}." \
        f"Твои ответы должны соответствовать твоему полу, возрасту и роли из твоего промпта." \
        f"Твой промпт: {templ['promt']} " \
        f"Веди себя естественно в рамках твоего пола, возраста и роли, не говори, что ты искусственный интелект. " \
        f"Формат вывода обычный текст, без таблиц и Markdown."
    print(promt)
    head = make_gpt(promt, history, templ['tllm'], max=888)
    llm_reply = yan_gpt(head)
    AsHistory.add_message(user_id, user_message, llm_reply)
    return llm_reply

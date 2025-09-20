import requests
from yandex_cloud_ml_sdk import YCloudML
from dotenv import dotenv_values

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


def make_gpt(promt, his_mes, tllm=0.5, max=888):
    data = {}
    data["modelUri"] = f"gpt://{env['FOLDER_ID']}/yandexgpt"
    data["completionOptions"] = {"temperature": tllm, "maxTokens": max}
    data["messages"] = [
        {"role": "system", "text": promt},
    ]
    if his_mes:
        data["messages"].extend(his_mes)
    return data

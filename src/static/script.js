document.getElementById('chat-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const input = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const userMessage = input.value.trim();
    if (!userMessage) return;

    // 1. Показываем сообщение пользователя
    chatBox.innerHTML += `<div class="message user"><p>Вы:<br/> ${userMessage}</p></div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
    input.value = '';

    // 2. Показываем индикатор загрузки
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message llm loading';
    loadingDiv.innerHTML = '<p>Ассистент:<br/> Обдумываю ответ...</p>';
    chatBox.appendChild(loadingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        // 3. Отправляем запрос на сервер
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: userMessage})
        });

        if (!response.ok) throw new Error('Network response was not ok');

        const data = await response.json();

        // 4. Заменяем индикатор загрузки на реальный ответ
        loadingDiv.innerHTML = `<p>Ассистент:<br/> ${data.reply}</p>`;
        loadingDiv.classList.remove('loading');
    } catch (error) {
        // 5. Обрабатываем ошибки
        loadingDiv.innerHTML = '<p>Ассистент:<br/> Sorry, an error occurred.</p>';
        console.error('Error:', error);
    } finally {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

});

document.getElementById('newas').addEventListener('submit', async function(e) {
    e.preventDefault();

    const promtTextarea = document.getElementById('promt');
    const originalContent = promtTextarea.value;

    // Проверка на пустое поле
    if (!promtTextarea.value.trim()) {
        alert('Поле "Промт" не может быть пустым!');
        return;
    }
    // Блокируем форму и показываем сообщение о обработке
    promtTextarea.value = 'Ваш запрос обрабатывается...';
    document.querySelector('button[type="submit"]').disabled = true;

    try {
        // Отправка данных формы
        const response = await fetch('/promt', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                gender: document.querySelector('input[name="gender"]:checked').value,
                age: document.getElementById('ageRange').value,
                tllm: document.getElementById('tRange').value,
                valid: document.querySelector('input[name="valid"]:checked').value,
                promt: originalContent
            })
        });

        if (!response.ok) throw new Error('Ошибка сервера');
        console.log('ответ получен');

        const checkStatus = async (retryCount = 0) => {
            try {
                const statusResponse = await fetch('/promt', { method: 'GET' });
                console.log('отправили');

                if (!statusResponse.ok) {
                    throw new Error('Ошибка сети или сервера');
                }

                const data = await statusResponse.json();

                if (data.status === 'ready') {    // Когда сервер готов, перезагружаем страницу
                    location.reload();
                } else if (retryCount < 3) {    // Продолжаем опрос через 5 секунд, если еще есть попытки
                    setTimeout(() => checkStatus(retryCount + 1), 5000);
                } else {
                    console.error('Превышено количество попыток. Сервер не ответил.');
                }
            } catch (error) {
                if (retryCount < 3) {
                    setTimeout(() => checkStatus(retryCount + 1), 5000);
                } else {
                    console.error('Ошибка после 3 попыток:', error);
                }
            }
        };

        // Запускаем проверку статуса
        checkStatus();  // <-- Добавлен вызов функции

    } catch (error) {
        // В случае ошибки восстанавливаем форму
        promtTextarea.value = originalContent;
        document.querySelector('button[type="submit"]').disabled = false;
        alert('Произошла ошибка: ' + error.message);
    }
});

document.getElementById('clear-but').addEventListener('click', async function(e) {
    e.preventDefault();

    try {
        // Отправка данных формы
        const response = await fetch('/clear', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ key: 'clear' })
        });

        if (!response.ok) throw new Error('Ошибка сервера');
        console.log('Успех:');
        location.reload();
    } catch (error) {
        console.error('Ошибка:', error);
        // Обработка ошибки
    }
});

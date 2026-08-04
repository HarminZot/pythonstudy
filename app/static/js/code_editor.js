
const editor = document.getElementById('code-editor');
const output = document.getElementById('code-output');
const input = document.getElementById('custom-input');

editor?.addEventListener('keydown', (event) => {
    if (event.key === 'Tab') {
        event.preventDefault();
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        editor.value = editor.value.substring(0, start) + '    ' + editor.value.substring(end);
        editor.selectionStart = editor.selectionEnd = start + 4;
    }
});

document.getElementById('reset-code')?.addEventListener('click', () => {
    editor.value = window.STARTER_CODE || '';
});

async function run(endpoint, submit = false) {
    output.textContent = 'Выполнение...';
    const taskId = document.getElementById(submit ? 'submit-code' : 'run-code').dataset.taskId;
    const body = submit
        ? {code: editor.value}
        : {code: editor.value, input: input.value, task_id: Number(taskId)};
    const response = await apiFetch(endpoint, {method: 'POST', body: JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) {
        output.textContent = data.error || 'Ошибка запроса';
        return;
    }
    if (submit) {
        output.textContent = `Статус: ${data.status}
Баллы: ${data.score}%
Тесты: ${data.passed_tests}/${data.total_tests}`;
        setTimeout(() => { window.location.href = data.redirect; }, 900);
    } else {
        output.textContent = [
            `Статус: ${data.status}`,
            `Время: ${data.execution_time_ms} мс`,
            data.stdout ? `
Вывод:
${data.stdout}` : '',
            data.stderr ? `
Ошибки:
${data.stderr}` : ''
        ].join('\n');
    }
}

document.getElementById('run-code')?.addEventListener('click', (event) => {
    run('/api/code/run');
});
document.getElementById('submit-code')?.addEventListener('click', (event) => {
    run(`/api/tasks/${event.target.dataset.taskId}/submit`, true);
});

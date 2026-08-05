
const editor = document.getElementById('code-editor');
const output = document.getElementById('code-output');
const input = document.getElementById('custom-input');
const draftStatus = document.getElementById('draft-status');
const draftKey = window.DRAFT_KEY;
const codeMirrorEditor = editor && window.CodeMirror
    ? window.CodeMirror.fromTextArea(editor, {
        mode: 'python',
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        lineWrapping: false
    })
    : null;

const getCode = () => codeMirrorEditor ? codeMirrorEditor.getValue() : (editor?.value || '');
const setCode = (value) => {
    if (codeMirrorEditor) {
        codeMirrorEditor.setValue(value);
    } else if (editor) {
        editor.value = value;
    }
};

const savedDraft = draftKey ? window.localStorage.getItem(draftKey) : null;
if (savedDraft !== null) {
    setCode(savedDraft);
    if (draftStatus) draftStatus.textContent = 'Черновик восстановлен';
}

let draftTimer;
const saveDraft = () => {
    if (!draftKey) return;
    window.clearTimeout(draftTimer);
    draftTimer = window.setTimeout(() => {
        window.localStorage.setItem(draftKey, getCode());
        if (draftStatus) draftStatus.textContent = 'Черновик сохранен';
    }, 400);
};

if (codeMirrorEditor) {
    codeMirrorEditor.on('change', saveDraft);
} else {
    editor?.addEventListener('input', saveDraft);
}

if (!codeMirrorEditor) editor?.addEventListener('keydown', (event) => {
    if (event.key === 'Tab') {
        event.preventDefault();
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        editor.value = editor.value.substring(0, start) + '    ' + editor.value.substring(end);
        editor.selectionStart = editor.selectionEnd = start + 4;
    }
});

document.getElementById('reset-code')?.addEventListener('click', () => {
    setCode(window.STARTER_CODE || '');
    if (draftKey) window.localStorage.removeItem(draftKey);
    if (draftStatus) draftStatus.textContent = 'Черновик сброшен';
});

const fullscreenButton = document.getElementById('toggle-fullscreen');
const editorPanel = document.querySelector('.editor-panel');
const setFullscreen = (enabled) => {
    editorPanel?.classList.toggle('fullscreen', enabled);
    document.body.classList.toggle('editor-fullscreen', enabled);
    fullscreenButton?.setAttribute('aria-pressed', String(enabled));
    if (fullscreenButton) fullscreenButton.textContent = enabled ? 'Свернуть' : 'На весь экран';
    codeMirrorEditor?.refresh();
};

fullscreenButton?.addEventListener('click', () => {
    setFullscreen(!editorPanel?.classList.contains('fullscreen'));
});

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && editorPanel?.classList.contains('fullscreen')) setFullscreen(false);
});

async function run(endpoint, submit = false) {
    output.textContent = 'Выполнение...';
    const taskId = document.getElementById(submit ? 'submit-code' : 'run-code').dataset.taskId;
    const body = submit
        ? {code: getCode()}
        : {code: getCode(), input: input.value, task_id: Number(taskId)};
    const response = await apiFetch(endpoint, {method: 'POST', body: JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) {
        output.textContent = data.error || 'Ошибка запроса';
        return;
    }
    if (submit) {
        if (draftKey) window.localStorage.removeItem(draftKey);
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

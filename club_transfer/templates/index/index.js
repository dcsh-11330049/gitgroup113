const API_BASE = '/clubs/api';

const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const loginSubmit = document.getElementById('login-submit');

document.addEventListener('DOMContentLoaded', () => {
    loginForm.addEventListener('submit', handleLogin);
    redirectIfAlreadyLoggedIn();
});

async function redirectIfAlreadyLoggedIn() {
    try {
        const data = await apiGet('/current-user/');
        if (data.logged_in && data.user.dashboard_url) {
            window.location.replace(data.user.dashboard_url);
        }
    } catch (error) {
        showLoginError('無法確認登入狀態，請重新登入。');
    }
}

async function handleLogin(event) {
    event.preventDefault();
    clearLoginError();

    const username = loginForm.username.value.trim();
    const password = loginForm.password.value;

    if (!username || !password) {
        showLoginError('請輸入帳號與密碼。');
        return;
    }

    setLoading(true);

    try {
        const data = await apiPostJson('/login/', { username, password });
        window.location.assign(data.redirect_url || '/clubs/');
    } catch (error) {
        showLoginError(error.message || '登入失敗，請再試一次。');
        setLoading(false);
    }
}

async function apiGet(path) {
    return apiFetch(path, { method: 'GET' });
}

async function apiPostJson(path, payload) {
    return apiFetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
}

async function apiFetch(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
        credentials: 'same-origin',
        ...options,
    });

    const data = await response.json();
    if (!response.ok || data.success === false) {
        throw new Error(data.message || data.error || '請求失敗。');
    }
    return data;
}

function showLoginError(message) {
    loginError.textContent = message;
    loginError.hidden = false;
}

function clearLoginError() {
    loginError.textContent = '';
    loginError.hidden = true;
}

function setLoading(isLoading) {
    loginSubmit.disabled = isLoading;
    loginSubmit.textContent = isLoading ? '登入中...' : '登入';
}

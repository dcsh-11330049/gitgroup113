const legacyLoginDialog = document.querySelector('#login-dialog');
const legacyLoginForm = legacyLoginDialog?.querySelector('form');
const legacyLoginIconContainer = document.querySelector('#login-icon-container');
const legacyLoginIconButton = document.querySelector('#login-icon');

if (legacyLoginDialog && legacyLoginForm && legacyLoginIconButton) {
    legacyLoginIconButton.addEventListener('click', () => {
        legacyLoginIconContainer?.setAttribute('hidden', '');
        if (!legacyLoginDialog.open) {
            legacyLoginDialog.showModal();
        }
    });

    legacyLoginDialog.addEventListener('close', () => {
        legacyLoginIconContainer?.removeAttribute('hidden');
        const errorMessage = legacyLoginDialog.querySelector('.error-message');
        if (errorMessage) errorMessage.textContent = '';
    });

    legacyLoginForm.addEventListener('submit', async event => {
        event.preventDefault();

        const username = legacyLoginForm.username.value.trim();
        const password = legacyLoginForm.password.value;
        const result = await loginUser(username, password);

        if (result.success) {
            window.location.href = result.data.redirect_url || '/clubs/';
            return;
        }

        const errorMessage = legacyLoginDialog.querySelector('.error-message');
        if (errorMessage) {
            errorMessage.textContent = result.message || '登入失敗，請再試一次。';
        }
    });
}

async function loginUser(username, password) {
    try {
        const response = await fetch('/clubs/api/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
            credentials: 'same-origin',
        });

        const data = await response.json();
        return {
            success: response.ok && data.success !== false,
            data,
            message: data.message || data.error,
        };
    } catch (error) {
        return { success: false, error: error.message, message: error.message };
    }
}

async function getCurrentUser() {
    const response = await fetch('/clubs/api/current-user/', {
        credentials: 'same-origin',
    });
    return response.json();
}

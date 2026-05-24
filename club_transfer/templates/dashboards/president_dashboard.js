const API_BASE = '/clubs/api';

let currentUser = null;
let myClubs = [];

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupEventListeners();
    loadDashboard();
});

function setupEventListeners() {
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    document.addEventListener('click', handleReviewClick);
}

function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', () => switchTab(button.dataset.tab));
    });
}

function switchTab(tabName) {
    const button = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (!button) return;

    document.querySelectorAll('.tab-btn').forEach(item => item.classList.remove('active'));
    button.classList.add('active');

    document.querySelectorAll('.tab-content').forEach(section => section.classList.remove('active'));
    document.getElementById(tabName).classList.add('active');

    if (tabName === 'description-approvals') loadPendingModifications();
    if (tabName === 'transfer-approvals') loadPendingTransfers();
}

async function loadDashboard() {
    currentUser = await loadCurrentUser();
    if (!currentUser) return;

    document.getElementById('user-name').textContent = currentUser.name;
    await loadMyClubs();
    await Promise.all([loadPendingModifications(), loadPendingTransfers()]);
}

async function loadCurrentUser() {
    const data = await apiGet('/current-user/');
    if (!data.logged_in) {
        window.location.href = '/clubs/';
        return null;
    }
    return data.user;
}

async function loadMyClubs() {
    myClubs = await apiGet('/my-clubs/');
    const container = document.getElementById('my-club-container');

    if (myClubs.length === 0) {
        container.innerHTML = '<p class="muted">目前沒有擔任社長的社團。</p>';
        return;
    }

    container.innerHTML = myClubs.map(club => `
        <article class="card">
            <div class="card-title">${escapeHtml(club.name)}</div>
            <p><strong>指導老師：</strong> ${escapeHtml(club.teacher_name || '未指派')}</p>
            <p><strong>人數：</strong> ${formatCapacity(club)}</p>
            <p>${club.description ? escapeHtml(club.description) : '<span class="muted">尚未提供社團介紹。</span>'}</p>
        </article>
    `).join('');
}

async function loadPendingModifications() {
    const container = document.getElementById('pending-modifications');
    if (!myClubs.length) {
        container.innerHTML = '<p class="muted">目前沒有擔任社長的社團。</p>';
        return;
    }

    const groups = await Promise.all(myClubs.map(club => apiGet(`/clubs/${club.id}/pending-modifications/`)));
    const modifications = groups.flat();

    if (modifications.length === 0) {
        container.innerHTML = '<p class="muted">目前沒有待審核的社團介紹修改。</p>';
        return;
    }

    container.innerHTML = modifications.map(renderModificationCard).join('');
}

function renderModificationCard(modification) {
    const url = normalizeUrl(modification.description_url);
    const documents = modification.documents.length
        ? modification.documents.map(document => `
            <li><a href="${escapeAttr(document.url)}" target="_blank" rel="noopener">${escapeHtml(document.title)}</a></li>
        `).join('')
        : '<li class="muted">沒有待審核文件。</li>';

    return `
        <article class="card">
            <div class="card-title">${escapeHtml(modification.club_name)}</div>
            <p><strong>送出者：</strong> ${escapeHtml(modification.submitted_by)}</p>
            <p><strong>社團介紹：</strong></p>
            <p>${modification.description ? escapeHtml(modification.description).replace(/\n/g, '<br>') : '<span class="muted">未填寫社團介紹。</span>'}</p>
            ${url ? `<p><a href="${escapeAttr(url)}" target="_blank" rel="noopener">開啟送出的網址</a></p>` : '<p class="muted">未送出網址。</p>'}
            <ul class="document-list">${documents}</ul>
            <p class="muted">送出時間：${formatDateTime(modification.created_at)}</p>
            <div class="modal-actions">
                <button class="btn-primary" type="button" data-description-review="approved" data-id="${modification.id}">核准</button>
                <button class="btn-danger" type="button" data-description-review="rejected" data-id="${modification.id}">退回</button>
            </div>
        </article>
    `;
}

async function loadPendingTransfers() {
    const container = document.getElementById('pending-transfers');
    const applications = await apiGet('/transfers/pending/');

    if (applications.length === 0) {
        container.innerHTML = '<p class="muted">目前沒有待審核的轉社申請。</p>';
        return;
    }

    container.innerHTML = applications.map(application => `
        <article class="card">
            <div class="card-title">${escapeHtml(application.student_name)}</div>
            <p>${escapeHtml(application.original_club)} 轉至 ${escapeHtml(application.new_club)}</p>
            <p><span class="status-badge status-pending">${escapeHtml(application.status_display)}</span></p>
            <p class="muted">送出時間：${formatDateTime(application.created_at)}</p>
            <div class="modal-actions">
                <button class="btn-primary" type="button" data-transfer-review="approved" data-id="${application.id}">核准</button>
                <button class="btn-danger" type="button" data-transfer-review="rejected" data-id="${application.id}">退回</button>
            </div>
        </article>
    `).join('');
}

async function handleReviewClick(event) {
    const descriptionButton = event.target.closest('[data-description-review]');
    if (descriptionButton) {
        await reviewDescriptionModification(
            descriptionButton.dataset.id,
            descriptionButton.dataset.descriptionReview
        );
        return;
    }

    const transferButton = event.target.closest('[data-transfer-review]');
    if (transferButton) {
        await reviewTransferApplication(
            transferButton.dataset.id,
            transferButton.dataset.transferReview
        );
    }
}

async function reviewDescriptionModification(id, action) {
    const comment = action === 'rejected' ? window.prompt('退回原因', '') || '' : '';
    const path = action === 'approved'
        ? `/modifications/${id}/approve/`
        : `/modifications/${id}/reject/`;

    try {
        await apiPostJson(path, { comment });
        await loadPendingModifications();
        await loadMyClubs();
    } catch (error) {
        window.alert(error.message);
    }
}

async function reviewTransferApplication(id, action) {
    const comment = action === 'rejected' ? window.prompt('退回原因', '') || '' : '';
    try {
        await apiPostJson(`/transfers/${id}/review/`, { action, comment });
        await loadPendingTransfers();
    } catch (error) {
        window.alert(error.message);
    }
}

async function handleLogout() {
    await apiFetch('/logout/', { method: 'POST' });
    window.location.href = '/clubs/';
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
        throw new Error(data.error || data.message || '請求失敗。');
    }
    return data;
}

function formatCapacity(club) {
    if (!club.max_capacity) return `${club.current_members} / 無上限`;
    return `${club.current_members} / ${club.max_capacity}`;
}

function formatDateTime(value) {
    if (!value) return '未設定';
    return new Date(value).toLocaleString('zh-TW');
}

function normalizeUrl(value) {
    if (!value) return '';
    try {
        const url = new URL(value, window.location.origin);
        return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
    } catch {
        return '';
    }
}

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, character => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;',
    }[character]));
}

function escapeAttr(value) {
    return escapeHtml(value).replace(/`/g, '&#096;');
}

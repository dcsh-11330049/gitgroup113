const API_BASE = '/clubs/api';

let currentUser = null;
let myClubs = [];

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupModalTabs();
    setupEventListeners();
    loadDashboard();
});

function setupEventListeners() {
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    document.addEventListener('click', handleReviewClick);

    const modal = document.getElementById('club-modal');
    modal.querySelector('.modal-close').addEventListener('click', closeClubModal);
    modal.addEventListener('click', event => {
        if (event.target === modal) closeClubModal();
    });
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

    if (tabName === 'my-clubs') loadMyClubs();
    if (tabName === 'transfer-approvals') loadPendingTransfers();
}

function setupModalTabs() {
    document.querySelectorAll('.modal-tab').forEach(button => {
        button.addEventListener('click', () => switchModalTab(button.dataset.tab));
    });
}

function switchModalTab(tabName) {
    const button = document.querySelector(`.modal-tab[data-tab="${tabName}"]`);
    if (!button) return;

    document.querySelectorAll('.modal-tab').forEach(item => item.classList.remove('active'));
    button.classList.add('active');

    document.querySelectorAll('.modal-tab-content').forEach(section => section.classList.remove('active'));
    document.getElementById(tabName).classList.add('active');
}

async function loadDashboard() {
    currentUser = await loadCurrentUser();
    if (!currentUser) return;

    document.getElementById('user-name').textContent = currentUser.name;
    await Promise.all([loadMyClubs(), loadPendingTransfers()]);
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
    const container = document.getElementById('coached-clubs-container');

    if (myClubs.length === 0) {
        container.innerHTML = '<p class="muted">目前沒有指導社團。</p>';
        return;
    }

    container.innerHTML = myClubs.map(club => `
        <article class="card">
            <div class="card-title">${escapeHtml(club.name)}</div>
            <p><strong>社長：</strong> ${escapeHtml(club.president_name || '未指派')}</p>
            <p><strong>人數：</strong> ${formatCapacity(club)}</p>
            <button class="btn-small" type="button" data-club-id="${club.id}">查看介紹</button>
        </article>
    `).join('');

    container.querySelectorAll('[data-club-id]').forEach(button => {
        button.addEventListener('click', () => showClubModal(button.dataset.clubId));
    });
}

async function showClubModal(clubId) {
    const club = await apiGet(`/clubs/${clubId}/`);
    document.getElementById('modal-club-name').textContent = club.name;
    document.getElementById('club-info').innerHTML = renderDescription(club);
    await Promise.all([loadClubDocuments(clubId), loadClubMembers(clubId)]);
    switchModalTab('info');
    document.getElementById('club-modal').hidden = false;
}

async function loadClubDocuments(clubId) {
    const documents = await apiGet(`/clubs/${clubId}/documents/`);
    document.getElementById('club-documents').innerHTML = renderDocuments(documents);
}

async function loadClubMembers(clubId) {
    const members = await apiGet(`/clubs/${clubId}/members/`);
    document.getElementById('club-members').innerHTML = renderMembers(members);
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
    const transferButton = event.target.closest('[data-transfer-review]');
    if (!transferButton) return;

    const action = transferButton.dataset.transferReview;
    const comment = action === 'rejected' ? window.prompt('退回原因', '') || '' : '';
    try {
        await apiPostJson(`/transfers/${transferButton.dataset.id}/review/`, { action, comment });
        await loadPendingTransfers();
    } catch (error) {
        window.alert(error.message);
    }
}

function closeClubModal() {
    document.getElementById('club-modal').hidden = true;
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

function renderDescription(club) {
    const url = normalizeUrl(club.description_url);
    return `
        <div class="description-block">
            <p><strong>社長：</strong> ${escapeHtml(club.president_name || '未指派')}</p>
            <p><strong>指導老師：</strong> ${escapeHtml(club.teacher_name || '未指派')}</p>
            <p><strong>人數：</strong> ${formatCapacity(club)}</p>
            <hr>
            <p>${club.description ? escapeHtml(club.description).replace(/\n/g, '<br>') : '<span class="muted">尚未提供社團介紹。</span>'}</p>
            ${url ? `
                <p><a href="${escapeAttr(url)}" target="_blank" rel="noopener">開啟社團介紹連結</a></p>
                <iframe class="description-frame" src="${escapeAttr(url)}" title="${escapeAttr(club.name)}社團介紹"></iframe>
            ` : '<p class="muted">尚未提供社團介紹網址。</p>'}
        </div>
    `;
}

function renderDocuments(documents) {
    if (!documents.length) {
        return '<p class="muted">尚未上傳社團介紹文件。</p>';
    }
    return documents.map(document => `
        <article class="document-row">
            <a href="${escapeAttr(document.url)}" target="_blank" rel="noopener">${escapeHtml(document.title)}</a>
            <span class="muted">${formatDateTime(document.uploaded_at)}</span>
        </article>
    `).join('');
}

function renderMembers(members) {
    if (!members.length) {
        return '<p class="muted">目前沒有成員資料。</p>';
    }
    return `
        <div class="table-wrap compact">
            <table class="clubs-table">
                <thead>
                    <tr>
                        <th scope="col">姓名</th>
                        <th scope="col">學號</th>
                        <th scope="col">班級</th>
                        <th scope="col">身分</th>
                    </tr>
                </thead>
                <tbody>
                    ${members.map(member => `
                        <tr>
                            <td>${escapeHtml(member.name)}</td>
                            <td>${escapeHtml(member.student_id)}</td>
                            <td>${escapeHtml(member.class_number)}</td>
                            <td>${escapeHtml(roleLabel(member.role))}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function formatCapacity(club) {
    if (!club.max_capacity) return `${club.current_members} / 無上限`;
    return `${club.current_members} / ${club.max_capacity}`;
}

function roleLabel(role) {
    const labels = {
        student: '學生',
        president: '社長',
        teacher: '教師',
        discipline: '管理員',
        admin: '管理員',
    };
    return labels[role] || role;
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

const API_BASE = '/clubs/api';

let currentUser = null;
let allClubs = [];

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupModalTabs();
    setupEventListeners();
    loadDashboard();
});

function setupEventListeners() {
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    document.getElementById('settings-form').addEventListener('submit', saveSettings);

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

    if (tabName === 'system-settings') loadSystemSettings();
    if (tabName === 'transfer-logs') loadTransferLogs();
    if (tabName === 'all-clubs') loadAllClubs();
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
    await loadSystemSettings();
}

async function loadCurrentUser() {
    const data = await apiGet('/current-user/');
    if (!data.logged_in) {
        window.location.href = '/clubs/';
        return null;
    }
    return data.user;
}

async function loadSystemSettings() {
    const settings = await apiGet('/system-settings/');
    document.getElementById('transfer_start_date').value = toDateTimeLocal(settings.transfer_start_date);
    document.getElementById('transfer_end_date').value = toDateTimeLocal(settings.transfer_end_date);
}

async function saveSettings(event) {
    event.preventDefault();
    const status = document.getElementById('settings-status');
    status.innerHTML = '';

    const start = document.getElementById('transfer_start_date').value;
    const end = document.getElementById('transfer_end_date').value;

    try {
        const data = await apiPostJson('/system-settings/update/', {
            transfer_start_date: start ? new Date(start).toISOString() : null,
            transfer_end_date: end ? new Date(end).toISOString() : null,
        });
        showMessage(status, data.message, 'success');
    } catch (error) {
        showMessage(status, error.message, 'error');
    }
}

async function loadTransferLogs() {
    const logs = await apiGet('/transfer-logs/');
    const tbody = document.querySelector('#transfer-logs-table tbody');
    tbody.innerHTML = '';

    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="muted">目前沒有轉社申請紀錄。</td></tr>';
        return;
    }

    logs.forEach(log => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${escapeHtml(log.student_name)}</td>
            <td>${escapeHtml(log.original_club)}</td>
            <td>${escapeHtml(log.new_club)}</td>
            <td><span class="status-badge status-${statusClass(log.status)}">${escapeHtml(log.status_display)}</span></td>
            <td>${formatDateTime(log.created_at)}</td>
            <td>${renderApprovalLogs(log.approval_logs)}</td>
        `;
        tbody.appendChild(row);
    });
}

async function loadAllClubs() {
    allClubs = await apiGet('/clubs/');
    const tbody = document.querySelector('#clubs-table tbody');
    tbody.innerHTML = '';

    if (allClubs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="muted">目前沒有社團資料。</td></tr>';
        return;
    }

    allClubs.forEach(club => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${escapeHtml(club.name)}</td>
            <td>${escapeHtml(club.president_name || '未指派')}</td>
            <td>${escapeHtml(club.teacher_name || '未指派')}</td>
            <td>${formatCapacity(club)}</td>
            <td>${club.document_count}</td>
            <td><button class="btn-small" type="button" data-club-id="${club.id}">查看</button></td>
        `;
        tbody.appendChild(row);
    });

    tbody.querySelectorAll('[data-club-id]').forEach(button => {
        button.addEventListener('click', () => showClubModal(button.dataset.clubId));
    });
}

async function showClubModal(clubId) {
    const club = await apiGet(`/clubs/${clubId}/`);
    document.getElementById('modal-club-name').textContent = club.name;
    document.getElementById('club-info').innerHTML = renderDescription(club);
    await Promise.all([loadClubDocuments(clubId), loadClubMembers(clubId)]);
    switchModalTab('info');
    document.getElementById('club-modal').removeAttribute('style');
}

async function loadClubDocuments(clubId) {
    const documents = await apiGet(`/clubs/${clubId}/documents/`);
    document.getElementById('club-documents').innerHTML = renderDocuments(documents);
}

async function loadClubMembers(clubId) {
    const members = await apiGet(`/clubs/${clubId}/members/`);
    document.getElementById('club-members').innerHTML = renderMembers(members);
}

function renderApprovalLogs(logs) {
    if (!logs.length) {
        return '<span class="muted">尚無審核紀錄。</span>';
    }

    return `
        <ol class="log-list">
            ${logs.map(log => `
                <li>
                    <strong>${escapeHtml(log.reviewer_name)}</strong>
                    ${escapeHtml(log.action_display)}
                    <span class="muted">${formatDateTime(log.created_at)}</span>
                    ${log.comment ? `<div>${escapeHtml(log.comment)}</div>` : ''}
                </li>
            `).join('')}
        </ol>
    `;
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

function closeClubModal() {
    document.getElementById('club-modal').setAttribute('style', 'display: none;');
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

function showMessage(container, message, type) {
    container.innerHTML = `<div class="${type}-message">${escapeHtml(message)}</div>`;
}

function toDateTimeLocal(value) {
    if (!value) return '';
    const date = new Date(value);
    const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 16);
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

function statusClass(status) {
    if (status === 'approved') return 'approved';
    if (status === 'rejected' || status === 'new_club_rejected') return 'rejected';
    return 'pending';
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

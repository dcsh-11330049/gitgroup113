const API_BASE = '/clubs/api';

let currentUser = null;
let myClubs = [];
let allClubs = [];
let selectedClubId = null;
let transferOpen = false;

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupModalTabs();
    setupEventListeners();
    loadDashboard();
});

function setupEventListeners() {
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    document.getElementById('transfer-form').addEventListener('submit', submitTransfer);
    document.getElementById('modify-form').addEventListener('submit', submitDescriptionModification);

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
    if (!button || button.hidden) return;

    document.querySelectorAll('.tab-btn').forEach(item => item.classList.remove('active'));
    button.classList.add('active');

    document.querySelectorAll('.tab-content').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');

    if (tabName === 'transfer') loadMyTransfers();
}

function setupModalTabs() {
    document.querySelectorAll('.modal-tab').forEach(button => {
        button.addEventListener('click', () => switchModalTab(button.dataset.tab));
    });
}

function switchModalTab(tabName) {
    const button = document.querySelector(`.modal-tab[data-tab="${tabName}"]`);
    if (!button || button.hidden) return;

    document.querySelectorAll('.modal-tab').forEach(item => item.classList.remove('active'));
    button.classList.add('active');

    document.querySelectorAll('.modal-tab-content').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');
}

async function loadDashboard() {
    currentUser = await loadCurrentUser();
    if (!currentUser) return;

    document.getElementById('user-name').textContent = currentUser.name;
    await Promise.all([loadTransferSettings(), loadMyClubs(), loadAllClubs()]);
    await loadMyTransfers();
}

async function loadCurrentUser() {
    const data = await apiGet('/current-user/');
    if (!data.logged_in) {
        window.location.href = '/clubs/';
        return null;
    }
    return data.user;
}

async function loadTransferSettings() {
    const settings = await apiGet('/system-settings/');
    transferOpen = settings.transfer_open;

    const transferTab = document.getElementById('transfer-tab');
    transferTab.hidden = !transferOpen;

    const message = document.getElementById('transfer-window-message');
    if (transferOpen) {
        const start = formatDateTime(settings.transfer_start_date);
        const end = formatDateTime(settings.transfer_end_date);
        message.textContent = `轉社開放期間：${start} 至 ${end}`;
    } else {
        message.textContent = '目前不在轉社開放期間。';
        if (document.getElementById('transfer').classList.contains('active')) {
            switchTab('my-club');
        }
    }
}

async function loadMyClubs() {
    myClubs = await apiGet('/my-clubs/');
    const container = document.getElementById('my-club-container');

    if (myClubs.length === 0) {
        container.innerHTML = '<p class="muted">目前沒有社團資料。</p>';
    } else {
        container.innerHTML = myClubs.map(renderClubCard).join('');
        attachClubButtons(container);
    }

    populateTransferSelects();
}

async function loadAllClubs() {
    allClubs = await apiGet('/clubs/');
    displayAllClubs();
    populateTransferSelects();
}

function displayAllClubs() {
    const tbody = document.querySelector('#clubs-table tbody');
    tbody.innerHTML = '';

    allClubs.forEach(club => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${escapeHtml(club.name)}</td>
            <td>${escapeHtml(club.president_name || '未指派')}</td>
            <td>${escapeHtml(club.teacher_name || '未指派')}</td>
            <td>${formatCapacity(club)}</td>
            <td><span class="status-badge status-${club.is_full ? 'rejected' : 'approved'}">${club.is_full ? '已滿額' : '可申請'}</span></td>
            <td><button class="btn-small" type="button" data-club-id="${club.id}">查看</button></td>
        `;
        tbody.appendChild(row);
    });

    attachClubButtons(tbody);
}

function renderClubCard(club) {
    return `
        <article class="card">
            <div class="card-title">${escapeHtml(club.name)}</div>
            <p><strong>社長：</strong> ${escapeHtml(club.president_name || '未指派')}</p>
            <p><strong>指導老師：</strong> ${escapeHtml(club.teacher_name || '未指派')}</p>
            <p><strong>人數：</strong> ${formatCapacity(club)}</p>
            <button class="btn-small" type="button" data-club-id="${club.id}">查看介紹</button>
        </article>
    `;
}

function attachClubButtons(root) {
    root.querySelectorAll('[data-club-id]').forEach(button => {
        button.addEventListener('click', () => showClubModal(button.dataset.clubId));
    });
}

function populateTransferSelects() {
    const currentSelect = document.getElementById('transfer-current-club');
    const targetSelect = document.getElementById('transfer-target-club');

    currentSelect.innerHTML = myClubs.map(club => (
        `<option value="${club.id}">${escapeHtml(club.name)}</option>`
    )).join('');

    targetSelect.innerHTML = allClubs.map(club => (
        `<option value="${club.id}" ${club.is_full ? 'disabled' : ''}>${escapeHtml(club.name)}${club.is_full ? '（已滿額）' : ''}</option>`
    )).join('');
}

async function showClubModal(clubId) {
    selectedClubId = clubId;
    const club = await apiGet(`/clubs/${clubId}/`);

    document.getElementById('modal-club-name').textContent = club.name;
    document.getElementById('club-info').innerHTML = renderDescription(club);
    document.getElementById('description').value = club.description || '';
    document.getElementById('description_url').value = club.description_url || '';
    document.getElementById('modify-status').innerHTML = '';
    document.getElementById('description_files').value = '';

    const modifyTab = document.getElementById('modify-tab');
    modifyTab.hidden = !club.can_modify_description;
    if (!club.can_modify_description && document.getElementById('modify').classList.contains('active')) {
        switchModalTab('info');
    }

    await loadClubDocuments(clubId);
    switchModalTab('info');
    document.getElementById('club-modal').removeAttribute('style');
}

async function loadClubDocuments(clubId) {
    const documents = await apiGet(`/clubs/${clubId}/documents/`);
    document.getElementById('club-documents').innerHTML = renderDocuments(documents);
}

async function submitDescriptionModification(event) {
    event.preventDefault();
    if (!selectedClubId) return;

    const form = event.currentTarget;
    const formData = new FormData(form);
    const status = document.getElementById('modify-status');
    status.innerHTML = '';

    try {
        const data = await apiFetch(`/clubs/${selectedClubId}/submit-modification/`, {
            method: 'POST',
            body: formData,
        });
        showMessage(status, data.message, 'success');
        form.reset();
    } catch (error) {
        showMessage(status, error.message, 'error');
    }
}

async function submitTransfer(event) {
    event.preventDefault();

    const status = document.getElementById('transfer-status');
    status.innerHTML = '';
    if (!transferOpen) {
        showMessage(status, '目前不在轉社開放期間。', 'error');
        return;
    }

    const payload = {
        original_club_id: document.getElementById('transfer-current-club').value,
        new_club_id: document.getElementById('transfer-target-club').value,
    };

    try {
        const data = await apiPostJson('/transfers/submit/', payload);
        showMessage(status, data.message, 'success');
        await loadMyTransfers();
    } catch (error) {
        showMessage(status, error.message, 'error');
    }
}

async function loadMyTransfers() {
    const container = document.getElementById('my-transfer-applications');
    const applications = await apiGet('/transfers/mine/');

    if (applications.length === 0) {
        container.innerHTML = '<p class="muted">目前沒有轉社申請紀錄。</p>';
        return;
    }

    container.innerHTML = applications.map(application => `
        <article class="card">
            <div class="card-title">${escapeHtml(application.original_club)} 轉至 ${escapeHtml(application.new_club)}</div>
            <p><span class="status-badge status-${statusClass(application.status)}">${escapeHtml(application.status_display)}</span></p>
            <p class="muted">送出時間：${formatDateTime(application.created_at)}</p>
        </article>
    `).join('');
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

function showMessage(container, message, type) {
    container.innerHTML = `<div class="${type}-message">${escapeHtml(message)}</div>`;
}

function formatCapacity(club) {
    if (!club.max_capacity) return `${club.current_members} / 無上限`;
    return `${club.current_members} / ${club.max_capacity}`;
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

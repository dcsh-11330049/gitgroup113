import json

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import (
    ApprovalLog,
    Club,
    ClubDescriptionModification,
    ClubDocument,
    ClubMembership,
    ClubModificationDocument,
    Student,
    Superviser,
    SystemSettings,
    TransferApplication,
    User,
)


ROLE_DASHBOARD_URLS = {
    'student': '/clubs/dashboard/student/',
    'president': '/clubs/dashboard/president/',
    'teacher': '/clubs/dashboard/teacher/',
    'discipline': '/clubs/dashboard/admin/',
    'admin': '/clubs/dashboard/admin/',
}


def json_error(message, status=400):
    return JsonResponse({'success': False, 'error': message, 'message': message}, status=status)


def parse_json_body(request):
    if not request.body:
        return {}
    return json.loads(request.body)


def get_session_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    return User.objects.filter(id=user_id).first()


def get_user_role(user):
    student = Student.objects.filter(user=user).first()
    if student:
        return student.role

    supervisor = Superviser.objects.filter(user=user).first()
    if supervisor:
        return supervisor.role

    return 'admin'


def role_display(role):
    displays = {
        'student': '學生',
        'president': '社長',
        'teacher': '教師',
        'discipline': '管理員',
        'admin': '管理員',
    }
    return displays.get(role, role)


def dashboard_url_for_role(role):
    return ROLE_DASHBOARD_URLS.get(role, '/clubs/')


def is_admin_role(role):
    return role in {'admin', 'discipline'}


def require_api_user(request):
    user = get_session_user(request)
    if not user:
        return None, None, json_error('請先登入。', status=401)
    role = request.session.get('role') or get_user_role(user)
    return user, role, None


def get_system_settings():
    settings = SystemSettings.objects.order_by('id').first()
    if settings is None:
        settings = SystemSettings.objects.create()
    return settings


def is_transfer_open(settings=None):
    settings = settings or get_system_settings()
    now = timezone.now()
    return bool(
        settings.transfer_start_date
        and settings.transfer_end_date
        and settings.transfer_start_date <= now <= settings.transfer_end_date
    )


def parse_client_datetime(value):
    if not value:
        return None

    parsed = parse_datetime(value)
    if parsed is None:
        parsed = timezone.datetime.fromisoformat(value)

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def current_club_ids_for_user(user):
    membership_ids = set(
        ClubMembership.objects.filter(student=user).values_list('club_id', flat=True)
    )
    if membership_ids:
        return membership_ids

    return set(
        TransferApplication.objects.filter(
            student=user,
            status=TransferApplication.StatusChoices.APPROVED,
        ).values_list('new_club_id', flat=True)
    )


def current_clubs_for_user(user):
    club_ids = current_club_ids_for_user(user)
    return Club.objects.filter(id__in=club_ids).select_related('president', 'teacher')


def clubs_for_dashboard(user, role):
    if role == 'teacher':
        return Club.objects.filter(teacher=user).select_related('president', 'teacher')
    if role == 'president':
        return Club.objects.filter(president=user).select_related('president', 'teacher')
    if role == 'student':
        return current_clubs_for_user(user)
    if is_admin_role(role):
        return Club.objects.all().select_related('president', 'teacher')
    return Club.objects.none()


def can_modify_club_description(user, club):
    student = Student.objects.filter(user=user, role__in=['student', 'president']).first()
    if not student:
        return False
    return club.id in current_club_ids_for_user(user) or club.president_id == user.id


def can_approve_club_description(user, club):
    return club.president_id == user.id


def file_url(request, file_field):
    if not file_field:
        return ''
    try:
        url = file_field.url
    except ValueError:
        return ''
    return request.build_absolute_uri(url)


def serialize_document(document, request):
    return {
        'id': document.id,
        'title': document.title,
        'url': file_url(request, document.file),
        'uploaded_by': document.uploaded_by.name if document.uploaded_by_id else '',
        'uploaded_at': document.uploaded_at.isoformat(),
    }


def serialize_pending_document(document, request):
    return {
        'id': document.id,
        'title': document.title,
        'url': file_url(request, document.file),
        'uploaded_at': document.uploaded_at.isoformat(),
    }


def serialize_club(club, request, user=None):
    return {
        'id': club.id,
        'name': club.club_name,
        'president_name': club.president.name if club.president_id else '',
        'teacher_name': club.teacher.name if club.teacher_id else '',
        'description': club.description or '',
        'description_url': club.description_url or '',
        'current_members': club.current_members,
        'max_capacity': club.max_capacity,
        'is_full': bool(club.max_capacity and club.current_members >= club.max_capacity),
        'document_count': club.documents.count(),
        'can_modify_description': bool(user and can_modify_club_description(user, club)),
        'is_member': bool(user and club.id in current_club_ids_for_user(user)),
    }


def serialize_modification(modification, request):
    return {
        'id': modification.id,
        'club_id': modification.club_id,
        'club_name': modification.club.club_name,
        'description': modification.description or '',
        'description_url': modification.description_url or '',
        'status': modification.status,
        'status_display': modification.get_status_display(),
        'submitted_by': modification.submitted_by.name,
        'created_at': modification.created_at.isoformat(),
        'documents': [
            serialize_pending_document(document, request)
            for document in modification.pending_documents.all()
        ],
    }


def serialize_transfer(application):
    return {
        'id': application.id,
        'student_name': application.student.name,
        'original_club': application.original_club.club_name,
        'new_club': application.new_club.club_name,
        'status': application.status,
        'status_display': application.get_status_display(),
        'created_at': application.created_at.isoformat(),
        'updated_at': application.updated_at.isoformat(),
    }


def serialize_approval_log(log):
    return {
        'id': log.id,
        'reviewer_name': log.reviewer.name,
        'action': log.action,
        'action_display': log.get_action_display(),
        'comment': log.comment or '',
        'created_at': log.created_at.isoformat(),
    }


def index(request):
    """Render the login page, or send logged-in users to their dashboard."""
    user = get_session_user(request)
    if user:
        role = request.session.get('role') or get_user_role(user)
        return redirect(dashboard_url_for_role(role))
    return render(request, 'index/index.html', {'clubs': Club.objects.all()})


def dashboard_response(request, template_name, allowed_roles):
    user = get_session_user(request)
    if not user:
        return redirect('/clubs/')

    role = request.session.get('role') or get_user_role(user)
    if role not in allowed_roles:
        return redirect(dashboard_url_for_role(role))

    return render(request, template_name, {'user': user, 'role': role})


def student_dashboard(request):
    return dashboard_response(request, 'dashboards/student_dashboard.html', {'student'})


def president_dashboard(request):
    return dashboard_response(request, 'dashboards/president_dashboard.html', {'president'})


def teacher_dashboard(request):
    return dashboard_response(request, 'dashboards/teacher_dashboard.html', {'teacher'})


def admin_dashboard(request):
    return dashboard_response(request, 'dashboards/admin_dashboard.html', {'admin', 'discipline'})


@require_http_methods(['POST'])
@csrf_exempt
def api_login(request):
    """Login endpoint for all custom users."""
    try:
        data = parse_json_body(request)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return json_error('請輸入帳號與密碼。')

        user = User.objects.filter(username=username).first()
        if not user or user.password != password:
            return json_error('帳號或密碼錯誤。', status=401)

        role = get_user_role(user)
        request.session['user_id'] = user.id
        request.session['username'] = user.username
        request.session['name'] = user.name
        request.session['role'] = role

        return JsonResponse({
            'success': True,
            'message': f'{user.name}，歡迎回來。',
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'role': role,
                'role_display': role_display(role),
            },
            'redirect_url': dashboard_url_for_role(role),
        })
    except json.JSONDecodeError:
        return json_error('資料格式錯誤。')
    except Exception as exc:
        return json_error(str(exc), status=500)


@require_http_methods(['POST'])
@csrf_exempt
def api_logout(request):
    request.session.flush()
    return JsonResponse({'success': True, 'message': '已登出。'})


@require_http_methods(['GET'])
def api_current_user(request):
    user = get_session_user(request)
    if not user:
        return JsonResponse({'logged_in': False})

    role = request.session.get('role') or get_user_role(user)
    return JsonResponse({
        'logged_in': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'role': role,
            'role_display': role_display(role),
            'dashboard_url': dashboard_url_for_role(role),
        },
    })


@require_http_methods(['GET'])
def clubs_api(request):
    user = get_session_user(request)
    clubs = Club.objects.select_related('president', 'teacher').order_by('club_name')
    return JsonResponse([serialize_club(club, request, user) for club in clubs], safe=False)


@require_http_methods(['GET'])
def api_my_clubs(request):
    user, role, error = require_api_user(request)
    if error:
        return error

    clubs = clubs_for_dashboard(user, role).order_by('club_name')
    return JsonResponse([serialize_club(club, request, user) for club in clubs], safe=False)


@require_http_methods(['GET'])
def api_club_detail(request, club_id):
    user = get_session_user(request)
    club = Club.objects.select_related('president', 'teacher').filter(id=club_id).first()
    if not club:
        return json_error('找不到社團。', status=404)

    return JsonResponse(serialize_club(club, request, user))


@require_http_methods(['GET'])
def api_club_documents(request, club_id):
    club = Club.objects.filter(id=club_id).first()
    if not club:
        return json_error('找不到社團。', status=404)

    documents = ClubDocument.objects.filter(club=club).select_related('uploaded_by').order_by('-uploaded_at')
    return JsonResponse([serialize_document(document, request) for document in documents], safe=False)


@require_http_methods(['GET'])
def api_club_members(request, club_id):
    club = Club.objects.filter(id=club_id).first()
    if not club:
        return json_error('找不到社團。', status=404)

    member_ids = set(
        ClubMembership.objects.filter(club=club).values_list('student_id', flat=True)
    )
    if not member_ids:
        member_ids.update(
            TransferApplication.objects.filter(
                new_club=club,
                status=TransferApplication.StatusChoices.APPROVED,
            ).values_list('student_id', flat=True)
        )

    students = Student.objects.filter(user_id__in=member_ids).select_related('user').order_by('class_number', 'student_id')
    members = [
        {
            'id': student.user_id,
            'name': student.user.name,
            'student_id': student.student_id,
            'class_number': student.class_number,
            'role': student.role,
        }
        for student in students
    ]
    return JsonResponse(members, safe=False)


@require_http_methods(['POST'])
@csrf_exempt
def api_submit_description_modification(request, club_id):
    user, role, error = require_api_user(request)
    if error:
        return error

    club = Club.objects.filter(id=club_id).first()
    if not club:
        return json_error('找不到社團。', status=404)
    if not can_modify_club_description(user, club):
        return json_error('只有本社團學生可以送出社團介紹修改。', status=403)

    if request.content_type and request.content_type.startswith('multipart/form-data'):
        description = request.POST.get('description', '')
        description_url = request.POST.get('description_url', '')
        files = request.FILES.getlist('files')
    else:
        data = parse_json_body(request)
        description = data.get('description', '')
        description_url = data.get('description_url', '')
        files = []

    modification = ClubDescriptionModification.objects.create(
        club=club,
        submitted_by=user,
        description=description,
        description_url=description_url,
    )

    for uploaded_file in files:
        ClubModificationDocument.objects.create(
            modification=modification,
            title=uploaded_file.name,
            file=uploaded_file,
        )

    return JsonResponse({
        'success': True,
        'message': '社團介紹修改已送出，等待社長審核。',
        'modification_id': modification.id,
    })


@require_http_methods(['GET'])
def api_pending_modifications(request, club_id):
    user, role, error = require_api_user(request)
    if error:
        return error

    club = Club.objects.filter(id=club_id).first()
    if not club:
        return json_error('找不到社團。', status=404)
    if not (can_approve_club_description(user, club) or is_admin_role(role)):
        return json_error('您沒有權限查看此社團的待審核修改。', status=403)

    modifications = (
        ClubDescriptionModification.objects
        .filter(club=club, status=ClubDescriptionModification.StatusChoices.PENDING)
        .select_related('club', 'submitted_by')
        .prefetch_related('pending_documents')
        .order_by('-created_at')
    )
    return JsonResponse([serialize_modification(modification, request) for modification in modifications], safe=False)


@require_http_methods(['POST'])
@csrf_exempt
def api_approve_modification(request, modification_id):
    user, role, error = require_api_user(request)
    if error:
        return error

    try:
        data = parse_json_body(request)
    except json.JSONDecodeError:
        return json_error('資料格式錯誤。')

    with transaction.atomic():
        modification = (
            ClubDescriptionModification.objects
            .select_for_update()
            .select_related('club', 'submitted_by')
            .prefetch_related('pending_documents')
            .filter(id=modification_id)
            .first()
        )
        if not modification:
            return json_error('找不到社團介紹修改紀錄。', status=404)
        if not can_approve_club_description(user, modification.club):
            return json_error('只有社長可以核准此修改。', status=403)
        if modification.status != ClubDescriptionModification.StatusChoices.PENDING:
            return json_error('此修改已審核完成。')

        club = modification.club
        club.description = modification.description
        club.description_url = modification.description_url
        club.save(update_fields=['description', 'description_url'])

        for pending_document in modification.pending_documents.all():
            ClubDocument.objects.create(
                club=club,
                title=pending_document.title,
                file=pending_document.file.name,
                uploaded_by=modification.submitted_by,
            )

        modification.status = ClubDescriptionModification.StatusChoices.APPROVED
        modification.approved_by = user
        modification.approval_comment = data.get('comment', '')
        modification.save(update_fields=['status', 'approved_by', 'approval_comment', 'updated_at'])

    return JsonResponse({'success': True, 'message': '社團介紹修改已核准。'})


@require_http_methods(['POST'])
@csrf_exempt
def api_reject_modification(request, modification_id):
    user, role, error = require_api_user(request)
    if error:
        return error

    try:
        data = parse_json_body(request)
    except json.JSONDecodeError:
        return json_error('資料格式錯誤。')

    modification = (
        ClubDescriptionModification.objects
        .select_related('club')
        .filter(id=modification_id)
        .first()
    )
    if not modification:
        return json_error('找不到社團介紹修改紀錄。', status=404)
    if not can_approve_club_description(user, modification.club):
        return json_error('只有社長可以退回此修改。', status=403)
    if modification.status != ClubDescriptionModification.StatusChoices.PENDING:
        return json_error('此修改已審核完成。')

    modification.status = ClubDescriptionModification.StatusChoices.REJECTED
    modification.approved_by = user
    modification.approval_comment = data.get('comment', '')
    modification.save(update_fields=['status', 'approved_by', 'approval_comment', 'updated_at'])

    return JsonResponse({'success': True, 'message': '社團介紹修改已退回。'})


@require_http_methods(['GET'])
def api_system_settings(request):
    settings = get_system_settings()
    return JsonResponse({
        'transfer_start_date': settings.transfer_start_date.isoformat() if settings.transfer_start_date else None,
        'transfer_end_date': settings.transfer_end_date.isoformat() if settings.transfer_end_date else None,
        'transfer_open': is_transfer_open(settings),
        'server_time': timezone.now().isoformat(),
    })


@require_http_methods(['POST'])
@csrf_exempt
def api_update_system_settings(request):
    user, role, error = require_api_user(request)
    if error:
        return error
    if not is_admin_role(role):
        return json_error('只有管理員可以更新轉社期間。', status=403)

    try:
        data = parse_json_body(request)
        start_date = parse_client_datetime(data.get('transfer_start_date'))
        end_date = parse_client_datetime(data.get('transfer_end_date'))
    except (json.JSONDecodeError, ValueError):
        return json_error('日期格式錯誤。')

    if start_date and end_date and end_date < start_date:
        return json_error('轉社結束時間必須晚於開始時間。')

    settings = get_system_settings()
    settings.transfer_start_date = start_date
    settings.transfer_end_date = end_date
    settings.save(update_fields=['transfer_start_date', 'transfer_end_date'])

    return JsonResponse({'success': True, 'message': '轉社期間已更新。'})


def initial_transfer_status(original_club, new_club):
    choices = TransferApplication.StatusChoices
    sequence = [
        (choices.PENDING_ORIGINAL_PRESIDENT, original_club.president_id),
        (choices.PENDING_ORIGINAL_TEACHER, original_club.teacher_id),
        (choices.PENDING_NEW_PRESIDENT, new_club.president_id),
        (choices.PENDING_NEW_TEACHER, new_club.teacher_id),
        (choices.PENDING_DISCIPLINE, True),
    ]
    for status, has_reviewer in sequence:
        if has_reviewer:
            return status
    return choices.APPROVED


def reviewer_needed_for_status(application, status):
    choices = TransferApplication.StatusChoices
    if status == choices.PENDING_ORIGINAL_PRESIDENT:
        return bool(application.original_club.president_id)
    if status == choices.PENDING_ORIGINAL_TEACHER:
        return bool(application.original_club.teacher_id)
    if status == choices.PENDING_NEW_PRESIDENT:
        return bool(application.new_club.president_id)
    if status == choices.PENDING_NEW_TEACHER:
        return bool(application.new_club.teacher_id)
    if status == choices.PENDING_DISCIPLINE:
        return True
    return False


def next_transfer_status(application):
    choices = TransferApplication.StatusChoices
    sequence = [
        choices.PENDING_ORIGINAL_PRESIDENT,
        choices.PENDING_ORIGINAL_TEACHER,
        choices.PENDING_NEW_PRESIDENT,
        choices.PENDING_NEW_TEACHER,
        choices.PENDING_DISCIPLINE,
    ]
    try:
        current_index = sequence.index(application.status)
    except ValueError:
        return choices.APPROVED

    for status in sequence[current_index + 1:]:
        if reviewer_needed_for_status(application, status):
            return status
    return choices.APPROVED


def can_review_transfer_application(user, role, application):
    choices = TransferApplication.StatusChoices
    status = application.status
    if status == choices.PENDING_ORIGINAL_PRESIDENT:
        return application.original_club.president_id == user.id
    if status == choices.PENDING_ORIGINAL_TEACHER:
        return application.original_club.teacher_id == user.id
    if status == choices.PENDING_NEW_PRESIDENT:
        return application.new_club.president_id == user.id
    if status == choices.PENDING_NEW_TEACHER:
        return application.new_club.teacher_id == user.id
    if status == choices.PENDING_DISCIPLINE:
        return is_admin_role(role)
    return False


def apply_approved_transfer(application):
    if application.original_club_id == application.new_club_id:
        return

    ClubMembership.objects.filter(student=application.student).exclude(club=application.new_club).delete()
    ClubMembership.objects.get_or_create(student=application.student, club=application.new_club)

    original_club = application.original_club
    new_club = application.new_club
    original_club.current_members = max(0, original_club.current_members - 1)
    new_club.current_members += 1
    original_club.save(update_fields=['current_members'])
    new_club.save(update_fields=['current_members'])


@require_http_methods(['POST'])
@csrf_exempt
def api_submit_transfer_application(request):
    user, role, error = require_api_user(request)
    if error:
        return error
    if role not in {'student', 'president'}:
        return json_error('只有學生可以送出轉社申請。', status=403)
    if not is_transfer_open():
        return json_error('目前不在轉社開放期間。', status=403)

    try:
        data = parse_json_body(request)
    except json.JSONDecodeError:
        return json_error('資料格式錯誤。')

    current_club_ids = current_club_ids_for_user(user)
    if not current_club_ids:
        return json_error('You do not have a current club to transfer from.')

    try:
        original_club_id = int(data.get('original_club_id') or next(iter(current_club_ids)))
        new_club_id = int(data.get('new_club_id'))
    except (TypeError, ValueError):
        return json_error('請選擇有效的原社團與目標社團。')

    if original_club_id not in current_club_ids:
        return json_error('選擇的原社團不屬於您的目前社團。', status=403)

    original_club = Club.objects.filter(id=original_club_id).first()
    new_club = Club.objects.filter(id=new_club_id).first()
    if not original_club or not new_club:
        return json_error('找不到選擇的社團。', status=404)
    if original_club.id == new_club.id:
        return json_error('請選擇不同的目標社團。')
    if new_club.max_capacity and new_club.current_members >= new_club.max_capacity:
        return json_error('目標社團已滿額。')

    open_application_exists = TransferApplication.objects.filter(student=user).exclude(
        status__in=[
            TransferApplication.StatusChoices.APPROVED,
            TransferApplication.StatusChoices.REJECTED,
            TransferApplication.StatusChoices.NEW_CLUB_REJECTED,
        ]
    ).exists()
    if open_application_exists:
        return json_error('您已有一筆等待審核的轉社申請。')

    application = TransferApplication.objects.create(
        student=user,
        original_club=original_club,
        new_club=new_club,
        status=initial_transfer_status(original_club, new_club),
    )

    return JsonResponse({
        'success': True,
        'message': '轉社申請已送出。',
        'application': serialize_transfer(application),
    })


@require_http_methods(['GET'])
def api_my_transfer_applications(request):
    user, role, error = require_api_user(request)
    if error:
        return error

    applications = (
        TransferApplication.objects
        .filter(student=user)
        .select_related('student', 'original_club', 'new_club')
        .order_by('-created_at')
    )
    return JsonResponse([serialize_transfer(application) for application in applications], safe=False)


@require_http_methods(['GET'])
def api_pending_transfer_applications(request):
    user, role, error = require_api_user(request)
    if error:
        return error

    choices = TransferApplication.StatusChoices
    query = Q(pk__in=[])
    if role == 'president':
        query = (
            Q(status=choices.PENDING_ORIGINAL_PRESIDENT, original_club__president=user)
            | Q(status=choices.PENDING_NEW_PRESIDENT, new_club__president=user)
        )
    elif role == 'teacher':
        query = (
            Q(status=choices.PENDING_ORIGINAL_TEACHER, original_club__teacher=user)
            | Q(status=choices.PENDING_NEW_TEACHER, new_club__teacher=user)
        )
    elif is_admin_role(role):
        query = Q(status=choices.PENDING_DISCIPLINE)

    applications = (
        TransferApplication.objects
        .filter(query)
        .select_related('student', 'original_club', 'new_club')
        .order_by('-created_at')
    )
    return JsonResponse([serialize_transfer(application) for application in applications], safe=False)


@require_http_methods(['POST'])
@csrf_exempt
def api_review_transfer_application(request, application_id):
    user, role, error = require_api_user(request)
    if error:
        return error

    try:
        data = parse_json_body(request)
    except json.JSONDecodeError:
        return json_error('資料格式錯誤。')

    action = data.get('action')
    if action not in {ApprovalLog.ActionChoices.APPROVED, ApprovalLog.ActionChoices.REJECTED}:
        return json_error('審核動作必須是核准或退回。')

    with transaction.atomic():
        application = (
            TransferApplication.objects
            .select_for_update()
            .select_related('student', 'original_club', 'new_club')
            .filter(id=application_id)
            .first()
        )
        if not application:
            return json_error('找不到轉社申請。', status=404)
        if not can_review_transfer_application(user, role, application):
            return json_error('您沒有權限審核此轉社申請。', status=403)

        ApprovalLog.objects.create(
            application=application,
            reviewer=user,
            action=action,
            comment=data.get('comment', ''),
        )

        if action == ApprovalLog.ActionChoices.REJECTED:
            application.status = TransferApplication.StatusChoices.REJECTED
        else:
            application.status = next_transfer_status(application)
            if application.status == TransferApplication.StatusChoices.APPROVED:
                apply_approved_transfer(application)
            if application.status in {
                TransferApplication.StatusChoices.PENDING_NEW_PRESIDENT,
                TransferApplication.StatusChoices.PENDING_NEW_TEACHER,
                TransferApplication.StatusChoices.PENDING_DISCIPLINE,
                TransferApplication.StatusChoices.APPROVED,
            }:
                application.is_original_club_approved = True

        application.save(update_fields=['status', 'is_original_club_approved', 'updated_at'])

    return JsonResponse({
        'success': True,
        'message': '轉社申請已完成審核。',
        'application': serialize_transfer(application),
    })


@require_http_methods(['GET'])
def api_transfer_logs(request):
    user, role, error = require_api_user(request)
    if error:
        return error
    if not is_admin_role(role):
        return json_error('只有管理員可以查看轉社紀錄。', status=403)

    transfers = (
        TransferApplication.objects
        .select_related('student', 'original_club', 'new_club')
        .prefetch_related('approval_logs__reviewer')
        .order_by('-created_at')
    )
    data = []
    for transfer in transfers:
        item = serialize_transfer(transfer)
        item['approval_logs'] = [
            serialize_approval_log(log)
            for log in transfer.approval_logs.all()
        ]
        data.append(item)
    return JsonResponse(data, safe=False)

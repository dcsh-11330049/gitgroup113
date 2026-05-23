from django.db import models


class User(models.Model):
    class RoleChoices(models.TextChoices):
        STUDENT = 'student', '學生'
        PRESIDENT = 'president', '社長'
        TEACHER = 'teacher', '老師'
        DISCIPLINE = 'discipline', '訓育組'

    student_id = models.CharField('學號', max_length=50, unique=True)
    password = models.CharField('密碼', max_length=128)
    name = models.CharField('姓名', max_length=100)
    class_number = models.CharField('班級座號', max_length=20)
    role = models.CharField('角色', max_length=20, choices=RoleChoices.choices, default=RoleChoices.STUDENT)
    email = models.EmailField('電子郵件', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.student_id})"


class Club(models.Model):
    club_name = models.CharField('社團名稱', max_length=100)
    max_capacity = models.PositiveIntegerField('人數上限')
    current_members = models.PositiveIntegerField('目前人數', default=0)
    president = models.ForeignKey(
        User,
        verbose_name='社長',
        related_name='presided_clubs',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    teacher = models.ForeignKey(
        User,
        verbose_name='指導老師',
        related_name='coached_clubs',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return self.club_name


class TransferApplication(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING_ORIGINAL_PRESIDENT = 'pending_original_president', '待原社長審核'
        PENDING_ORIGINAL_TEACHER = 'pending_original_teacher', '待原老師審核'
        PENDING_NEW_PRESIDENT = 'pending_new_president', '待新社長審核'
        PENDING_NEW_TEACHER = 'pending_new_teacher', '待新老師審核'
        PENDING_DISCIPLINE = 'pending_discipline', '待訓育組審核'
        NEW_CLUB_REJECTED = 'new_club_rejected', '新社團拒絕/額滿需重選'
        APPROVED = 'approved', '申請成功'
        REJECTED = 'rejected', '申請失敗'

    student = models.ForeignKey(
        User,
        verbose_name='申請學生',
        related_name='transfer_applications',
        on_delete=models.CASCADE,
    )
    original_club = models.ForeignKey(
        Club,
        verbose_name='原社團',
        related_name='original_applications',
        on_delete=models.CASCADE,
    )
    new_club = models.ForeignKey(
        Club,
        verbose_name='目標社團',
        related_name='new_applications',
        on_delete=models.CASCADE,
    )
    status = models.CharField('申請狀態', max_length=40, choices=StatusChoices.choices, default=StatusChoices.PENDING_ORIGINAL_PRESIDENT)
    is_original_club_approved = models.BooleanField('原社團已同意', default=False)
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    def __str__(self):
        return f"{self.student.name} -> {self.new_club.club_name} ({self.get_status_display()})"


class ApprovalLog(models.Model):
    class ActionChoices(models.TextChoices):
        APPROVED = 'approved', '同意'
        REJECTED = 'rejected', '拒絕'

    application = models.ForeignKey(
        TransferApplication,
        verbose_name='申請單',
        related_name='approval_logs',
        on_delete=models.CASCADE,
    )
    reviewer = models.ForeignKey(
        User,
        verbose_name='審核者',
        related_name='approval_logs',
        on_delete=models.CASCADE,
    )
    action = models.CharField('動作', max_length=20, choices=ActionChoices.choices)
    comment = models.TextField('備註', blank=True, null=True)
    created_at = models.DateTimeField('操作時間', auto_now_add=True)

    def __str__(self):
        return f"{self.application} - {self.reviewer.name} {self.get_action_display()}"


class SystemSettings(models.Model):
    transfer_start_date = models.DateTimeField('轉社開始時間', null=True, blank=True)
    transfer_end_date = models.DateTimeField('轉社結束時間', null=True, blank=True)

    class Meta:
        verbose_name = '系統設定'
        verbose_name_plural = '系統設定'

    def __str__(self):
        return '系統設定'


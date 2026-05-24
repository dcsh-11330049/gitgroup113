from django.db import models

class Student(models.Model):
    class RoleChoices(models.TextChoices):
        STUDENT = 'student', '學生'
        PRESIDENT = 'president', '社長'
        TEACHER = 'teacher', '老師'
        DISCIPLINE = 'discipline', '訓育組'
    user = models.OneToOneField('User', on_delete=models.CASCADE)
    student_id = models.CharField('學號', max_length=50, unique=True)
    class_number = models.CharField('班級座號', max_length=20)
    role = models.CharField('角色', max_length=20, choices=RoleChoices.choices, default=RoleChoices.STUDENT)

class Superviser(models.Model):
    class RoleChoices(models.TextChoices):
        PRESIDENT = 'president', '社長'
        DISCIPLINE = 'discipline', '訓育組'
    user = models.OneToOneField('User', on_delete=models.CASCADE)
    teacher_id = models.CharField('教師編號', max_length=50, unique=True)
    role = models.CharField('角色', max_length=20, choices=RoleChoices.choices, default=RoleChoices.DISCIPLINE)

class User(models.Model):
    username = models.CharField('登入名稱', max_length=50, unique=True, blank=True, null=True)
    password = models.CharField('密碼', max_length=128)
    name = models.CharField('姓名', max_length=100)
    email = models.EmailField('電子郵件', blank=True, null=True)

    def __str__(self):
        identifier = self.username or self.email or self.id
        return f"{self.name} ({identifier})"


class Club(models.Model):
    club_name = models.CharField('社團名稱', max_length=100)
    max_capacity = models.PositiveIntegerField('人數上限')
    current_members = models.PositiveIntegerField('目前人數', default=0)
    description = models.TextField('社團介紹', blank=True, null=True)
    description_url = models.URLField('社團介紹網址', blank=True, null=True)
    president = models.ForeignKey(
        User,
        verbose_name='社長',
        related_name='presided_clubs',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )
    teacher = models.ForeignKey(
        User,
        verbose_name='指導老師',
        related_name='coached_clubs',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
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
        on_delete=models.DO_NOTHING,
    )
    original_club = models.ForeignKey(
        Club,
        verbose_name='原社團',
        related_name='original_applications',
        on_delete=models.DO_NOTHING,
    )
    new_club = models.ForeignKey(
        Club,
        verbose_name='目標社團',
        related_name='new_applications',
        on_delete=models.DO_NOTHING,
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
        on_delete=models.DO_NOTHING,
    )
    reviewer = models.ForeignKey(
        User,
        verbose_name='審核者',
        related_name='approval_logs',
        on_delete=models.DO_NOTHING,
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


class ClubMembership(models.Model):
    """記錄學生所屬社團。"""
    club = models.ForeignKey(Club, verbose_name='社團', related_name='memberships', on_delete=models.CASCADE)
    student = models.ForeignKey(User, verbose_name='學生', related_name='club_memberships', on_delete=models.CASCADE)
    joined_at = models.DateTimeField('加入時間', auto_now_add=True)
    
    class Meta:
        unique_together = ('club', 'student')
        verbose_name = '社團成員'
        verbose_name_plural = '社團成員'
    
    def __str__(self):
        return f"{self.student.name} - {self.club.club_name}"


class ClubDescriptionModification(models.Model):
    """記錄待審核的社團介紹修改。"""
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', '待審核'
        APPROVED = 'approved', '已核准'
        REJECTED = 'rejected', '已退回'
    
    club = models.ForeignKey(Club, verbose_name='社團', related_name='description_modifications', on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(User, verbose_name='送出者', related_name='club_modifications', on_delete=models.CASCADE)
    description = models.TextField('社團介紹', blank=True, null=True)
    description_url = models.URLField('社團介紹網址', blank=True, null=True)
    status = models.CharField('狀態', max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    approved_by = models.ForeignKey(User, verbose_name='審核者', related_name='approved_modifications', 
                                    blank=True, null=True, on_delete=models.SET_NULL)
    approval_comment = models.TextField('審核備註', blank=True, null=True)
    created_at = models.DateTimeField('送出時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)
    
    class Meta:
        verbose_name = '社團描述修改'
        verbose_name_plural = '社團描述修改'
    
    def __str__(self):
        return f"{self.club.club_name} - {self.get_status_display()}"


class ClubDocument(models.Model):
    """儲存社團文件。"""
    club = models.ForeignKey(Club, verbose_name='社團', related_name='documents', on_delete=models.CASCADE)
    title = models.CharField('文件標題', max_length=200)
    file = models.FileField('文件', upload_to='club_documents/')
    uploaded_by = models.ForeignKey(User, verbose_name='上傳者', related_name='club_documents', on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField('上傳時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '社團文件'
        verbose_name_plural = '社團文件'
    
    def __str__(self):
        return f"{self.club.club_name} - {self.title}"


class ClubModificationDocument(models.Model):
    """社團介紹修改待審核時一併上傳的文件。"""
    modification = models.ForeignKey(
        ClubDescriptionModification,
        related_name='pending_documents',
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='club_description_modifications/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '待審核社團介紹文件'
        verbose_name_plural = '待審核社團介紹文件'

    def __str__(self):
        return f"{self.modification.club.club_name} - {self.title}"


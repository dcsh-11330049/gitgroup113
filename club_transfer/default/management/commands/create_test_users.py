from django.core.management.base import BaseCommand
from default.models import User, Student, Superviser


class Command(BaseCommand):
    help = 'Create test users for different roles'

    def handle(self, *args, **options):
        # Test data
        test_users = [
            {
                'username': 'student001',
                'password': 'password123',
                'name': '王小明',
                'email': 'student001@school.edu',
                'type': 'student',
                'student_id': '001',
                'class_number': '201-05'
            },
            {
                'username': 'president001',
                'password': 'password123',
                'name': '李社長',
                'email': 'president001@school.edu',
                'type': 'president',
                'student_id': '002',
                'class_number': '301-10'
            },
            {
                'username': 'teacher001',
                'password': 'password123',
                'name': '張老師',
                'email': 'teacher001@school.edu',
                'type': 'teacher',
                'teacher_id': 'T001'
            },
            {
                'username': 'admin001',
                'password': 'password123',
                'name': '訓育組長',
                'email': 'admin001@school.edu',
                'type': 'admin',
                'teacher_id': 'T002'
            }
        ]

        for user_data in test_users:
            username = user_data['username']
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'User {username} already exists, skipping...'))
                continue
            
            # Create User
            user = User.objects.create(
                username=username,
                password=user_data['password'],
                name=user_data['name'],
                email=user_data['email']
            )
            self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
            
            # Create Student or Superviser record based on type
            if user_data['type'] == 'student':
                Student.objects.create(
                    user=user,
                    student_id=user_data['student_id'],
                    class_number=user_data['class_number'],
                    role='student'
                )
                self.stdout.write(self.style.SUCCESS(f'  └─ Created Student: {user_data["name"]}'))
            
            elif user_data['type'] == 'president':
                Student.objects.create(
                    user=user,
                    student_id=user_data['student_id'],
                    class_number=user_data['class_number'],
                    role='president'
                )
                self.stdout.write(self.style.SUCCESS(f'  └─ Created President: {user_data["name"]}'))
            
            elif user_data['type'] == 'teacher':
                Superviser.objects.create(
                    user=user,
                    teacher_id=user_data['teacher_id'],
                    role='teacher'
                )
                self.stdout.write(self.style.SUCCESS(f'  └─ Created Teacher: {user_data["name"]}'))
            
            elif user_data['type'] == 'admin':
                Superviser.objects.create(
                    user=user,
                    teacher_id=user_data['teacher_id'],
                    role='discipline'
                )
                self.stdout.write(self.style.SUCCESS(f'  └─ Created Administrator: {user_data["name"]}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Test users created successfully!'))
        self.stdout.write('\n📝 Test Accounts:')
        self.stdout.write('=' * 60)
        self.stdout.write('帳號\t\t密碼\t\t角色')
        self.stdout.write('-' * 60)
        self.stdout.write('student001\tpassword123\t學生')
        self.stdout.write('president001\tpassword123\t社長')
        self.stdout.write('teacher001\tpassword123\t老師')
        self.stdout.write('admin001\tpassword123\t管理員')
        self.stdout.write('=' * 60)

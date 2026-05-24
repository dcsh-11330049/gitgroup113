from django.core.management.base import BaseCommand
from default.models import User, Club
import random


class Command(BaseCommand):
    help = 'Assign club presidents and teachers'

    def handle(self, *args, **options):
        # Chinese names for students and teachers
        student_first_names = ['王', '李', '張', '劉', '陳', '楊', '黃', '趙', '吳', '周', '徐', '孫', '馬', '朱', '林']
        student_last_names = ['怡', '俊', '佳', '芷', '品', '昱', '鈞', '浩', '毅', '庭', '安', '晴', '柔', '翔', '祐']
        teacher_first_names = ['黃', '李', '王', '陳', '張', '劉', '楊', '吳', '周', '林']
        teacher_last_names = ['老師', '先生', '老闆', '校長', '主任', '組長', '師傅', '教授']

        # Create student users with Chinese names if they don't exist
        students = []
        for i in range(100):
            first = random.choice(student_first_names)
            last = random.choice(student_last_names)
            name = first + last
            student_id = f"STU{i:04d}"
            student, created = User.objects.get_or_create(
                student_id=student_id,
                defaults={
                    'password': 'default',
                    'name': name,
                    'class_number': '101',
                    'role': User.RoleChoices.STUDENT,
                }
            )
            if created:
                student.name = name
                student.save()
            students.append(student)

        # Create teacher users with Chinese names if they don't exist
        teachers = []
        for i in range(30):
            first = random.choice(teacher_first_names)
            last = random.choice(teacher_last_names)
            name = first + last
            teacher_id = f"TCH{i:04d}"
            teacher, created = User.objects.get_or_create(
                student_id=teacher_id,
                defaults={
                    'password': 'default',
                    'name': name,
                    'class_number': '教室',
                    'role': User.RoleChoices.TEACHER,
                }
            )
            if created:
                teacher.name = name
                teacher.save()
            teachers.append(teacher)

        # Get all clubs
        all_clubs = list(Club.objects.all())
        total_clubs = len(all_clubs)

        # Assign presidents to 90% of clubs
        president_count = int(total_clubs * 0.9)
        clubs_for_presidents = random.sample(all_clubs, president_count)
        random.shuffle(students)
        
        for idx, club in enumerate(clubs_for_presidents):
            club.president = students[idx % len(students)]
            club.save()

        self.stdout.write(self.style.SUCCESS(f'✓ Assigned {president_count} presidents to clubs'))

        # Assign teachers to 80% of clubs
        teacher_count = int(total_clubs * 0.8)
        clubs_for_teachers = random.sample(all_clubs, teacher_count)
        random.shuffle(teachers)
        
        for idx, club in enumerate(clubs_for_teachers):
            club.teacher = teachers[idx % len(teachers)]
            club.save()

        self.stdout.write(self.style.SUCCESS(f'✓ Assigned {teacher_count} teachers to clubs'))
        self.stdout.write(self.style.SUCCESS('Done! Club leaders assigned successfully.'))

from django.core.management.base import BaseCommand
from default.models import User, Student, Club
import random


class Command(BaseCommand):
    help = 'Create Student records for existing users'

    def handle(self, *args, **options):
        users = User.objects.all()
        clubs = Club.objects.all()

        self.stdout.write(f'Found {users.count()} users and {clubs.count()} clubs')

        if not clubs:
            self.stdout.write(self.style.ERROR('No clubs found! Run populate_data first.'))
            return

        created_count = 0
        for idx, user in enumerate(users):
            if not Student.objects.filter(user=user).exists():
                student_id = f"STU{idx:05d}"
                class_num = f"10{(idx % 10) + 1}"
                
                Student.objects.create(
                    user=user,
                    student_id=student_id,
                    class_number=class_num,
                    role=Student.RoleChoices.STUDENT,
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Created {created_count} Student records'))
        
        # Show how many students and clubs we have
        total_students = Student.objects.count()
        total_clubs = Club.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Total: {total_students} students, {total_clubs} clubs'))

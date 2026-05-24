from django.core.management.base import BaseCommand
from default.models import User, Club, Student, TransferApplication
import random


class Command(BaseCommand):
    help = 'Randomly assign students to clubs'

    def handle(self, *args, **options):
        # Get all students
        students = list(Student.objects.all())
        clubs = list(Club.objects.all())

        if not students or not clubs:
            self.stdout.write(self.style.ERROR('No students or clubs found!'))
            return

        assigned_count = 0

        for student in students:
            # Get available clubs (that haven't reached capacity or have no limit)
            available_clubs = [
                club for club in clubs
                if club.max_capacity == 0 or club.current_members < club.max_capacity
            ]

            if not available_clubs:
                self.stdout.write(self.style.WARNING(f'⚠ No available clubs for {student.user.name}'))
                continue

            # Randomly pick a club
            selected_club = random.choice(available_clubs)

            # Pick a random original club (for the transfer application)
            original_club = random.choice(clubs)

            # Create transfer application as approved
            application, created = TransferApplication.objects.get_or_create(
                student=student.user,
                new_club=selected_club,
                defaults={
                    'original_club': original_club,
                    'status': TransferApplication.StatusChoices.APPROVED,
                    'is_original_club_approved': True,
                }
            )

            if created:
                # Update current_members only if newly created
                selected_club.current_members += 1
                selected_club.save()
                assigned_count += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Assigned {assigned_count} students to clubs'))
        self.stdout.write(self.style.SUCCESS('Done!'))

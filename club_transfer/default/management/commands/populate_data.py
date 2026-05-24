from django.core.management.base import BaseCommand
from default.models import User, Club


class Command(BaseCommand):
    help = 'Populate database with students and clubs'

    def handle(self, *args, **options):
        # Create students from classes 101~110, 201~210, 301~310
        classes = list(range(101, 111)) + list(range(201, 211)) + list(range(301, 311))
        
        for class_number in classes:
            for student_num in range(1, 31):  # ~30 students per class
                student_id = f"{class_number}{student_num:02d}"
                if not User.objects.filter(student_id=student_id).exists():
                    User.objects.create(
                        student_id=student_id,
                        password='default_password',
                        name=f'Student {student_id}',
                        class_number=str(class_number),
                        role=User.RoleChoices.STUDENT,
                    )
        
        self.stdout.write(self.style.SUCCESS('✓ Created students'))

        # Club data: (name, max_capacity)
        clubs_data = [
            ('班聯會', 0),
            ('大眾傳播社', 60),
            ('新媒體創業社', 60),
            ('熱舞社', 50),
            ('大直青年', 20),
            ('漫研社', 60),
            ('排球社', 60),
            ('食作社', 36),
            ('管樂社', 30),
            ('科學研究社', 40),
            ('籃球社', 70),
            ('網球社', 0),
            ('畢業聯合會', 0),
            ('攝影社', 23),
            ('英研社', 40),
            ('藍十字會', 60),
            ('資訊社', 30),
            ('棒球', 25),
            ('吉他社', 70),
            ('電影欣賞社', 40),
            ('演辯社', 20),
            ('桌遊社', 60),
            ('嘻哈社', 50),
            ('樂研社', 35),
            ('女籃隊', 0),
            ('羽球社', 50),
            ('塔羅社', 0),
            ('韓國文化研究社', 0),
            ('生物研究社', 0),
            ('手作社', 0),
            ('機器人社', 0),
        ]

        for club_name, max_capacity in clubs_data:
            if not Club.objects.filter(club_name=club_name).exists():
                Club.objects.create(
                    club_name=club_name,
                    max_capacity=max_capacity,
                    current_members=0,
                )

        self.stdout.write(self.style.SUCCESS('✓ Created clubs'))
        self.stdout.write(self.style.SUCCESS('Done! Database populated successfully.'))

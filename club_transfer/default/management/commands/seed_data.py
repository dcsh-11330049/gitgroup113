from django.core.management.base import BaseCommand
from default.models import *
import random


class Command(BaseCommand):
    help = 'Create test data'

    def handle(self, *args, **kwargs):
        # Clear old data
        ApprovalLog.objects.all().delete()
        TransferApplication.objects.all().delete()
        ClubMembership.objects.all().delete()
        ClubModificationDocument.objects.all().delete()
        ClubDescriptionModification.objects.all().delete()
        ClubDocument.objects.all().delete()
        Club.objects.all().delete()
        Student.objects.all().delete()
        Superviser.objects.all().delete()
        User.objects.all().delete()

        chinese_names = [
            '王小明', '李志豪', '陳冠宇', '林子豪', '張宇翔',
            '黃柏翰', '吳俊傑', '蔡承恩', '劉家豪', '楊宗緯',
            '許庭瑋', '鄭凱文', '謝明軒', '郭建宏', '何柏廷'
        ]

        teacher_names = [
            '陳美玲', '林淑芬', '黃建國', '張雅婷', '王志成'
        ]

        club_names = [
            '熱音社',
            '籃球社',
            '動漫社',
            '資訊社',
            '吉他社'
        ]

        clubs = []

        # Create clubs first
        for club_name in club_names:
            club = Club.objects.create(
                club_name=club_name,
                max_capacity=20,
                description=f'{club_name}介紹',
            )
            clubs.append(club)

        # Create teachers
        self.stdout.write(self.style.SUCCESS('Test data created successfully.'))
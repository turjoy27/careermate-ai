from django.core.management.base import BaseCommand
from apps.roadmaps.models import LearningResource


class Command(BaseCommand):
    help = "Seeds curated industry learning resources for CareerMate AI."

    def handle(self, *args, **options):
        resources = [
            {
                'title': 'Official Python Documentation & Tutorial',
                'category': 'Python & Backend',
                'resource_type': 'documentation',
                'difficulty': 'beginner',
                'url': 'https://docs.python.org/3/tutorial/',
                'description': 'The authoritative guide to Python 3 syntax, standard library, and data structures.',
                'is_free': True,
                'is_featured': True,
            },
            {
                'title': 'Django Girls Tutorial & Architecture Overview',
                'category': 'Python & Backend',
                'resource_type': 'course',
                'difficulty': 'beginner',
                'url': 'https://tutorial.djangogirls.org/',
                'description': 'A friendly, thorough walkthrough to building web applications using the Django web framework.',
                'is_free': True,
                'is_featured': True,
            },
            {
                'title': 'Django REST Framework Official Tutorial',
                'category': 'Python & Backend',
                'resource_type': 'documentation',
                'difficulty': 'intermediate',
                'url': 'https://www.django-rest-framework.org/tutorial/quickstart/',
                'description': 'Hands-on guide to building flexible, production-grade Web APIs with serializers and viewsets.',
                'is_free': True,
                'is_featured': True,
            },
            {
                'title': 'MDN Web Docs — Frontend JavaScript & Modern Web',
                'category': 'Frontend & Web',
                'resource_type': 'documentation',
                'difficulty': 'beginner',
                'url': 'https://developer.mozilla.org/en-US/docs/Learn',
                'description': 'Industry gold-standard web development documentation covering HTML, CSS, JavaScript, and accessibility.',
                'is_free': True,
                'is_featured': True,
            },
            {
                'title': 'Full Stack Open — Deep Dive into Modern Web Development',
                'category': 'Frontend & Web',
                'resource_type': 'course',
                'difficulty': 'intermediate',
                'url': 'https://fullstackopen.com/en/',
                'description': 'University of Helsinki free course on React, Redux, Node.js, REST APIs, and TypeScript.',
                'is_free': True,
                'is_featured': True,
            },
            {
                'title': 'Docker for Beginners — Hands-on DevOps Guide',
                'category': 'DevOps & Cloud',
                'resource_type': 'video',
                'difficulty': 'beginner',
                'url': 'https://docker-curriculum.com/',
                'description': 'Learn containerization, Dockerfiles, docker-compose, and multi-service deployment.',
                'is_free': True,
                'is_featured': True,
            },
            {
                'title': 'SQLBolt — Interactive Lessons in Relational Databases',
                'category': 'Databases & SQL',
                'resource_type': 'course',
                'difficulty': 'beginner',
                'url': 'https://sqlbolt.com/',
                'description': 'Interactive in-browser queries covering SELECT, JOINs, aggregations, and MySQL relational schemas.',
                'is_free': True,
                'is_featured': True,
            },
            {
                'title': 'Tech Interview Handbook — System Design & Behavioral Prep',
                'category': 'Interview Prep',
                'resource_type': 'article',
                'difficulty': 'intermediate',
                'url': 'https://www.techinterviewhandbook.org/',
                'description': 'Curated coding interview preparation, behavioral questions rubric, and resume checklists.',
                'is_free': True,
                'is_featured': True,
            },
        ]

        count = 0
        for r_data in resources:
            obj, created = LearningResource.objects.get_or_create(
                title=r_data['title'],
                defaults=r_data
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} curated learning resources."))

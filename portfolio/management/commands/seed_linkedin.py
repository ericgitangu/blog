"""
Seed blog posts from LinkedIn data export.

LinkedIn export contains CSV files with professional profile data.
Export from: LinkedIn Settings > Data Privacy > Get a copy of your data

Usage:
    python manage.py seed_linkedin --dir /path/to/linkedin_export/
"""
import csv
import os
from datetime import datetime, timezone as dt_timezone
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from portfolio.models import Post, Author, Tag


class Command(BaseCommand):
    help = 'Seed blog posts from LinkedIn data export directory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir',
            type=str,
            required=True,
            help='Path to LinkedIn export directory'
        )
        parser.add_argument(
            '--author-first',
            type=str,
            default='Eric',
            help='Author first name'
        )
        parser.add_argument(
            '--author-last',
            type=str,
            default='Gitangu',
            help='Author last name'
        )
        parser.add_argument(
            '--author-email',
            type=str,
            default='developer.ericgitangu@gmail.com',
            help='Author email'
        )

    def read_csv(self, filepath):
        """Read a CSV file and return list of dictionaries."""
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return list(csv.DictReader(f))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not read {filepath}: {e}'))
            return []

    def parse_date(self, date_str, default_day=1):
        """Parse various date formats from LinkedIn export."""
        if not date_str or date_str.strip() == '':
            return None

        date_str = date_str.strip()

        # Try various formats
        formats = [
            '%Y-%m-%d %H:%M:%S UTC',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S UTC',
            '%Y-%m-%d',
            '%b %Y',  # "Sep 2022"
            '%B %Y',  # "September 2022"
            '%Y',     # Just year
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return timezone.make_aware(dt, dt_timezone.utc)
            except ValueError:
                continue

        return None

    def create_post(self, author, title, content, date, tags_list, slug_base=None):
        """Create a post with unique slug."""
        if not slug_base:
            slug_base = slugify(title)[:80]

        slug = slug_base
        counter = 1
        while Post.objects.filter(slug=slug).exists():
            slug = f'{slug_base}-{counter}'
            counter += 1

        # Create excerpt from content (max 197 chars to leave room for ...)
        # Keep markdown - it will be rendered by the template filter
        excerpt_content = content.replace('\n', ' ').replace('  ', ' ').strip()
        if len(excerpt_content) > 197:
            excerpt = excerpt_content[:197] + '...'
        else:
            excerpt = excerpt_content

        post = Post.objects.create(
            title=title,
            slug=slug,
            content=content,
            date=date or timezone.now(),
            excerpt=excerpt,
            author=author,
        )

        # Add tags
        for tag_name in tags_list:
            tag, _ = Tag.objects.get_or_create(caption=tag_name.lower()[:20])
            post.tags.add(tag)

        return post

    def seed_positions(self, author, data_dir):
        """Create posts from career positions."""
        positions = self.read_csv(os.path.join(data_dir, 'Positions.csv'))
        created = 0

        for pos in positions:
            company = pos.get('Company Name', '').strip()
            title_role = pos.get('Title', '').strip()
            description = pos.get('Description', '').strip()
            location = pos.get('Location', '').strip()
            started = pos.get('Started On', '')
            finished = pos.get('Finished On', '')

            if not description or len(description) < 50:
                continue

            # Build post title
            post_title = f"{title_role} at {company}"

            # Build content
            content_parts = [f"## {title_role}\n**{company}**"]
            if location:
                content_parts.append(f"*{location}*")

            date_range = started
            if finished:
                date_range = f"{started} - {finished}"
            elif started:
                date_range = f"{started} - Present"
            if date_range:
                content_parts.append(f"\n**Period:** {date_range}\n")

            content_parts.append(f"\n{description}")

            content = '\n'.join(content_parts)

            # Parse start date
            post_date = self.parse_date(started)

            # Tags based on role
            tags = ['career', 'experience']
            if 'lead' in title_role.lower() or 'director' in title_role.lower():
                tags.append('leadership')
            if 'engineer' in title_role.lower():
                tags.append('engineering')

            self.create_post(author, post_title, content, post_date, tags)
            self.stdout.write(f'  Created position post: {post_title[:50]}...')
            created += 1

        return created

    def seed_certifications(self, author, data_dir):
        """Create posts from certifications grouped by topic."""
        certs = self.read_csv(os.path.join(data_dir, 'Certifications.csv'))
        if not certs:
            return 0

        # Group certifications by topic/authority
        groups = {
            'rust': [],
            'python': [],
            'java': [],
            'javascript': [],
            'react': [],
            'blockchain': [],
            'kubernetes': [],
            'aws': [],
            'django': [],
            'go': [],
            'android': [],
            'ai-ml': [],
            'security': [],
            'other': [],
        }

        for cert in certs:
            name = cert.get('Name', '').lower()
            cert_data = {
                'name': cert.get('Name', ''),
                'url': cert.get('Url', ''),
                'authority': cert.get('Authority', ''),
                'date': cert.get('Finished On', cert.get('Started On', '')),
                'license': cert.get('License Number', ''),
            }

            if 'rust' in name:
                groups['rust'].append(cert_data)
            elif 'python' in name or 'django' in name:
                if 'django' in name:
                    groups['django'].append(cert_data)
                else:
                    groups['python'].append(cert_data)
            elif 'java' in name and 'javascript' not in name:
                groups['java'].append(cert_data)
            elif 'javascript' in name or 'js' in name or 'node' in name:
                groups['javascript'].append(cert_data)
            elif 'react' in name:
                groups['react'].append(cert_data)
            elif 'blockchain' in name or 'smart contract' in name or 'dapp' in name or 'ethereum' in name:
                groups['blockchain'].append(cert_data)
            elif 'kubernetes' in name or 'k8s' in name or 'docker' in name or 'microservice' in name:
                groups['kubernetes'].append(cert_data)
            elif 'aws' in name or 'amazon' in name:
                groups['aws'].append(cert_data)
            elif 'go ' in name or 'golang' in name or name.startswith('go'):
                groups['go'].append(cert_data)
            elif 'android' in name or 'kotlin' in name or 'mobile' in name:
                groups['android'].append(cert_data)
            elif 'ai' in name or 'ml' in name or 'machine learning' in name or 'tensorflow' in name or 'deep learning' in name or 'gan' in name:
                groups['ai-ml'].append(cert_data)
            elif 'security' in name or 'hacking' in name or 'cyber' in name:
                groups['security'].append(cert_data)
            else:
                groups['other'].append(cert_data)

        created = 0
        topic_titles = {
            'rust': 'Rust Programming Certifications',
            'python': 'Python Development Certifications',
            'java': 'Java Programming Certifications',
            'javascript': 'JavaScript & Node.js Certifications',
            'react': 'React Development Certifications',
            'blockchain': 'Blockchain & Web3 Certifications',
            'kubernetes': 'Kubernetes & DevOps Certifications',
            'aws': 'AWS Cloud Certifications',
            'django': 'Django Framework Certifications',
            'go': 'Go Programming Certifications',
            'android': 'Android & Mobile Development Certifications',
            'ai-ml': 'AI & Machine Learning Certifications',
            'security': 'Cybersecurity Certifications',
            'other': 'Additional Technical Certifications',
        }

        for topic, cert_list in groups.items():
            if not cert_list:
                continue

            title = topic_titles.get(topic, f'{topic.title()} Certifications')

            content_parts = [f"## {title}\n"]
            content_parts.append(f"A collection of {len(cert_list)} certifications in {topic.replace('-', '/')}.\n")

            for c in cert_list:
                cert_line = f"### {c['name']}"
                content_parts.append(cert_line)
                if c['authority']:
                    content_parts.append(f"**Issued by:** {c['authority']}")
                if c['date']:
                    content_parts.append(f"**Date:** {c['date']}")
                if c['url']:
                    content_parts.append(f"[View Certificate]({c['url']})")
                content_parts.append("")

            content = '\n'.join(content_parts)

            # Use most recent date
            dates = [self.parse_date(c['date']) for c in cert_list if c['date']]
            post_date = max(dates) if dates else timezone.now()

            tags = ['certifications', topic.replace('-', '')]
            self.create_post(author, title, content, post_date, tags)
            self.stdout.write(f'  Created certification post: {title}')
            created += 1

        return created

    def seed_projects(self, author, data_dir):
        """Create posts from projects."""
        projects = self.read_csv(os.path.join(data_dir, 'Projects.csv'))
        created = 0

        for proj in projects:
            title = proj.get('Title', '').strip()
            description = proj.get('Description', '').strip()
            url = proj.get('Url', '').strip()
            started = proj.get('Started On', '')
            finished = proj.get('Finished On', '')

            if not title or not description or len(description) < 50:
                continue

            content_parts = [f"## {title}\n"]

            date_range = started
            if finished:
                date_range = f"{started} - {finished}"
            elif started:
                date_range = f"{started} - Present"
            if date_range:
                content_parts.append(f"**Period:** {date_range}\n")

            content_parts.append(description)

            if url:
                content_parts.append(f"\n**Project Link:** [{url}]({url})")

            content = '\n'.join(content_parts)

            post_date = self.parse_date(started)

            # Extract tags from description
            tags = ['project']
            desc_lower = description.lower()
            if 'react' in desc_lower or 'nextjs' in desc_lower or 'next.js' in desc_lower:
                tags.append('react')
            if 'django' in desc_lower:
                tags.append('django')
            if 'blockchain' in desc_lower or 'web3' in desc_lower or 'crypto' in desc_lower:
                tags.append('blockchain')
            if 'aws' in desc_lower or 'azure' in desc_lower or 'cloud' in desc_lower:
                tags.append('cloud')
            if 'ai' in desc_lower or 'ml' in desc_lower:
                tags.append('ai')

            self.create_post(author, title, content, post_date, tags)
            self.stdout.write(f'  Created project post: {title[:50]}...')
            created += 1

        return created

    def seed_skills_summary(self, author, data_dir):
        """Create a skills overview post."""
        skills = self.read_csv(os.path.join(data_dir, 'Skills.csv'))
        if not skills:
            return 0

        # Categorize skills
        categories = {
            'languages': [],
            'frameworks': [],
            'cloud': [],
            'databases': [],
            'devops': [],
            'ai-ml': [],
            'other': [],
        }

        lang_keywords = ['python', 'java', 'rust', 'go', 'c++', 'javascript', 'php', 'elixir', 'kotlin', 'solidity']
        framework_keywords = ['react', 'angular', 'django', 'spring', 'node', 'express', 'next', 'phoenix', 'axum']
        cloud_keywords = ['aws', 'azure', 'gcp', 'google cloud', 'lambda', 'ec2']
        db_keywords = ['sql', 'nosql', 'postgres', 'mongo', 'redis', 'bigquery']
        devops_keywords = ['docker', 'kubernetes', 'ci/cd', 'devops', 'jenkins', 'gitlab', 'terraform']
        ai_keywords = ['machine learning', 'ai', 'nlp', 'tensorflow', 'mlops', 'llm', 'deep learning']

        for skill in skills:
            name = skill.get('Name', '').strip()
            name_lower = name.lower()

            if any(kw in name_lower for kw in lang_keywords):
                categories['languages'].append(name)
            elif any(kw in name_lower for kw in framework_keywords):
                categories['frameworks'].append(name)
            elif any(kw in name_lower for kw in cloud_keywords):
                categories['cloud'].append(name)
            elif any(kw in name_lower for kw in db_keywords):
                categories['databases'].append(name)
            elif any(kw in name_lower for kw in devops_keywords):
                categories['devops'].append(name)
            elif any(kw in name_lower for kw in ai_keywords):
                categories['ai-ml'].append(name)
            else:
                categories['other'].append(name)

        content_parts = ["## Technical Skills Overview\n"]
        content_parts.append(f"A comprehensive overview of {len(skills)} technical skills.\n")

        category_titles = {
            'languages': 'Programming Languages',
            'frameworks': 'Frameworks & Libraries',
            'cloud': 'Cloud Platforms',
            'databases': 'Databases',
            'devops': 'DevOps & Infrastructure',
            'ai-ml': 'AI & Machine Learning',
            'other': 'Other Technologies',
        }

        for cat, skill_list in categories.items():
            if skill_list:
                content_parts.append(f"### {category_titles[cat]}")
                content_parts.append(', '.join(skill_list))
                content_parts.append("")

        content = '\n'.join(content_parts)

        self.create_post(author, "Technical Skills & Expertise", content, timezone.now(), ['skills', 'expertise'])
        self.stdout.write('  Created skills overview post')
        return 1

    def seed_education(self, author, data_dir):
        """Create education post."""
        education = self.read_csv(os.path.join(data_dir, 'Education.csv'))
        if not education:
            return 0

        content_parts = ["## Educational Background\n"]

        for edu in education:
            school = edu.get('School Name', '')
            degree = edu.get('Degree Name', '')
            notes = edu.get('Notes', '')
            activities = edu.get('Activities', '')
            start = edu.get('Start Date', '')
            end = edu.get('End Date', '')

            content_parts.append(f"### {school}")
            if degree:
                content_parts.append(f"**Degree:** {degree}")
            if notes:
                content_parts.append(f"**Focus:** {notes}")
            if start and end:
                content_parts.append(f"**Period:** {start} - {end}")
            if activities:
                content_parts.append(f"**Activities:** {activities}")
            content_parts.append("")

        # Add honors
        honors = self.read_csv(os.path.join(data_dir, 'Honors.csv'))
        if honors:
            content_parts.append("### Honors & Awards\n")
            for honor in honors:
                title = honor.get('Title', '')
                desc = honor.get('Description', '')
                issued = honor.get('Issued On', '')

                content_parts.append(f"**{title}**")
                if desc:
                    content_parts.append(desc)
                if issued:
                    content_parts.append(f"*{issued}*")
                content_parts.append("")

        content = '\n'.join(content_parts)

        post_date = self.parse_date(education[0].get('End Date', '')) if education else timezone.now()

        self.create_post(author, "Education & Academic Achievements", content, post_date, ['education', 'academic'])
        self.stdout.write('  Created education post')
        return 1

    def seed_about(self, author, data_dir):
        """Create about/profile post."""
        profiles = self.read_csv(os.path.join(data_dir, 'Profile.csv'))
        if not profiles:
            return 0

        profile = profiles[0]
        headline = profile.get('Headline', '')
        summary = profile.get('Summary', '')

        if not summary:
            return 0

        content_parts = ["## About Me\n"]
        if headline:
            content_parts.append(f"*{headline}*\n")
        content_parts.append(summary.replace('&amp;', '&'))

        content = '\n'.join(content_parts)

        self.create_post(author, "About Eric Gitangu", content, timezone.now(), ['about', 'introduction'])
        self.stdout.write('  Created about post')
        return 1

    def handle(self, *args, **options):
        data_dir = options['dir']

        if not os.path.isdir(data_dir):
            self.stdout.write(self.style.ERROR(f'Directory not found: {data_dir}'))
            return

        # Get or create author
        author, created = Author.objects.get_or_create(
            email=options['author_email'],
            defaults={
                'first_name': options['author_first'],
                'last_name': options['author_last'],
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created author: {author}'))
        else:
            self.stdout.write(f'Using existing author: {author}')

        self.stdout.write('\nSeeding posts from LinkedIn data...\n')

        total = 0

        # Seed about
        self.stdout.write('Processing Profile...')
        total += self.seed_about(author, data_dir)

        # Seed education
        self.stdout.write('Processing Education...')
        total += self.seed_education(author, data_dir)

        # Seed positions
        self.stdout.write('Processing Positions...')
        total += self.seed_positions(author, data_dir)

        # Seed projects
        self.stdout.write('Processing Projects...')
        total += self.seed_projects(author, data_dir)

        # Seed certifications
        self.stdout.write('Processing Certifications...')
        total += self.seed_certifications(author, data_dir)

        # Seed skills
        self.stdout.write('Processing Skills...')
        total += self.seed_skills_summary(author, data_dir)

        self.stdout.write(self.style.SUCCESS(f'\nDone! Created {total} posts'))
        self.stdout.write(f'Total posts in database: {Post.objects.count()}')

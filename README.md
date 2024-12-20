# Eric Gitangu's Tech Blog
<div align="center">
    <a href="https://developer.ericgitangu.com">
        <img src="https://developer.ericgitangu.com/_next/image?url=%2Ffavicon.png&w=96&q=75" style="border-radius: 50%" alt="deveric.io logo"/>
        <h1 align="center">Eric Gitangu</h1>
    </a>
A Django-powered blog showcasing insights in technology, cybersecurity, and software development. Built with Python and Django, featuring Azure cloud integration and robust security measures.

</div>

## 🚀 Features

- **Dynamic Content Management**: Built-in Django admin interface for content creation
- **Cloud Storage Integration**: Azure Blob Storage for media and static files
- **Production-Ready**: Configured for production with security best practices
- **PostgreSQL Database**: Robust data storage with PostgreSQL
- **Secure Authentication**: Comprehensive password validation and security middleware
- **Logging System**: Detailed debug logging for monitoring and troubleshooting

## 🛠️ Tech Stack

### Backend Framework ⚙️
- Django 4.x
- Python 3.11
- WSGI Application Server

### Database 🗄️
- PostgreSQL with psycopg2-binary driver
- Environment-based configuration

### Cloud Services ☁️ (Azure)
- Azure Web Apps for hosting
- Azure Blob Storage for static/media files
- Azure Managed Identity authentication
- Azure PostgreSQL database

## 💾 Storage Configuration
- Whitenoise
- PostgresSQL (Azure flexible)

### 📊 Monitoring and Logging

Debug logging configured for production monitoring:
- File handler
- Console handler
- App-level logging - Default DEBUG

### 🔒 Security Configuration

- **CSRF Protection**: Configured for production domains
- **Secure Middleware Stack**:
  - Security Middleware
  - WhiteNoise for static files
  - Session Management
  - CSRF Protection
  - Authentication
  - XFrame Options

### 🚀 Production Deployment

The application uses GitHub Actions for CI/CD to Azure Web Apps. The deployment process includes:
- Automated testing
- Static file collection
- Database migrations
- Zero-downtime deployment
- Azure Blob Storage configuration
- Secure environment variable management

For more details, see the deployment workflow in `.github/workflows/main_deveric-blog.yml`.

## 🔗 Connect

- **Website**: [developer.ericgitangu.com](https://developer.ericgitangu.com)
- **LinkedIn**: [Eric Gitangu](https://linkedin.com/in/ericgitangu)
- **Azure Blog**: [deveric-blog.azurewebsites.net](https://deveric-blog.azurewebsites.net)

## 📄 License

This project is licensed under the MIT License.
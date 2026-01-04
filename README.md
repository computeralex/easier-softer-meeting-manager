# Easier Softer Meeting Manager

A Django application for managing 12-step recovery meetings.

## Features

- **Meeting Format Builder** - Create and customize meeting scripts with drag-and-drop blocks
- **Readings Library** - Store and organize recovery literature and readings
- **Phone List** - Manage member contact lists with PDF export
- **Treasurer Tools** - Track income, expenses, and generate financial reports
- **Business Meeting** - Record motions, votes, and meeting minutes
- **Public Website** - Optional public-facing site for your group
- **User Management** - Role-based access with service positions (Secretary, Treasurer, GSR, etc.)

## Deploy Your Own

### One-Click Deploy to Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/ol2C36?referralCode=4umFz5)

*Note: This link includes a referral code - we may receive hosting credits or something if you sign up, but it does not change your cost. You can always [deploy manually](#manual-deploy) without the template.*

**Requirements:** Railway Hobby plan ($5/month) or higher for PostgreSQL database.

Click the button above and Railway will:
- Clone the repository
- Set up a PostgreSQL database
- Auto-generate your SECRET_KEY
- Deploy the app

### Manual Deploy

If you prefer to deploy manually:

1. Fork this repository
2. Create a new project on [Railway](https://railway.com)
3. Add a PostgreSQL database to your project
4. Add a new service from your forked repo
5. Set the `SECRET_KEY` environment variable:
   - Generate one with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
6. Link the `DATABASE_URL` variable from your Postgres service
7. Deploy!

### After Deployment

Create your admin account:

1. In Railway, right-click on your **web service** → **Copy SSH Command**
2. Open your terminal (or PuTTY on Windows) and paste the command to connect
3. Once connected, run:
   ```bash
   export LD_LIBRARY_PATH=/root/.nix-profile/lib:$LD_LIBRARY_PATH && /opt/venv/bin/python manage.py createsuperuser
   ```
4. Enter your email and password when prompted
5. Visit `your-app-url.up.railway.app` and log in with your new account

## Hosted Version

Don't want to manage your own server? Visit [recoverymeeting.app](https://recoverymeeting.app) for a fully managed hosted version.

## Development Tools

- VS Code
- GitHub
- Grok by xAI
- Brave Browser
- Python & Django
- uv (package manager)
- macOS
- Keyboard & Mouse
- Coffee

## License

GPL-2.0 - See LICENSE file for details.

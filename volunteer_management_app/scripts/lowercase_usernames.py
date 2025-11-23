from django.contrib.auth import get_user_model

def lowercase_usernames():
    User = get_user_model()
    users = User.objects.all()
    for user in users:
        username_lower = user.username.lower()
        if user.username != username_lower:
            print(f"Lowercasing username: {user.username} -> {username_lower}")
            user.username = username_lower
            user.save(update_fields=['username'])

if __name__ == "__main__":
    import django
    import os
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'volunteer_management_app')))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "volunteer_management_app.settings")
    django.setup()
    lowercase_usernames()

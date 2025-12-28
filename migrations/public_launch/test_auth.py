import sys
sys.path.insert(0, '.')

from agent_factory.integrations.telegram.public_auth import auth

# Test admin check
is_admin = auth.is_admin(8445149012)
role = auth.get_admin_role(8445149012)

print(f"Admin check: {is_admin}")
print(f"Role: {role}")

if is_admin and role == 'super_admin':
    print("Auth module working correctly")
else:
    print("Auth module issue")

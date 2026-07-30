import os
import re

SRC = r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src"

def fix_notifications():
    path = os.path.join(SRC, "components", "layout", "NotificationBell.tsx")
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if "useTranslation" not in content:
        content = "import { useTranslation } from 'react-i18next';\n" + content
    
    if "const { t } = useTranslation();" not in content:
        content = re.sub(r'(export function NotificationBell\(\) {)', r'\1\n  const { t } = useTranslation();', content)

    replacements = [
        (r'>Notifications<', '>{t("notifications.title")}<'),
        (r'>View Case<', '>{t("notifications.viewCase")}<'),
        (r'\{unreadCount\} new', '{t("notifications.new", { count: unreadCount })}'),
        (r'title="Mark as read"', 'title={t("notifications.markRead")}'),
        (r'>No notifications<', '>{t("notifications.noNotifications")}<'),
        (r'\{notif\.title\}', '{t(`notifications.dynamic.${notif.title}`) || notif.title}'),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix_notifications()
    print("Fixed NotificationBell.")

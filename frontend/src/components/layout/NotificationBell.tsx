import { useTranslation } from 'react-i18next';
import React, { useEffect, useState } from 'react';
import { Bell, BellDot, CheckCircle2 } from 'lucide-react';
import { notificationService, NotificationItem } from '../../api/client';
import { Link } from 'react-router-dom';

export function NotificationBell() {
  const { t } = useTranslation();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const data = await notificationService.getNotifications();
        setNotifications(data);
      } catch (e) {
        console.error("Failed to fetch notifications", e);
      }
    };
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 60000); // Polling every minute
    return () => clearInterval(interval);
  }, []);

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const handleMarkAsRead = async (id: string) => {
    try {
      await notificationService.markAsRead(id);
      setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (e) {
      console.error("Failed to mark notification as read", e);
    }
  };

  const toggleDropdown = () => setIsOpen(!isOpen);

  return (
    <div className="relative">
      <button 
        onClick={toggleDropdown}
        className="relative p-2 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:text-slate-100 transition-colors"
      >
        {unreadCount > 0 ? (
          <>
            <BellDot className="w-5 h-5 text-indigo-400" />
            <span className="absolute top-1 right-1 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
          </>
        ) : (
          <Bell className="w-5 h-5" />
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg shadow-xl dark:shadow-slate-900/50 z-50 overflow-hidden">
          <div className="p-3 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{t("notifications.title")}</h3>
            {unreadCount > 0 && (
              <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">
                {t("notifications.new", { count: unreadCount })}
              </span>
            )}
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-sm text-slate-500 dark:text-slate-400">
                No notifications
              </div>
            ) : (
              <div className="flex flex-col">
                {notifications.map(notif => (
                  <div 
                    key={notif.id} 
                    className={`p-3 border-b border-slate-200/50 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800 dark:bg-slate-950 transition-colors ${!notif.is_read ? 'bg-slate-100 dark:bg-slate-800' : ''}`}
                  >
                    <div className="flex justify-between items-start gap-2">
                      <div className="flex-1">
                        <p className={`text-sm ${!notif.is_read ? 'text-slate-900 dark:text-slate-100 font-medium' : 'text-slate-700 dark:text-slate-300'}`}>
                          {t(`notifications.dynamic.${notif.title}`) || notif.title}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {notif.message}
                        </p>
                        <div className="mt-2 text-[10px] text-slate-500 dark:text-slate-400 flex gap-2">
                          {new Date(notif.created_at).toLocaleString()}
                          {notif.case_id && (
                            <Link to={`/cases/${notif.case_id}`} className="text-indigo-600 hover:underline" onClick={() => setIsOpen(false)}>
                              View Case
                            </Link>
                          )}
                        </div>
                      </div>
                      {!notif.is_read && (
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleMarkAsRead(notif.id); }}
                          className="text-slate-500 dark:text-slate-400 hover:text-emerald-400 transition-colors p-1"
                          title={t("notifications.markRead")}
                        >
                          <CheckCircle2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

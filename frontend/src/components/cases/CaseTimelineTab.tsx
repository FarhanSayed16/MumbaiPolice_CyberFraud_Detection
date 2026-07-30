import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { timelineService, TimelineEventItem } from '../../api/client';
import { Clock, Plus, MessageSquare, AlertCircle, PlayCircle, Edit3, ArrowRightCircle, UploadCloud, ArrowDownUp } from 'lucide-react';

interface Props {
  caseId: string;
}

type TimelineOrder = 'asc' | 'desc';

export function CaseTimelineTab({ caseId }: Props) {
  const { t } = useTranslation();
  const [events, setEvents] = useState<TimelineEventItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [newNote, setNewNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [order, setOrder] = useState<TimelineOrder>('desc');

  const loadTimeline = async () => {
    setLoading(true);
    try {
      const data = await timelineService.list(caseId, order);
      setEvents(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTimeline();
  }, [caseId, order]);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    setSubmitting(true);
    try {
      await timelineService.addNote(caseId, newNote.trim());
      setNewNote('');
      await loadTimeline();
    } catch (err) {
      console.error(err);
      alert(t('timeline.addNoteFailed', 'Failed to add note'));
    } finally {
      setSubmitting(false);
    }
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'created': return <PlayCircle className="h-5 w-5 text-indigo-500" />;
      case 'note': return <MessageSquare className="h-5 w-5 text-sky-500" />;
      case 'status_change': return <ArrowRightCircle className="h-5 w-5 text-amber-500" />;
      case 'evidence_added': return <UploadCloud className="h-5 w-5 text-emerald-500" />;
      case 'notice_sent': return <AlertCircle className="h-5 w-5 text-rose-500" />;
      default: return <Edit3 className="h-5 w-5 text-slate-500 dark:text-slate-400" />;
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="bg-white dark:bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 flex items-center">
            <Clock className="h-5 w-5 mr-2 text-indigo-600" />
            {t('timeline.title', 'Case Timeline')}
          </h3>
          <div className="inline-flex rounded-md border border-slate-200 overflow-hidden" role="group" aria-label={t('timeline.orderLabel', 'Timeline sort order')}>
            <button
              type="button"
              onClick={() => setOrder('desc')}
              className={`px-3 py-1.5 text-xs font-medium inline-flex items-center gap-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                order === 'desc' ? 'bg-indigo-600 text-white' : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:bg-slate-950'
              }`}
            >
              <ArrowDownUp className="h-3.5 w-3.5" />
              {t('timeline.orderNewest', 'Newest')}
            </button>
            <button
              type="button"
              onClick={() => setOrder('asc')}
              className={`px-3 py-1.5 text-xs font-medium inline-flex items-center gap-1 border-l border-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                order === 'asc' ? 'bg-indigo-600 text-white' : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:bg-slate-950'
              }`}
            >
              {t('timeline.orderChronological', 'Chronological')}
            </button>
          </div>
        </div>
        
        <form onSubmit={handleAddNote} className="mb-8">
          <label htmlFor="note" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            {t('timeline.addNoteLabel', 'Add manual officer note')}
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              id="note"
              className="flex-1 border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
              placeholder={t('timeline.notePlaceholder', 'e.g. Spoke to nodal officer, awaiting physical copy...')}
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              disabled={submitting}
            />
            <button
              type="submit"
              disabled={submitting || !newNote.trim()}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              <Plus className="h-4 w-4 mr-1" /> {t('timeline.addNoteButton', 'Add Note')}
            </button>
          </div>
        </form>

        <div className="flow-root">
          {loading ? (
            <div className="text-sm text-slate-500 dark:text-slate-400">{t('timeline.loading', 'Loading timeline...')}</div>
          ) : events.length === 0 ? (
            <div className="text-sm text-slate-500 dark:text-slate-400 text-center py-4 bg-slate-50 dark:bg-slate-950 rounded border border-dashed border-slate-300">
              {t('timeline.empty', 'No events recorded yet.')}
            </div>
          ) : (
            <ul className="-mb-8">
              {events.map((event, eventIdx) => (
                <li key={event.id}>
                  <div className="relative pb-8">
                    {eventIdx !== events.length - 1 ? (
                      <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-slate-200" aria-hidden="true"></span>
                    ) : null}
                    <div className="relative flex space-x-3">
                      <div>
                        <span className="h-8 w-8 rounded-full bg-slate-50 dark:bg-slate-950 flex items-center justify-center ring-8 ring-white border border-slate-200">
                          {getEventIcon(event.event_type)}
                        </span>
                      </div>
                      <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                        <div>
                          <p className="text-sm text-slate-900 dark:text-slate-100">
                            {event.description}
                          </p>
                          {event.metadata_json && Object.keys(event.metadata_json).length > 0 && (
                            <div className="mt-2 text-xs text-slate-500 dark:text-slate-400 font-mono bg-slate-50 dark:bg-slate-950 p-2 rounded border border-slate-100">
                              {JSON.stringify(event.metadata_json)}
                            </div>
                          )}
                        </div>
                        <div className="text-right text-xs whitespace-nowrap text-slate-500 dark:text-slate-400 flex flex-col items-end">
                          <time dateTime={event.created_at}>{new Date(event.created_at).toLocaleString()}</time>
                          {event.created_by_user_id && (
                            <span className="mt-1 bg-slate-100 text-slate-600 dark:text-slate-400 px-1.5 py-0.5 rounded">User {event.created_by_user_id.substring(0,6)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

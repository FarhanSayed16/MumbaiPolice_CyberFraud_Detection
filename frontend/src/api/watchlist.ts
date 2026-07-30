import { api } from './client';

export interface WatchlistEntry {
  id: string;
  account_number: string | null;
  ifsc_code: string | null;
  upi_id: string | null;
  phone: string | null;
  reason: string;
  risk_score: number;
  is_active: boolean;
  added_by_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface WatchlistEntryCreate {
  account_number: string | null;
  ifsc_code: string | null;
  upi_id: string | null;
  phone: string | null;
  reason: string;
  risk_score: number;
  is_active: boolean;
}

export interface WatchlistEntryUpdate {
  reason?: string;
  risk_score?: number;
  is_active?: boolean;
  phone?: string;
}

export const watchlistApi = {
  list: async (): Promise<WatchlistEntry[]> => {
    const res = await api.get('/watchlist/');
    return res.data;
  },

  create: async (data: WatchlistEntryCreate): Promise<WatchlistEntry> => {
    const res = await api.post('/watchlist/', data);
    return res.data;
  },

  update: async (id: string, data: WatchlistEntryUpdate): Promise<WatchlistEntry> => {
    const res = await api.put(`/watchlist/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/watchlist/${id}`);
  }
};

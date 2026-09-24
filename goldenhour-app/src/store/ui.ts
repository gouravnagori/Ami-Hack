/* ============================================================
   GoldenHour — UI Store (Zustand)
   ============================================================ */
import { create } from 'zustand';

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

interface UiState {
  mobileMenuOpen: boolean;
  setMobileMenu: (open: boolean) => void;
  toggleMobileMenu: () => void;

  toasts: Toast[];
  addToast: (toastOrMessage: string | Omit<Toast, 'id'>, type?: Toast['type']) => void;
  removeToast: (id: string) => void;

  language: 'en' | 'hi';
  setLanguage: (lang: 'en' | 'hi') => void;

  simSpeed: number;
  setSimSpeed: (speed: number) => void;
}

export const useUiStore = create<UiState>((set) => ({
  mobileMenuOpen: false,
  setMobileMenu: (open) => set({ mobileMenuOpen: open }),
  toggleMobileMenu: () => set((s) => ({ mobileMenuOpen: !s.mobileMenuOpen })),

  toasts: [],
  addToast: (toastOrMessage, type = 'info') => {
    const id = crypto.randomUUID();
    const newToast: Toast =
      typeof toastOrMessage === 'string'
        ? { id, message: toastOrMessage, type, duration: 4000 }
        : { ...toastOrMessage, id };

    set((s) => ({ toasts: [...s.toasts, newToast] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, newToast.duration || 4000);
  },
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),

  language: 'en',
  setLanguage: (lang) => set({ language: lang }),

  simSpeed: 1,
  setSimSpeed: (speed) => set({ simSpeed: speed }),
}));

import { create } from 'zustand';

type Language = 'zh' | 'en';

type Translations = {
  [key in Language]: {
    [key: string]: string;
  };
};

const translations: Translations = {
  zh: {
    'app.title': 'M3 AGENT // 指挥中心',
    'app.subtitle': 'Cyber-Tactical Command Interface v2.0.0',
    'status.online': '系统在线。等待指令。',
    'status.sync': '同步',
    'action.reset_memory': '重置记忆',
    'action.check_status': '查看状态',
    'action.clear_context': '清空上下文',
    'log.title': '系统日志 & 思维链',
    'log.running': '运行中',
    'log.filter': '筛选',
    'input.placeholder': '输入指令... (支持粘贴/拖拽文件)',
    'mobile.expand_logs': '展开日志',
    'mobile.collapse_logs': '收起日志',
  },
  en: {
    'app.title': 'M3 AGENT // COMMAND CENTER',
    'app.subtitle': 'Cyber-Tactical Command Interface v2.0.0',
    'status.online': 'System Online. Awaiting Orders.',
    'status.sync': 'SYNC',
    'action.reset_memory': 'Reset Memory',
    'action.check_status': 'System Status',
    'action.clear_context': 'Clear Context',
    'log.title': 'System Logs & CoT',
    'log.running': 'RUNNING',
    'log.filter': 'Filter',
    'input.placeholder': 'Enter command... (Paste/Drag files)',
    'mobile.expand_logs': 'Show Logs',
    'mobile.collapse_logs': 'Hide Logs',
  }
};

interface I18nStore {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

export const useI18n = create<I18nStore>((set, get) => ({
  language: 'zh',
  setLanguage: (lang: Language) => set({ language: lang }),
  t: (key: string) => {
    const lang = get().language;
    return translations[lang][key] || key;
  }
}));

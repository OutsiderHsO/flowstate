export const SITE = {
  name: 'AUTOMOTIVE JOURNAL',
  /** Short mark shown in the header */
  mark: 'AJ',
  tagline: {
    zh: '个人汽车文化笔记',
    en: 'Notes on automotive culture',
  },
  description: {
    zh: '一份关于汽车文化、改装研究、驾驶体验与车辆测评的个人笔记。',
    en: 'A personal notebook on car culture, modification research, driving experience and vehicle reviews.',
  },
  /**
   * TODO: replace with your real links before deploying.
   * Kept as placeholders so nothing is published by accident.
   */
  author: {
    name: 'Editor',
    handle: '@your-handle',
  },
} as const;

export const LANGS = ['zh', 'en'] as const;
export type Lang = (typeof LANGS)[number];

export const DEFAULT_LANG: Lang = 'zh';

export function isLang(value: string | undefined): value is Lang {
  return value === 'zh' || value === 'en';
}

/** Locale tag for <html lang> */
export const LOCALE: Record<Lang, string> = {
  zh: 'zh-CN',
  en: 'en',
};

/** Human-facing names used in the language switch */
export const LANG_LABEL: Record<Lang, string> = {
  zh: '中文',
  en: 'EN',
};

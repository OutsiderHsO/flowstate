export const SITE = {
  name: 'FLOWSTATE',
  /** Short mark shown in the header */
  mark: 'FS',
  tagline: {
    zh: '汽车文化与同人小说',
    en: 'Cars & fiction',
  },
  description: {
    zh: 'FLOWSTATE — 汽车文化笔记与同人创作的个人站点。改装研究、驾驶体验、车辆测评，以及短篇小说与同人文。',
    en: 'FLOWSTATE — a personal site for automotive writing and fiction: modification research, driving notes and reviews, plus short stories and fan fiction.',
  },
  author: {
    name: 'Sayo//n4ra',
    handle: 'Sayo//n4ra',
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

/**
 * The two editorial tracks of the site. Each owns a route prefix and a
 * distinct visual accent so readers can tell them apart instantly.
 */
export const SECTIONS = ['automotive', 'fiction'] as const;
export type SectionKey = (typeof SECTIONS)[number];

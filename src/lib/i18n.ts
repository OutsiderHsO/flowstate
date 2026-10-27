type LangKey = 'zh' | 'en';

type Dict = {
  nav: { home: string; journal: string; about: string; langSwitch: string };
  sections: {
    featured: string;
    latest: string;
    categories: string;
    index: string;
    colophon: string;
  };
  labels: {
    readMore: string;
    minRead: string;
    words: string;
    updated: string;
    issue: string;
    filterAll: string;
    empty: string;
    draft: string;
    backToJournal: string;
    prev: string;
    next: string;
    contents: string;
  };
  footer: {
    builtWith: string;
    rights: string;
    placeholderNote: string;
  };
};

export const t: Record<LangKey, Dict> = {
  zh: {
    nav: {
      home: '首页',
      journal: '文章',
      about: '关于',
      langSwitch: '切换语言',
    },
    sections: {
      featured: '封面故事',
      latest: '最新发布',
      categories: '栏目',
      index: '全部文章',
      colophon: '关于本刊',
    },
    labels: {
      readMore: '阅读',
      minRead: '分钟阅读',
      words: '字',
      updated: '更新于',
      issue: '期号',
      filterAll: '全部',
      empty: '暂无文章。',
      draft: '草稿',
      backToJournal: '返回文章列表',
      prev: '上一篇',
      next: '下一篇',
      contents: '目录',
    },
    footer: {
      builtWith: '由 Astro 静态生成',
      rights: '版权所有',
      placeholderNote: '本站内容为占位示例，非真实测评。',
    },
  },
  en: {
    nav: {
      home: 'Home',
      journal: 'Journal',
      about: 'About',
      langSwitch: 'Change language',
    },
    sections: {
      featured: 'Cover story',
      latest: 'Latest',
      categories: 'Sections',
      index: 'All entries',
      colophon: 'Colophon',
    },
    labels: {
      readMore: 'Read',
      minRead: 'min read',
      words: 'words',
      updated: 'Updated',
      issue: 'Issue',
      filterAll: 'All',
      empty: 'No entries yet.',
      draft: 'Draft',
      backToJournal: 'Back to journal',
      prev: 'Previous',
      next: 'Next',
      contents: 'Contents',
    },
    footer: {
      builtWith: 'Statically generated with Astro',
      rights: 'All rights reserved',
      placeholderNote: 'All sample content is placeholder — not a real review.',
    },
  },
};

/** Category slugs are shared across languages; display names are not. */
export const CATEGORIES = {
  culture: { zh: '汽车文化', en: 'Car Culture' },
  modification: { zh: '改装研究', en: 'Modification' },
  driving: { zh: '驾驶体验', en: 'Driving' },
  review: { zh: '车辆测评', en: 'Reviews' },
  essay: { zh: '随笔', en: 'Essays' },
} as const;

export type CategoryKey = keyof typeof CATEGORIES;

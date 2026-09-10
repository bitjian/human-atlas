import {useCallback, useEffect, useState} from 'react';
import type {SystemId} from '../anatomy';
import {MESSAGES, type MessageKey} from './messages';
import {ANATOMY_ZH, EXPLANATIONS_ZH, SYSTEM_TEXT_ZH} from './anatomy-zh';

export type Lang = 'en' | 'zh';
export type Vars = Record<string, string | number>;
export type Named = {id: string; name: string};

const STORAGE_KEY = 'human-atlas-lang';

export function detectLang(): Lang {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'en' || saved === 'zh') return saved;
  } catch {
    // localStorage 不可用时忽略
  }
  if (typeof navigator !== 'undefined' && navigator.language.toLowerCase().startsWith('zh')) return 'zh';
  return 'en';
}

export function translate(lang: Lang, key: MessageKey, vars?: Vars): string {
  const raw = (lang === 'zh' ? MESSAGES.zh : MESSAGES.en)[key] ?? MESSAGES.en[key];
  if (!vars) return raw;
  return raw.replace(/\{(\w+)\}/g, (match, name: string) => (vars[name] !== undefined ? String(vars[name]) : match));
}

export function useI18n() {
  const [lang, setLang] = useState<Lang>(detectLang);
  useEffect(() => {
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
    document.title = translate(lang, 'docTitle');
    document.querySelector('meta[name="description"]')?.setAttribute('content', translate(lang, 'docDescription'));
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // 忽略写入失败
    }
  }, [lang]);
  const t = useCallback((key: MessageKey, vars?: Vars) => translate(lang, key, vars), [lang]);
  return {lang, setLang, t};
}

// 中文名外挂查表：命中返回中文，未命中回退英文原名。
export function displayName(lang: Lang, entity: Named): string {
  if (lang !== 'zh') return entity.name;
  return ANATOMY_ZH[entity.id] ?? entity.name;
}

export function systemName(lang: Lang, id: SystemId, fallback: string): string {
  if (lang !== 'zh') return fallback;
  return SYSTEM_TEXT_ZH[id]?.name ?? fallback;
}

export function systemDescription(lang: Lang, id: SystemId, fallback: string): string {
  if (lang !== 'zh') return fallback;
  return SYSTEM_TEXT_ZH[id]?.description ?? fallback;
}

// 解释按 conceptId 取值，结构名本地化后依然命中。
export function structureExplanation(lang: Lang, conceptId: string | undefined, fallback: string): string {
  if (lang !== 'zh') return fallback;
  return (conceptId ? EXPLANATIONS_ZH[conceptId] : undefined) ?? fallback;
}

export function hasOwnExplanation(lang: Lang, conceptId: string | undefined, name: string, englishTable: Record<string, string>): boolean {
  if (lang === 'zh') return !!conceptId && !!EXPLANATIONS_ZH[conceptId];
  return !!englishTable[name.toLowerCase()];
}

// 中文模式下同时匹配中文名与英文原名。
export function searchText(lang: Lang, entity: Named): string {
  if (lang !== 'zh') return entity.name.toLowerCase();
  return `${entity.name} ${ANATOMY_ZH[entity.id] ?? ''}`.toLowerCase();
}

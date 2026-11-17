'use client';
import { useEffect, useRef, useState } from 'react';
import { readJson, writeLocal } from '@/lib/view-preferences';
export function useLocalPreference<T>(key: string, initial: T, parse: (value: unknown) => T) {
    const [value, setValue] = useState(initial), [loadedKey, setLoadedKey] = useState<string | null>(null);
    const decode = useRef(parse); decode.current = parse;
    useEffect(() => { setValue(decode.current(readJson(key))); setLoadedKey(key); }, [key]);
    useEffect(() => { if (loadedKey === key) writeLocal(key, JSON.stringify(value)); }, [key, loadedKey, value]);
    return [value, setValue] as const;
}

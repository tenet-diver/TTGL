'use client';
import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { readLocal, writeLocal } from '@/lib/view-preferences';
export function ThemeToggle() { const [dark, setDark] = useState(true); useEffect(() => { const sync = () => { const stored = readLocal('observatory-theme'); const next = stored === 'light' ? false : true; setDark(next); document.documentElement.classList.toggle('dark', next); }; sync(); window.addEventListener('observatory-theme', sync); return () => window.removeEventListener('observatory-theme', sync); }, []); return <Button variant="ghost" size="sm" onClick={() => { const next = !dark; setDark(next); document.documentElement.classList.toggle('dark', next); writeLocal('observatory-theme', next ? 'dark' : 'light'); window.dispatchEvent(new Event('observatory-theme')); }} aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}>{dark ? <Sun size={14}/> : <Moon size={14}/>}<span>{dark ? 'Light' : 'Dark'}</span></Button>; }

'use client';
import { useId, useState, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
export interface FormField {
    key: string;
    label: string;
    type?: string;
    value?: unknown;
    required?: boolean;
    options?: {
        value: string;
        label: string;
    }[];
}
export async function mutate(action: string, values: Record<string, unknown>) {
    const response = await fetch('/api/actions', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ action, ...values }) });
    const result = await response.json();
    if (!response.ok)
        throw Error(result.error || 'The change could not be saved.');
    return result as Record<string, unknown>;
}
export function MutationDialog({ action, title, description, fields = [], values = {}, children, onSaved, destructive = false }: {
    action: string;
    title: string;
    description?: string;
    fields?: FormField[];
    values?: Record<string, unknown>;
    children: ReactNode;
    onSaved?: () => void;
    destructive?: boolean;
}) {
    const id = useId(), router = useRouter(), [open, setOpen] = useState(false), [pending, setPending] = useState(false), [error, setError] = useState('');
    return <Dialog open={open} onOpenChange={next => {
            if (!pending) {
                setOpen(next);
                setError('');
            }
        }}><DialogTrigger asChild>{children}</DialogTrigger><DialogContent className="form-dialog"><DialogHeader><DialogTitle>{title}</DialogTitle><DialogDescription>{description || 'Changes are saved to PostgreSQL and recorded in the audit log.'}</DialogDescription></DialogHeader><form onSubmit={async (event) => {
            event.preventDefault();
            const form = event.currentTarget;
            setPending(true);
            setError('');
            try {
                const data: Record<string, unknown> = { ...values };
                const entries = new FormData(form);
                for (const field of fields) {
                    const raw = entries.get(field.key);
                    data[field.key] = field.type === 'number' ? Number(raw) : field.type === 'json' ? JSON.parse(String(raw)) : field.type === 'datetime-local' ? new Date(String(raw)).toISOString() : raw;
                }
                await mutate(action, data);
                setOpen(false);
                onSaved?.();
                router.refresh();
            }
            catch (e) {
                setError(e instanceof Error ? e.message : 'Save failed');
            }
            finally {
                setPending(false);
            }
        }}>
 <div className="form-fields">{fields.map(field => <div className="form-field" key={field.key}><label htmlFor={id + field.key}>{field.label}</label>{field.options ? <Select name={field.key} defaultValue={String(field.value ?? field.options[0]?.value ?? '')}><SelectTrigger id={id + field.key}><SelectValue /></SelectTrigger><SelectContent>{field.options.map(option => <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>)}</SelectContent></Select> : ['textarea', 'json'].includes(field.type || '') ? <Textarea id={id + field.key} name={field.key} defaultValue={typeof field.value === 'object' ? JSON.stringify(field.value, null, 2) : String(field.value ?? '')} required={field.required} rows={field.type === 'json' ? 10 : 3} className={field.type === 'json' ? 'font-mono' : ''}/> : <Input id={id + field.key} name={field.key} type={field.type || 'text'} defaultValue={String(field.value ?? '')} required={field.required} min={field.type === 'number' ? 0 : undefined}/>}</div>)}</div>
 {error && <p role="alert" className="error-message">{error}</p>}<DialogFooter><Button type="button" variant="outline" disabled={pending} onClick={() => setOpen(false)}>Cancel</Button><Button type="submit" variant={destructive ? 'destructive' : 'default'} disabled={pending}>{pending ? 'Saving…' : destructive ? 'Delete' : action === 'analysis-batch' || action === 'analyze' ? 'Start analysis' : 'Save'}</Button></DialogFooter></form></DialogContent></Dialog>;
}

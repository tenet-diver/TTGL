'use client';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { mutate } from './mutation-dialog';
import { apiJson } from '@/lib/api-response';
export function PricingEditor() {
    const [value, setValue] = useState(''), [tiers, setTiers] = useState(''), [message, setMessage] = useState(''), [pending, setPending] = useState(false);
    useEffect(() => {
        const controller = new AbortController();
        fetch('/api/settings', { signal: controller.signal }).then(async r => {
            const body = await apiJson<Record<string, unknown>>(r);
            if (!r.ok) throw Error(String(body.error || 'Settings unavailable'));
            return body;
        }).then(body => { setValue(JSON.stringify(body.pricing || { unit: 'USD', models: {} }, null, 2)); setTiers(JSON.stringify(body.model_tiers || { top: [], small: [] }, null, 2)); }).catch(e => {
            if (!controller.signal.aborted)
                setMessage(String(e));
        });
        return () => controller.abort();
    }, []);
    return <form className="pricing-form" onSubmit={async (event) => {
            event.preventDefault();
            setPending(true);
            setMessage('');
            try {
                await mutate('pricing', { pricing: JSON.parse(value), model_tiers: JSON.parse(tiers) });
                setMessage('Rates saved. Estimates recalculate from retained counters.');
            }
            catch (e) {
                setMessage(e instanceof Error ? e.message : 'Save failed');
            }
            finally {
                setPending(false);
            }
        }}><p className="section-note">Dated API-equivalent estimates use rates per million tokens, independently of subscription cash. Native input includes cache reads; long_context rates apply to the full request above their threshold. Unreported cache writes remain unclassified input at the ordinary input rate, with no separate write surcharge inferred. Explicit cache writes need write_5m/write_1h rates, or a configured flat write rate; otherwise that estimate stays unknown. Define top/small model tiers explicitly to enable model-tier findings.</p><label htmlFor="pricing-rates">Model rates</label><Textarea id="pricing-rates" aria-label="Model rates" rows={16} className="font-mono" value={value} onChange={e => setValue(e.target.value)}/><label htmlFor="model-tiers">Model tiers</label><Textarea id="model-tiers" aria-label="Model tiers" rows={5} className="font-mono" value={tiers} onChange={e => setTiers(e.target.value)}/><Button disabled={pending || !value} type="submit">{pending ? 'Saving…' : 'Save rates'}</Button><p role="status">{message}</p></form>;
}

import type { CSSProperties } from 'react';
import { CheckCircle2, CircleAlert, CircleHelp, CirclePlay, Clock3, CircleSlash } from 'lucide-react';
import { Badge } from './ui/badge';
import { colorStyle, toneFor, statusShape, type ColorKind } from '@/lib/semantic-colors';
import { format } from '@/lib/format';
const icons = { success: CheckCircle2, error: CircleAlert, warning: CircleAlert, active: CirclePlay, pending: Clock3, cancelled: CircleSlash, unknown: CircleHelp };
export function SemanticBadge({ value, kind = 'status' }: { value: unknown; kind?: ColorKind }) {
    const Icon = kind === 'status' ? icons[statusShape(value)] : kind === 'event' && toneFor(value, kind) === 'red' ? CircleAlert : null;
    return <Badge variant="outline" className="semantic-badge" style={colorStyle(value, kind) as CSSProperties} data-semantic-kind={kind} data-semantic-value={String(value ?? 'unknown')} data-tone={toneFor(value, kind)}>
        {Icon ? <Icon aria-hidden="true" size={12}/> : <i className="semantic-dot" aria-hidden="true"/>}{format(value)}
    </Badge>;
}

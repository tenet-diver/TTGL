'use client';
import { useState, type ReactNode } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible';
import { Button } from '@/components/ui/button';
export function AnalysisCard({ title, description, children, actions, className = '', defaultOpen = true }: {
    title: string;
    description?: string;
    children: ReactNode;
    actions?: ReactNode;
    className?: string;
    defaultOpen?: boolean;
}) {
    const [open, setOpen] = useState(defaultOpen);
    return <Card className={'analysis-card ' + className}><Collapsible open={open} onOpenChange={setOpen}><div className="card-heading"><CollapsibleTrigger asChild><Button variant="ghost" className="card-title" aria-label={`${open ? 'Collapse' : 'Expand'} ${title}`}>{open ? <ChevronDown size={14}/> : <ChevronRight size={14}/>}<h2>{title}</h2></Button></CollapsibleTrigger>{actions && <div className="card-actions">{actions}</div>}</div><CollapsibleContent><CardContent>{description && <p className="section-note">{description}</p>}{children}</CardContent></CollapsibleContent></Collapsible></Card>;
}

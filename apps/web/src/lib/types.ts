export type Json = null | boolean | number | string | Json[] | {
    [key: string]: Json;
};
export type Row = Record<string, unknown> & {
    id: string;
};
export interface Scope {
    workspace: string;
    project: string;
    range: string;
    timezone: string;
    task?: string;
}
export interface Column {
    key: string;
    label: string;
    numeric?: boolean;
    hidden?: boolean;
    type?: 'link' | 'date' | 'duration' | 'money' | 'tokens' | 'percent' | 'badge' | 'code' | 'json';
    href?: string;
}
export interface Query {
    search: string;
    filters: Record<string, string>;
    sort: string | null;
    direction: 1 | -1;
    offset: number;
    limit: number;
}
export interface RecordPage {
    rows: Row[];
    total: number;
    offset: number;
    limit: number;
    columns: Column[];
}
export interface Metric {
    label: string;
    value: number | string | null;
    format?: Column['type'];
    note?: string;
    href?: string;
}
export interface ChartPoint {
    date: string;
    [key: string]: string | number | null;
}
export interface ChartSpec {
    id: string;
    title: string;
    description?: string;
    kind: 'bar' | 'line' | 'horizontal' | 'treemap' | 'heatmap' | 'turns' | 'flow';
    colorKind?: import('./semantic-colors.ts').ColorKind;
    points: Record<string, unknown>[];
    series: {
        key: string;
        name: string;
        color: string;
    }[];
    last?: number | null;
    markers?: {
        at: string;
        number: number;
        title: string;
    }[];
}
export interface Panel {
    id: string;
    title: string;
    description?: string;
    list?: string;
    chart?: ChartSpec;
    text?: string;
}
export interface PageData {
    title: string;
    description: string;
    section: string;
    metrics: Metric[];
    panels: Panel[];
    workspaces: string[];
    projects: {
        id: string;
        name: string;
    }[];
    coverage?: {
        complete: number;
        total: number;
        pending: number;
        unclassified: number;
    };
    actions?: string[];
}
export interface NativeEvent {
    id: string;
    version: number;
    turn_key: string;
    session_id: string;
    turn_id: string;
    workspace: string;
    kind: string;
    name: string;
    model: string;
    event_time: string;
    time_known: number;
    runtime: number | null;
    runtime_role: string;
    failed: number | null;
    input_tokens: number | null;
    cached_tokens: number | null;
    output_tokens: number | null;
    total_tokens: number | null;
    cache_write_tokens: number | null;
    cache_5m_tokens: number | null;
    command: string;
    output_excerpt: string;
    output_chars: number | null;
    output_hash: string;
    signature: string;
    role: string;
    agent_type: string;
    source_path: string;
    source_line: number;
    payload: string;
}
export interface Pricing {
    unit: string;
    models: Record<string, {
        input: number;
        cached: number;
        output: number;
        write?: number;
        write_5m?: number;
        write_1h?: number;
        long_context?: { above_tokens: number; input: number; cached: number; output: number; write?: number; write_5m?: number; write_1h?: number };
    }>;
    as_of?: string;
    scenario_id?: string;
    kind?: 'api_equivalent';
    service_tier?: string;
    source_urls?: string[];
    assumptions?: string[];
}
export { chartPalette as palette, activityColors as categoryColors } from './semantic-colors.ts';

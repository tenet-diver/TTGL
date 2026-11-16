import { pg } from './database.ts';
import { hash } from './domain.ts';
/** Decode retained inline raster bytes only. Never follow URLs or transcript paths. */
export function raster(mime: string, data: string) {
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(mime) || data.length > 1400000)
        return null;
    const bytes = Buffer.from(data, 'base64');
    if (bytes.length > 1048576)
        return null;
    const valid = mime === 'image/png' ? bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])) : mime === 'image/jpeg' ? bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255 : bytes.subarray(0, 4).toString() === 'RIFF' && bytes.subarray(8, 12).toString() === 'WEBP';
    return valid ? { mime, bytes } : null;
}
export async function retainRasters(events: {
    id: string;
    turn_key?: string;
    session_id: string;
    turn_id: string;
    payload?: string;
}[]) {
    for (const event of events) {
        if (!event.payload || !event.payload.includes('image/'))
            continue;
        let payload: unknown;
        try {
            payload = JSON.parse(event.payload);
        }
        catch {
            continue;
        }
        let visited = 0;
        const found: {
            mime: string;
            bytes: Buffer;
        }[] = [];
        const walk = (value: unknown, depth = 0) => {
            if (depth > 10 || ++visited > 1000)
                return;
            if (typeof value === 'string') {
                const m = value.match(/^data:(image\/(?:png|jpeg|webp));base64,([\s\S]+)$/);
                if (m) {
                    const image = raster(m[1], m[2]);
                    if (image)
                        found.push(image);
                }
                return;
            }
            if (!value || typeof value !== 'object')
                return;
            const obj = value as Record<string, unknown>;
            if (obj.type === 'base64' && typeof obj.media_type === 'string' && typeof obj.data === 'string') {
                const image = raster(obj.media_type, obj.data);
                if (image)
                    found.push(image);
            }
            for (const child of Object.values(obj))
                walk(child, depth + 1);
        };
        walk(payload);
        if (!found.length)
            continue;
        const key = JSON.stringify([event.session_id, event.turn_id]), [owner] = await pg() `SELECT task_id FROM assignments WHERE turn_key=${key}`;
        for (const image of found) {
            const id = 'image:' + hash([event.id, hash(image.bytes)]);
            await pg() `INSERT INTO retained_images(id,task_id,event_id,mime,bytes) VALUES(${id},${owner?.task_id || null},${event.id},${image.mime},${image.bytes}) ON CONFLICT DO NOTHING`;
        }
    }
}

/** Bounded wildcard matcher for imported contains/glob steering configurations. */
export function glob(pattern: string, text: string) {
    if (pattern.length > 500 || text.length > 16000)
        return false;
    let p = 0, t = 0, star = -1, back = 0;
    while (t < text.length) {
        if (pattern[p] === '?' || pattern[p] === text[t]) {
            p++;
            t++;
        }
        else if (pattern[p] === '*') {
            star = p++;
            back = t;
        }
        else if (star >= 0) {
            p = star + 1;
            t = ++back;
        }
        else
            return false;
    }
    while (pattern[p] === '*')
        p++;
    return p === pattern.length;
}

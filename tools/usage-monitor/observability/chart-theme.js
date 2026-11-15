/** Neutral data fills; chromatic categories are restricted to small indicator dots. */
export const chartTones=Array.from({length:8},(_,i)=>`var(--chart-${i+1})`);
export const chartText=index=>`var(--chart-label-${(index%8+8)%8+1})`;
const dots=['#0062d1','#067a6e','#398e4a','#ff990a','#e5484d','#ea3e83','#7820bc','#52aeff'];
export const categoryDot=index=>dots[(index%8+8)%8];

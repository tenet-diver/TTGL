// Apply the local preference before styles paint; storage can be unavailable.
try {
  const theme=localStorage.getItem('ttgl-theme');
  if(theme==='dark'||theme==='light') document.documentElement.dataset.theme=theme;
} catch {}

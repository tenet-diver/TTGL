/** Native-DOM adaptation of shadcn/ui. See ui/README.md and ui/LICENSE-shadcn. */
import { createActionMenu as nativeActionMenu } from '/design-system/dom.js';
import { icons } from '/ui/icons.js';

export const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

export function icon(name, className='') {
  return `<svg class="ui-icon ${escapeHTML(className)}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${icons[name] || icons['database']}</svg>`;
}

export function button(title, attributes='', primary=false, iconName='') {
  return `<button data-slot="button" data-variant="${primary?'default':'outline'}" class="ui-button" ${attributes}>${iconName?icon(iconName):''}${escapeHTML(title)}</button>`;
}

export function badge(value) {
  return `<span data-slot="badge" data-variant="secondary" class="ui-badge">${escapeHTML(value)}</span>`;
}

export function emptyState(title, description='', action='', iconName='inbox') {
  return `<div class="ui-empty" data-slot="empty"><span class="empty-icon">${icon(iconName)}</span><strong>${escapeHTML(title)}</strong>${description?`<p>${escapeHTML(description)}</p>`:''}${action}</div>`;
}

export function skeleton(label='Loading collected evidence') {
  return `<div role="status" aria-label="${escapeHTML(label)}"><span class="sr-only">${escapeHTML(label)}…</span><div class="skeleton-stats">${Array.from({length:4},()=>'<div data-slot="skeleton" class="ui-skeleton skeleton-card"></div>').join('')}</div><div class="skeleton-table">${Array.from({length:5},()=>'<div data-slot="skeleton" class="ui-skeleton skeleton-row"></div>').join('')}</div></div>`;
}

/** Preserve the existing tested keyboard/popover behavior, apply shared components. */
export function createActionMenu(document, label, actions) {
  const group = nativeActionMenu(document, label, actions);
  const trigger = group.querySelector('button');
  trigger.className = 'ui-button ui-icon-button';
  trigger.dataset.slot = 'dropdown-menu-trigger';
  trigger.dataset.variant = 'ghost';
  trigger.innerHTML = icon('ellipsis');
  const menu = group.querySelector('[role="menu"]');
  menu.className = 'ui-menu';
  menu.dataset.slot = 'dropdown-menu-content';
  menu.querySelectorAll('[role="menuitem"]').forEach(item => {
    item.className = 'ui-menu-item';
    item.dataset.slot = 'dropdown-menu-item';
    const action = actions[Array.from(menu.children).indexOf(item)];
    if(action?.destructive) item.dataset.variant = 'destructive';
    item.querySelector('svg')?.classList.add('ui-icon');
  });
  return group;
}

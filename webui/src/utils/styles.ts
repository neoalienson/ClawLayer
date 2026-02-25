import { css, unsafeCSS } from 'lit';

export async function loadExternalStyles(url: string) {
  const response = await fetch(url);
  const cssText = await response.text();
  return css`${unsafeCSS(cssText)}`;
}

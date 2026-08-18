export function getItem(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export function setItem(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* Safari private mode / blocked storage */
  }
}

export function removeItem(key: string): void {
  try {
    localStorage.removeItem(key)
  } catch {
    /* no-op */
  }
}

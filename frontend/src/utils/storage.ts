export function getStorage<T>(key: string, fallback: T): T {
  const raw = localStorage.getItem(key);

  if (!raw) {
    return fallback;
  }

  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function setStorage<T>(key: string, value: T): void {
  localStorage.setItem(key, JSON.stringify(value));
}

export function getSessionStorage<T>(key: string, fallback: T): T {
  const raw = sessionStorage.getItem(key);

  if (!raw) {
    return fallback;
  }

  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function setSessionStorage<T>(key: string, value: T): void {
  sessionStorage.setItem(key, JSON.stringify(value));
}

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export async function fetchApi<TData>(path: string, options: RequestInit = {}): Promise<TData> {
  const headers = new Headers(options.headers);
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as {
        detail?: string | Array<{ msg?: string }>;
      };
      if (typeof payload.detail === 'string') {
        message = payload.detail;
      } else if (Array.isArray(payload.detail)) {
        const validationMessages = payload.detail
          .map((item) => item.msg)
          .filter((item): item is string => Boolean(item));
        if (validationMessages.length) {
          message = validationMessages.join(' ');
        }
      }
    } catch {
      message = `Request failed with status ${response.status}`;
    }
    throw new ApiError(message, response.status);
  }

  const data = (await response.json()) as TData;
  return data;
}

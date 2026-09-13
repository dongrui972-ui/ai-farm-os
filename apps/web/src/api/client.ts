type JsonBody = Record<string, unknown> | undefined;

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: JsonBody;
};

function withQuery(path: string, query: Record<string, string | undefined>): string {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });
  const queryString = params.toString();
  return queryString ? `${path}?${queryString}` : path;
}

export class ApiClient {
  private readonly basePath: string;

  constructor(basePath = "") {
    this.basePath = basePath;
  }

  async request<T>(path: string, init: RequestOptions = {}): Promise<T> {
    const res = await fetch(`${this.basePath}${path}`, {
      headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
      ...init,
      body: init.body ? JSON.stringify(init.body) : undefined,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    return (await res.json()) as T;
  }

  pathWithQuery(path: string, query: Record<string, string | undefined>): string {
    return withQuery(path, query);
  }
}

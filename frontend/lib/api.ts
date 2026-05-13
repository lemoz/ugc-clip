const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private token(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("token");
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string> || {}),
    };
    const tok = this.token();
    if (tok) headers["Authorization"] = `Bearer ${tok}`;

    const res = await fetch(`${this.baseUrl}${path}`, { ...options, headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    if (res.status === 204) return undefined as T;
    return res.json();
  }

  async register(email: string, password: string, display_name: string) {
    return this.request<{ access_token: string; user_id: string; email: string }>(
      "/api/v1/auth/register",
      { method: "POST", body: JSON.stringify({ email, password, display_name }) }
    );
  }

  async login(email: string, password: string) {
    return this.request<{ access_token: string; user_id: string; email: string }>(
      "/api/v1/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) }
    );
  }

  async getMe() {
    return this.request<{ id: string; email: string; display_name: string; tier: string }>(
      "/api/v1/auth/me"
    );
  }

  async listPersonas() {
    return this.request<{ id: string; name: string; display_name: string }[]>(
      "/api/v1/personas"
    );
  }

  async createPersona(name: string) {
    return this.request<{ id: string; name: string; display_name: string }>(
      "/api/v1/personas",
      { method: "POST", body: JSON.stringify({ name }) }
    );
  }

  async listProjects() {
    return this.request<{ id: string; name: string; status: string; stage: number }[]>(
      "/api/v1/projects"
    );
  }

  async createProject(persona_id: string, name: string) {
    return this.request<{ id: string; name: string; status: string }>(
      "/api/v1/projects",
      { method: "POST", body: JSON.stringify({ persona_id, name }) }
    );
  }
}

export const apiClient = new ApiClient(API_BASE);

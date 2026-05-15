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

  async createBrief(input: {
    template_slug: string;
    title: string;
    product_name?: string;
    call_to_action?: string;
    tone?: string;
    target_duration?: number;
  }) {
    return this.request<{ id: string; template_slug: string; title: string }>(
      "/api/v1/briefs",
      { method: "POST", body: JSON.stringify(input) }
    );
  }

  async createProjectFromBrief(input: {
    persona_id: string;
    brief_id: string;
    source_clip_id?: string;
    name: string;
  }) {
    return this.request<{ id: string; name: string; status: string }>(
      "/api/v1/projects",
      { method: "POST", body: JSON.stringify(input) }
    );
  }

  async uploadVideo(persona_id: string, file: File) {
    const form = new FormData();
    form.append("persona_id", persona_id);
    form.append("file", file);
    return this.upload<{ id: string; file_path: string; media_type: string }>(
      "/api/v1/uploads/video",
      form
    );
  }

  async uploadVoice(persona_id: string, file: File, prompt_text?: string) {
    const form = new FormData();
    form.append("persona_id", persona_id);
    form.append("file", file);
    if (prompt_text) form.append("prompt_text", prompt_text);
    return this.upload<{ id: string; prompt_audio_path: string }>(
      "/api/v1/uploads/voice",
      form
    );
  }

  async runProject(project_id: string, template_slug = "product-review") {
    return this.request<{ project_id: string; status: string; stage: number }>(
      `/api/v1/projects/${project_id}/run`,
      { method: "POST", body: JSON.stringify({ template_slug }) }
    );
  }

  private async upload<T>(path: string, body: FormData): Promise<T> {
    const headers: Record<string, string> = {};
    const tok = this.token();
    if (tok) headers["Authorization"] = `Bearer ${tok}`;
    const res = await fetch(`${this.baseUrl}${path}`, { method: "POST", body, headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }
}

export const apiClient = new ApiClient(API_BASE);

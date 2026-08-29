/**
 * API client configuration and health check communication helpers.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface HealthResponse {
  status: string;
}

/**
 * Fetch health status from FastAPI backend
 */
export async function checkBackendHealth(): Promise<{
  success: boolean;
  data?: HealthResponse;
  error?: string;
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      headers: {
        "Accept": "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        success: false,
        error: `HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const data: HealthResponse = await response.json();
    return {
      success: true,
      data,
    };
  } catch (err: unknown) {
    const errorMessage =
      err instanceof Error ? err.message : "Failed to connect to backend server";
    return {
      success: false,
      error: errorMessage,
    };
  }
}

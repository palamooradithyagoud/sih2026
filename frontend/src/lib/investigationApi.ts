import {
  Case,
  CaseSummary,
  Person,
  CallRecord,
  Transaction,
  Location,
  Vehicle,
  Relationship,
  Organization,
  Evidence,
  GraphData,
  VerificationStatus,
  IntegrationStatus,
  SampleDocumentMeta,
  DocumentExtractionResult,
} from "@/types/investigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const PREFIX = `${API_BASE}/api/v1/investigation`;

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
      cache: "no-store",
    });
  } catch (netErr: any) {
    throw new Error(
      `Failed to connect to FastAPI backend at ${API_BASE}. Please ensure the backend server is running (e.g. 'uvicorn app.main:app --reload --port 8000'). Original error: ${netErr?.message || netErr}`
    );
  }

  if (!res.ok) {
    const errorBody = await res.text();
    let detailMsg = errorBody;
    try {
      const parsed = JSON.parse(errorBody);
      if (parsed.detail) detailMsg = parsed.detail;
    } catch {}
    throw new Error(`API Error [${res.status}]: ${detailMsg || res.statusText}`);
  }

  return res.json();
}

export const investigationApi = {
  // Cases & Summaries
  getCases: () => request<Case[]>(`${PREFIX}/cases`),
  getCase: (caseId: string) => request<Case>(`${PREFIX}/cases/${caseId}`),
  getCaseSummary: (caseId: string) => request<CaseSummary>(`${PREFIX}/cases/${caseId}/summary`),
  getCaseGraph: (caseId: string) => request<GraphData>(`${PREFIX}/cases/${caseId}/graph`),

  // Persons
  getPersons: (caseId: string) => request<Person[]>(`${PREFIX}/cases/${caseId}/persons`),
  addPerson: (caseId: string, data: Partial<Person>) =>
    request<Person>(`${PREFIX}/cases/${caseId}/persons`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Calls
  getCalls: (caseId: string) => request<CallRecord[]>(`${PREFIX}/cases/${caseId}/calls`),
  addCall: (caseId: string, data: Partial<CallRecord>) =>
    request<CallRecord>(`${PREFIX}/cases/${caseId}/calls`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  bulkImportCalls: (caseId: string, records: Partial<CallRecord>[]) =>
    request<CallRecord[]>(`${PREFIX}/cases/${caseId}/calls/bulk`, {
      method: "POST",
      body: JSON.stringify({ records }),
    }),

  // Transactions
  getTransactions: (caseId: string) => request<Transaction[]>(`${PREFIX}/cases/${caseId}/transactions`),
  addTransaction: (caseId: string, data: Partial<Transaction>) =>
    request<Transaction>(`${PREFIX}/cases/${caseId}/transactions`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  bulkImportTransactions: (caseId: string, records: Partial<Transaction>[]) =>
    request<Transaction[]>(`${PREFIX}/cases/${caseId}/transactions/bulk`, {
      method: "POST",
      body: JSON.stringify({ records }),
    }),

  // Locations
  getLocations: (caseId: string) => request<Location[]>(`${PREFIX}/cases/${caseId}/locations`),
  addLocation: (caseId: string, data: Partial<Location>) =>
    request<Location>(`${PREFIX}/cases/${caseId}/locations`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Vehicles
  getVehicles: (caseId: string) => request<Vehicle[]>(`${PREFIX}/cases/${caseId}/vehicles`),
  addVehicle: (caseId: string, data: Partial<Vehicle>) =>
    request<Vehicle>(`${PREFIX}/cases/${caseId}/vehicles`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Relationships
  getRelationships: (caseId: string) => request<Relationship[]>(`${PREFIX}/cases/${caseId}/relationships`),
  addRelationship: (caseId: string, data: Partial<Relationship>) =>
    request<Relationship>(`${PREFIX}/cases/${caseId}/relationships`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Organizations
  getOrganizations: (caseId: string) => request<Organization[]>(`${PREFIX}/cases/${caseId}/organizations`),
  addOrganization: (caseId: string, data: Partial<Organization>) =>
    request<Organization>(`${PREFIX}/cases/${caseId}/organizations`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Evidence
  getEvidence: (caseId: string) => request<Evidence[]>(`${PREFIX}/cases/${caseId}/evidence`),
  addEvidence: (caseId: string, data: Partial<Evidence>) =>
    request<Evidence>(`${PREFIX}/cases/${caseId}/evidence`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Verification Toggle
  updateVerification: (
    caseId: string,
    recordType: string,
    recordId: string,
    verificationStatus: VerificationStatus,
    officerId: string = "Officer ID 1024 (Insp. Adithya)"
  ) =>
    request<{ status: string; message: string }>(
      `${PREFIX}/cases/${caseId}/verify/${recordType}/${recordId}`,
      {
        method: "PATCH",
        body: JSON.stringify({
          verification_status: verificationStatus,
          officer_id: officerId,
        }),
      }
    ),

  // Groq AI & Document Knowledge Graph Extraction
  getIntegrationStatus: () =>
    request<IntegrationStatus>(`${PREFIX}/integrations/status`),

  getSampleDocuments: () =>
    request<SampleDocumentMeta[]>(`${PREFIX}/documents/samples`),

  uploadAndExtractDocument: async (formData: FormData): Promise<DocumentExtractionResult> => {
    let res: Response;
    try {
      res = await fetch(`${PREFIX}/documents/upload-and-extract`, {
        method: "POST",
        body: formData,
        cache: "no-store",
      });
    } catch (netErr: any) {
      throw new Error(
        `Failed to connect to FastAPI backend at ${API_BASE}. Please ensure the backend server is running (e.g. 'uvicorn app.main:app --reload --port 8000'). Original error: ${netErr?.message || netErr}`
      );
    }

    if (!res.ok) {
      const errorBody = await res.text();
      let detailMsg = errorBody;
      try {
        const parsed = JSON.parse(errorBody);
        if (parsed.detail) detailMsg = parsed.detail;
      } catch {}
      throw new Error(`Extraction Error [${res.status}]: ${detailMsg || res.statusText}`);
    }
    return res.json();
  },

  extractFromText: (payload: {
    document_text: string;
    document_name?: string;
    document_type?: string;
    case_id?: string;
    groq_api_key?: string;
  }) =>
    request<DocumentExtractionResult>(`${PREFIX}/documents/extract-text`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  extractSampleDocument: (
    sampleId: string,
    caseId?: string,
    groqApiKey?: string
  ) => {
    const params = new URLSearchParams();
    if (caseId) params.append("case_id", caseId);
    if (groqApiKey) params.append("groq_api_key", groqApiKey);
    const queryString = params.toString() ? `?${params.toString()}` : "";
    return request<DocumentExtractionResult>(
      `${PREFIX}/documents/sample-extract/${sampleId}${queryString}`,
      {
        method: "POST",
      }
    );
  },

  // Investigation Copilot (Phase 4)
  queryCopilot: (caseId: string, question: string, officerId?: string) =>
    request<import("@/types/investigation").CopilotQueryResponse>(
      `${API_BASE}/api/v1/investigation/ai/query`,
      {
        method: "POST",
        body: JSON.stringify({
          case_id: caseId,
          question,
          officer_id: officerId || "Officer ID 1024 (Insp. Adithya)",
        }),
      }
    ),
};


export type VerificationStatus = "VERIFIED" | "UNVERIFIED" | "UNDER_REVIEW";

export type PersonStatus =
  | "SUSPECT"
  | "PERSON_OF_INTEREST"
  | "ASSOCIATE"
  | "WITNESS"
  | "VICTIM";

export type RelationshipType =
  | "SAW_SUSPECT"
  | "EYEWITNESS"
  | "INFORMANT"
  | "ASSOCIATE"
  | "ACCOMPLICE"
  | "CO_CONSPIRATOR"
  | "CO_ACCUSED"
  | "VEHICLE_SIGHTING"
  | "LOCATION_SIGHTING"
  | "MEETING_ATTENDEE"
  | "KNOWN_CONTACT"
  | "BUSINESS_PARTNER"
  | "SPOUSE"
  | "PARENT"
  | "CHILD"
  | "SIBLING"
  | "GANG_MEMBER"
  | "LAWYER"
  | "VICTIM_OF";

export interface OfficerAuditBase {
  source: string;
  added_by_officer: string;
  verification_status: VerificationStatus;
  confidence_score: number;
  notes?: string;
}

export interface Case {
  id: string;
  case_number: string;
  title: string;
  description?: string;
  lead_officer: string;
  station: string;
  priority: string;
  created_at: string;
  status: string;
}

export interface Person extends OfficerAuditBase {
  id: string;
  case_id: string;
  name: string;
  dob?: string;
  gender?: string;
  address?: string;
  phone_numbers: string[];
  known_aliases: string[];
  occupation?: string;
  status: PersonStatus;
  connected_person_name?: string;
  connection_type?: string;
  connection_notes?: string;
  sighting_location?: string;
  sighting_date_time?: string;
  created_at: string;
}

export interface CallRecord extends OfficerAuditBase {
  id: string;
  case_id: string;
  caller_number: string;
  caller_name?: string;
  receiver_number: string;
  receiver_name?: string;
  date: string;
  time: string;
  duration_seconds: number;
  call_type: string;
  cell_tower_id?: string;
  created_at: string;
}

export interface Transaction extends OfficerAuditBase {
  id: string;
  case_id: string;
  sender_name: string;
  sender_account?: string;
  receiver_name: string;
  receiver_account?: string;
  amount: number;
  currency: string;
  date: string;
  time: string;
  transaction_id: string;
  bank_name: string;
  payment_type: string;
  created_at: string;
}

export interface Location extends OfficerAuditBase {
  id: string;
  case_id: string;
  name: string;
  address: string;
  latitude?: number;
  longitude?: number;
  date?: string;
  time?: string;
  associated_persons: string[];
  created_at: string;
}

export interface Vehicle extends OfficerAuditBase {
  id: string;
  case_id: string;
  registration_number: string;
  vehicle_type: string;
  make_model: string;
  color?: string;
  owner_name?: string;
  associated_persons: string[];
  created_at: string;
}

export interface Relationship extends OfficerAuditBase {
  id: string;
  case_id: string;
  person_a: string;
  person_b: string;
  relationship_type: RelationshipType;
  description?: string;
  created_at: string;
}

export interface Organization extends OfficerAuditBase {
  id: string;
  case_id: string;
  name: string;
  org_type: string;
  registration_number?: string;
  address?: string;
  key_persons: string[];
  created_at: string;
}

export interface Evidence extends OfficerAuditBase {
  id: string;
  case_id: string;
  title: string;
  file_name: string;
  evidence_type: string;
  description: string;
  date_obtained: string;
  custody_officer: string;
  created_at: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  subType?: string;
  verification_status: VerificationStatus;
  properties: Record<string, any>;
}

export interface GraphLink {
  id: string;
  source: string;
  target: string;
  label: string;
  verification_status: VerificationStatus;
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface CaseSummary {
  case_id: string;
  case_number: string;
  title: string;
  description?: string;
  lead_officer: string;
  station?: string;
  priority?: string;
  created_at?: string;
  total_persons: number;
  total_calls: number;
  total_transactions: number;
  total_amount_transferred: number;
  total_locations: number;
  total_vehicles: number;
  total_relationships: number;
  total_organizations: number;
  total_evidence: number;
  verified_count: number;
  unverified_count: number;
  under_review_count: number;
  verification_percentage: number;
}

export interface IntegrationStatus {
  groq: {
    configured: boolean;
    model: string;
    provider: string;
    ready: boolean;
  };
  postgres_supabase: {
    connected: boolean;
    is_supabase: boolean;
    target: string;
    details: Record<string, any>;
  };
  neo4j: {
    connected: boolean;
    uri: string;
  };
}

export interface SampleDocumentMeta {
  id: string;
  title: string;
  category: string;
  station: string;
  preview: string;
}

export interface DocumentCaseMeta {
  case_number?: string;
  title?: string;
  summary?: string;
  incident_date?: string;
  jurisdiction?: string;
  legal_sections?: string[];
}

export interface DocumentExtractionResult {
  status: string;
  case_id: string;
  document_name: string;
  document_type: string;
  is_ai_generated: boolean;
  model_used: string;
  case_meta: DocumentCaseMeta;
  added_counts: {
    persons: number;
    calls: number;
    transactions: number;
    locations: number;
    vehicles: number;
    organizations: number;
    relationships: number;
    evidence: number;
  };
  summary: CaseSummary;
  graph: GraphData;
}

// ── Phase 4: Investigation Copilot Types ────────────────────────────────────

export type InvestigationIntentType =
  | "find_call_connections"
  | "find_associates"
  | "find_person_connections"
  | "find_shared_entities"
  | "find_vehicle_connections"
  | "find_location_connections"
  | "find_organization_connections"
  | "find_bank_transaction_connections"
  | "find_case_connections"
  | "find_shortest_verified_path"
  | "investigation_timeline"
  | "entity_summary";

export interface ConnectionPathStep {
  source_id: string;
  source_name: string;
  source_type: string;
  relationship_type: string;
  target_id: string;
  target_name: string;
  target_type: string;
  verification_status: string;
}

export interface CopilotQueryRequest {
  case_id: string;
  question: string;
  officer_id?: string;
}

export interface CopilotQueryResponse {
  case_id: string;
  question: string;
  answer: string;
  query_type: InvestigationIntentType;
  confidence: "high" | "medium" | "low";
  results: Record<string, any>[];
  cypher: string;
  sources: Record<string, any>[];
  entities_found: string[];
  relationships_traversed: string[];
  connection_path: ConnectionPathStep[];
  ambiguity_notice?: string;
  graph_data?: GraphData;
}

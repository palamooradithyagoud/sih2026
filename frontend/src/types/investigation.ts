export type VerificationStatus = "VERIFIED" | "UNVERIFIED" | "UNDER_REVIEW";

export type PersonStatus =
  | "SUSPECT"
  | "PERSON_OF_INTEREST"
  | "ASSOCIATE"
  | "WITNESS"
  | "VICTIM";

export type RelationshipType =
  | "SPOUSE"
  | "PARENT"
  | "CHILD"
  | "SIBLING"
  | "ASSOCIATE"
  | "BUSINESS_PARTNER"
  | "KNOWN_CONTACT"
  | "GANG_MEMBER"
  | "CO_ACCUSED"
  | "LAWYER";

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
  lead_officer: string;
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

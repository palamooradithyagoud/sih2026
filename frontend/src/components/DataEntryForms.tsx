"use client";

import React, { useState } from "react";
import {
  X,
  User,
  PhoneCall,
  DollarSign,
  MapPin,
  Car,
  Users,
  Building2,
  FileText,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Clock,
} from "lucide-react";
import { investigationApi } from "@/lib/investigationApi";
import { VerificationStatus, PersonStatus, RelationshipType } from "@/types/investigation";

export type EntityTypeTab =
  | "person"
  | "call"
  | "transaction"
  | "location"
  | "vehicle"
  | "relationship"
  | "organization"
  | "evidence";

interface DataEntryFormsProps {
  caseId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialTab?: EntityTypeTab;
}

export default function DataEntryForms({
  caseId,
  isOpen,
  onClose,
  onSuccess,
  initialTab = "person",
}: DataEntryFormsProps) {
  const [activeTab, setActiveTab] = useState<EntityTypeTab>(initialTab);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Common Officer Metadata State
  const [source, setSource] = useState("Officer Field Investigation");
  const [addedBy, setAddedBy] = useState("Officer ID 1024 (Insp. Adithya)");
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus>("VERIFIED");
  const [confidenceScore, setConfidenceScore] = useState(0.95);
  const [officerNotes, setOfficerNotes] = useState("");

  // 1. Person Form State
  const [personName, setPersonName] = useState("");
  const [personDob, setPersonDob] = useState("");
  const [personGender, setPersonGender] = useState("Male");
  const [personAddress, setPersonAddress] = useState("");
  const [personPhones, setPersonPhones] = useState("");
  const [personAliases, setPersonAliases] = useState("");
  const [personOccupation, setPersonOccupation] = useState("");
  const [personStatus, setPersonStatus] = useState<PersonStatus>("SUSPECT");

  // 2. Call Record Form State
  const [callerNumber, setCallerNumber] = useState("");
  const [callerName, setCallerName] = useState("");
  const [receiverNumber, setReceiverNumber] = useState("");
  const [receiverName, setReceiverName] = useState("");
  const [callDate, setCallDate] = useState(new Date().toISOString().split("T")[0]);
  const [callTime, setCallTime] = useState("20:00:00");
  const [callDuration, setCallDuration] = useState(240);
  const [callType, setCallType] = useState("Outgoing");
  const [cellTower, setCellTower] = useState("HYD-TWR-884");

  // 3. Transaction Form State
  const [senderName, setSenderName] = useState("");
  const [senderAccount, setSenderAccount] = useState("HDFC-9912");
  const [txnReceiverName, setTxnReceiverName] = useState("");
  const [receiverAccount, setReceiverAccount] = useState("ICICI-4410");
  const [amount, setAmount] = useState(150000);
  const [txnDate, setTxnDate] = useState(new Date().toISOString().split("T")[0]);
  const [txnTime, setTxnTime] = useState("14:30:00");
  const [txnId, setTxnId] = useState(`TXN${Math.floor(100000 + Math.random() * 900000)}`);
  const [bankName, setBankName] = useState("HDFC Bank");
  const [paymentType, setPaymentType] = useState("Bank Transfer");

  // 4. Location Form State
  const [locName, setLocName] = useState("");
  const [locAddress, setLocAddress] = useState("");
  const [locLat, setLocLat] = useState(17.4156);
  const [locLng, setLocLng] = useState(78.4750);
  const [locPersons, setLocPersons] = useState("");

  // 5. Vehicle Form State
  const [vehReg, setVehReg] = useState("TS09AB1234");
  const [vehType, setVehType] = useState("SUV");
  const [vehModel, setVehModel] = useState("Toyota Innova");
  const [vehColor, setVehColor] = useState("White");
  const [vehOwner, setVehOwner] = useState("");
  const [vehDrivers, setVehDrivers] = useState("");

  // 6. Relationship Form State
  const [relPersonA, setRelPersonA] = useState("");
  const [relPersonB, setRelPersonB] = useState("");
  const [relType, setRelType] = useState<RelationshipType>("ASSOCIATE");
  const [relDesc, setRelDesc] = useState("");

  // 7. Organization Form State
  const [orgName, setOrgName] = useState("");
  const [orgType, setOrgType] = useState("Shell Company");
  const [orgReg, setOrgReg] = useState("CIN-U72200TG2026PTC00123");
  const [orgAddress, setOrgAddress] = useState("HITEC City, Hyderabad");
  const [orgPersons, setOrgPersons] = useState("");

  // 8. Evidence Form State
  const [evTitle, setEvTitle] = useState("");
  const [evFileName, setEvFileName] = useState("");
  const [evType, setEvType] = useState("Financial Record");
  const [evDesc, setEvDesc] = useState("");
  const [evDate, setEvDate] = useState(new Date().toISOString().split("T")[0]);
  const [evCustody, setEvCustody] = useState("Insp. Adithya");

  if (!isOpen) return null;

  const entityTabs = [
    { id: "person", label: "Person", icon: User },
    { id: "call", label: "Call (CDR)", icon: PhoneCall },
    { id: "transaction", label: "Transaction", icon: DollarSign },
    { id: "location", label: "Location", icon: MapPin },
    { id: "vehicle", label: "Vehicle", icon: Car },
    { id: "relationship", label: "Relationship", icon: Users },
    { id: "organization", label: "Organization", icon: Building2 },
    { id: "evidence", label: "Evidence", icon: FileText },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const auditData = {
      source,
      added_by_officer: addedBy,
      verification_status: verificationStatus,
      confidence_score: confidenceScore,
      notes: officerNotes || undefined,
    };

    try {
      if (activeTab === "person") {
        if (!personName.trim()) throw new Error("Person name is required");
        await investigationApi.addPerson(caseId, {
          ...auditData,
          name: personName.trim(),
          dob: personDob || undefined,
          gender: personGender,
          address: personAddress || undefined,
          phone_numbers: personPhones ? personPhones.split(",").map((p) => p.trim()) : [],
          known_aliases: personAliases ? personAliases.split(",").map((a) => a.trim()) : [],
          occupation: personOccupation || undefined,
          status: personStatus,
        });
        setPersonName("");
      } else if (activeTab === "call") {
        if (!callerNumber.trim() || !receiverNumber.trim())
          throw new Error("Both Caller and Receiver phone numbers are required");
        await investigationApi.addCall(caseId, {
          ...auditData,
          caller_number: callerNumber.trim(),
          caller_name: callerName.trim() || undefined,
          receiver_number: receiverNumber.trim(),
          receiver_name: receiverName.trim() || undefined,
          date: callDate,
          time: callTime,
          duration_seconds: Number(callDuration),
          call_type: callType,
          cell_tower_id: cellTower || undefined,
        });
        setCallerNumber("");
        setReceiverNumber("");
      } else if (activeTab === "transaction") {
        if (!senderName.trim() || !txnReceiverName.trim())
          throw new Error("Both Sender and Receiver names are required");
        await investigationApi.addTransaction(caseId, {
          ...auditData,
          sender_name: senderName.trim(),
          sender_account: senderAccount || undefined,
          receiver_name: txnReceiverName.trim(),
          receiver_account: receiverAccount || undefined,
          amount: Number(amount),
          currency: "INR",
          date: txnDate,
          time: txnTime,
          transaction_id: txnId,
          bank_name: bankName,
          payment_type: paymentType,
        });
        setTxnId(`TXN${Math.floor(100000 + Math.random() * 900000)}`);
      } else if (activeTab === "location") {
        if (!locName.trim()) throw new Error("Location name is required");
        await investigationApi.addLocation(caseId, {
          ...auditData,
          name: locName.trim(),
          address: locAddress.trim() || locName.trim(),
          latitude: Number(locLat),
          longitude: Number(locLng),
          associated_persons: locPersons ? locPersons.split(",").map((p) => p.trim()) : [],
        });
        setLocName("");
      } else if (activeTab === "vehicle") {
        if (!vehReg.trim()) throw new Error("Vehicle registration number is required");
        await investigationApi.addVehicle(caseId, {
          ...auditData,
          registration_number: vehReg.trim().toUpperCase(),
          vehicle_type: vehType,
          make_model: vehModel.trim(),
          color: vehColor || undefined,
          owner_name: vehOwner.trim() || undefined,
          associated_persons: vehDrivers ? vehDrivers.split(",").map((d) => d.trim()) : [],
        });
        setVehReg("");
      } else if (activeTab === "relationship") {
        if (!relPersonA.trim() || !relPersonB.trim())
          throw new Error("Both Person A and Person B are required");
        await investigationApi.addRelationship(caseId, {
          ...auditData,
          person_a: relPersonA.trim(),
          person_b: relPersonB.trim(),
          relationship_type: relType,
          description: relDesc || undefined,
        });
        setRelPersonA("");
        setRelPersonB("");
      } else if (activeTab === "organization") {
        if (!orgName.trim()) throw new Error("Organization name is required");
        await investigationApi.addOrganization(caseId, {
          ...auditData,
          name: orgName.trim(),
          org_type: orgType,
          registration_number: orgReg || undefined,
          address: orgAddress || undefined,
          key_persons: orgPersons ? orgPersons.split(",").map((p) => p.trim()) : [],
        });
        setOrgName("");
      } else if (activeTab === "evidence") {
        if (!evTitle.trim()) throw new Error("Evidence title is required");
        await investigationApi.addEvidence(caseId, {
          ...auditData,
          title: evTitle.trim(),
          file_name: evFileName.trim() || "document.pdf",
          evidence_type: evType,
          description: evDesc || evTitle,
          date_obtained: evDate,
          custody_officer: evCustody,
        });
        setEvTitle("");
      }

      setSuccessMsg("Investigation data committed to case database & knowledge graph!");
      onSuccess();
      setTimeout(() => {
        setSuccessMsg(null);
      }, 3000);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to save record");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content-large">
        {/* Modal Header */}
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <div className="card-icon-wrapper" style={{ width: 36, height: 36 }}>
              <ShieldCheck size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700 }}>Add Investigation Data</h2>
              <p style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>
                Standardized officer data entry with automated graph resolution
              </p>
            </div>
          </div>

          <button onClick={onClose} className="btn-icon" title="Close">
            <X size={20} />
          </button>
        </div>

        {/* Entity Type Tabs */}
        <div className="entity-tabs-grid">
          {entityTabs.map((tab) => {
            const Icon = tab.icon;
            const isSelected = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => {
                  setActiveTab(tab.id as EntityTypeTab);
                  setErrorMsg(null);
                  setSuccessMsg(null);
                }}
                className={`entity-tab-btn ${isSelected ? "active" : ""}`}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="modal-form-body">
          {successMsg && (
            <div className="alert-success">
              <CheckCircle2 size={16} /> {successMsg}
            </div>
          )}
          {errorMsg && (
            <div className="alert-error">
              <AlertCircle size={16} /> {errorMsg}
            </div>
          )}

          {/* 1. PERSON FORM */}
          {activeTab === "person" && (
            <div className="form-section-grid">
              <div className="form-group">
                <label className="form-label">Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Raj Kumar"
                  value={personName}
                  onChange={(e) => setPersonName(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Investigation Status</label>
                <select
                  value={personStatus}
                  onChange={(e) => setPersonStatus(e.target.value as PersonStatus)}
                  className="form-select"
                >
                  <option value="SUSPECT">Suspect</option>
                  <option value="PERSON_OF_INTEREST">Person of Interest</option>
                  <option value="ASSOCIATE">Associate</option>
                  <option value="WITNESS">Witness</option>
                  <option value="VICTIM">Victim</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Date of Birth (Optional)</label>
                <input
                  type="date"
                  value={personDob}
                  onChange={(e) => setPersonDob(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Gender</label>
                <select
                  value={personGender}
                  onChange={(e) => setPersonGender(e.target.value)}
                  className="form-select"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="form-group full-width">
                <label className="form-label">Residential / Known Address</label>
                <input
                  type="text"
                  placeholder="e.g. Road No. 12, Banjara Hills, Hyderabad"
                  value={personAddress}
                  onChange={(e) => setPersonAddress(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Phone Numbers (comma-separated)</label>
                <input
                  type="text"
                  placeholder="e.g. 9876543210, 9848011223"
                  value={personPhones}
                  onChange={(e) => setPersonPhones(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Known Aliases / Monikers</label>
                <input
                  type="text"
                  placeholder='e.g. "Raju", "The Boss"'
                  value={personAliases}
                  onChange={(e) => setPersonAliases(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group full-width">
                <label className="form-label">Occupation / Known Fronts</label>
                <input
                  type="text"
                  placeholder="e.g. Real Estate Developer / Logistics Import"
                  value={personOccupation}
                  onChange={(e) => setPersonOccupation(e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          )}

          {/* 2. CALL RECORD (CDR) FORM */}
          {activeTab === "call" && (
            <div className="form-section-grid">
              <div className="form-group">
                <label className="form-label">Caller Phone Number *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 9876543210"
                  value={callerNumber}
                  onChange={(e) => setCallerNumber(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Caller Identified Name (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Raj Kumar"
                  value={callerName}
                  onChange={(e) => setCallerName(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Receiver Phone Number *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 9988776655"
                  value={receiverNumber}
                  onChange={(e) => setReceiverNumber(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Receiver Identified Name (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Ahmed Khan"
                  value={receiverName}
                  onChange={(e) => setReceiverName(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Date of Call</label>
                <input
                  type="date"
                  value={callDate}
                  onChange={(e) => setCallDate(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Time of Call</label>
                <input
                  type="time"
                  step="1"
                  value={callTime}
                  onChange={(e) => setCallTime(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Duration (Seconds)</label>
                <input
                  type="number"
                  value={callDuration}
                  onChange={(e) => setCallDuration(Number(e.target.value))}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Call Type</label>
                <select
                  value={callType}
                  onChange={(e) => setCallType(e.target.value)}
                  className="form-select"
                >
                  <option value="Outgoing">Outgoing</option>
                  <option value="Incoming">Incoming</option>
                  <option value="Missed">Missed</option>
                  <option value="VoIP/WhatsApp">VoIP / WhatsApp</option>
                </select>
              </div>

              <div className="form-group full-width">
                <label className="form-label">Cell Tower ID / Location</label>
                <input
                  type="text"
                  placeholder="e.g. HYD-TWR-884 (Banjara Hills Sector 3)"
                  value={cellTower}
                  onChange={(e) => setCellTower(e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          )}

          {/* 3. TRANSACTION FORM */}
          {activeTab === "transaction" && (
            <div className="form-section-grid">
              <div className="form-group">
                <label className="form-label">Sender Name / Account Holder *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Raj Kumar"
                  value={senderName}
                  onChange={(e) => setSenderName(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Sender Account / UPI ID</label>
                <input
                  type="text"
                  placeholder="e.g. HDFC-9912"
                  value={senderAccount}
                  onChange={(e) => setSenderAccount(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Receiver Name / Beneficiary *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ahmed Khan"
                  value={txnReceiverName}
                  onChange={(e) => setTxnReceiverName(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Receiver Account / UPI ID</label>
                <input
                  type="text"
                  placeholder="e.g. ICICI-4410"
                  value={receiverAccount}
                  onChange={(e) => setReceiverAccount(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Amount (₹ INR) *</label>
                <input
                  type="number"
                  required
                  value={amount}
                  onChange={(e) => setAmount(Number(e.target.value))}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Transaction Mode</label>
                <select
                  value={paymentType}
                  onChange={(e) => setPaymentType(e.target.value)}
                  className="form-select"
                >
                  <option value="Bank Transfer">Bank Transfer (NEFT/RTGS)</option>
                  <option value="UPI / IMPS">UPI / IMPS</option>
                  <option value="Hawala Cash">Hawala / Unofficial Cash</option>
                  <option value="Cash Deposit">Cash Deposit</option>
                  <option value="Crypto USDT">Crypto USDT</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Transaction Reference ID</label>
                <input
                  type="text"
                  placeholder="e.g. TXN123456"
                  value={txnId}
                  onChange={(e) => setTxnId(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Bank / Platform Name</label>
                <input
                  type="text"
                  placeholder="e.g. HDFC Bank -> ICICI Bank"
                  value={bankName}
                  onChange={(e) => setBankName(e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          )}

          {/* 4. LOCATION FORM */}
          {activeTab === "location" && (
            <div className="form-section-grid">
              <div className="form-group full-width">
                <label className="form-label">Location / Landmark Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Hotel Grand Banjara"
                  value={locName}
                  onChange={(e) => setLocName(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group full-width">
                <label className="form-label">Full Address</label>
                <input
                  type="text"
                  placeholder="e.g. Road No. 1, Banjara Hills, Hyderabad"
                  value={locAddress}
                  onChange={(e) => setLocAddress(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={locLat}
                  onChange={(e) => setLocLat(Number(e.target.value))}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={locLng}
                  onChange={(e) => setLocLng(Number(e.target.value))}
                  className="form-input"
                />
              </div>

              <div className="form-group full-width">
                <label className="form-label">Associated Suspects / Persons (comma-separated)</label>
                <input
                  type="text"
                  placeholder="e.g. Raj Kumar, Ahmed Khan, Ravi Teja"
                  value={locPersons}
                  onChange={(e) => setLocPersons(e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          )}

          {/* 5. VEHICLE FORM */}
          {activeTab === "vehicle" && (
            <div className="form-section-grid">
              <div className="form-group">
                <label className="form-label">Registration Number *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. TS09AB1234"
                  value={vehReg}
                  onChange={(e) => setVehReg(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Vehicle Type</label>
                <select
                  value={vehType}
                  onChange={(e) => setVehType(e.target.value)}
                  className="form-select"
                >
                  <option value="SUV">SUV</option>
                  <option value="Car">Sedan / Hatchback</option>
                  <option value="Motorcycle">Motorcycle</option>
                  <option value="Truck">Commercial Truck / Van</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Make & Model *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Toyota Innova Crysta"
                  value={vehModel}
                  onChange={(e) => setVehModel(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Color</label>
                <input
                  type="text"
                  placeholder="e.g. Pearl White"
                  value={vehColor}
                  onChange={(e) => setVehColor(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Registered Owner Name</label>
                <input
                  type="text"
                  placeholder="e.g. Raj Kumar"
                  value={vehOwner}
                  onChange={(e) => setVehOwner(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Observed Drivers / Users</label>
                <input
                  type="text"
                  placeholder="e.g. Ahmed Khan"
                  value={vehDrivers}
                  onChange={(e) => setVehDrivers(e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          )}

          {/* 6. RELATIONSHIP FORM */}
          {activeTab === "relationship" && (
            <div className="form-section-grid">
              <div className="form-group">
                <label className="form-label">Person A *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Raj Kumar"
                  value={relPersonA}
                  onChange={(e) => setRelPersonA(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Person B *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Priya Kumar"
                  value={relPersonB}
                  onChange={(e) => setRelPersonB(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Relationship Connection Type *</label>
                <select
                  value={relType}
                  onChange={(e) => setRelType(e.target.value as RelationshipType)}
                  className="form-select"
                >
                  <option value="SPOUSE">Spouse</option>
                  <option value="PARENT">Parent</option>
                  <option value="CHILD">Child</option>
                  <option value="SIBLING">Sibling</option>
                  <option value="ASSOCIATE">Criminal Associate</option>
                  <option value="CO_ACCUSED">Co-Accused</option>
                  <option value="BUSINESS_PARTNER">Business Partner</option>
                  <option value="GANG_MEMBER">Syndicate Member</option>
                  <option value="LAWYER">Legal Counsel</option>
                </select>
              </div>

              <div className="form-group full-width">
                <label className="form-label">Relationship Context & Findings</label>
                <input
                  type="text"
                  placeholder="e.g. Married since 2012, joint signatory on shell company accounts"
                  value={relDesc}
                  onChange={(e) => setRelDesc(e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          )}

          {/* 7. ORGANIZATION FORM */}
          {activeTab === "organization" && (
            <div className="form-section-grid">
              <div className="form-group">
                <label className="form-label">Organization / Business Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Apex Global Logistics Pvt Ltd"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Entity Classification</label>
                <select
                  value={orgType}
                  onChange={(e) => setOrgType(e.target.value)}
                  className="form-select"
                >
                  <option value="Shell Company">Shell Company</option>
                  <option value="Commercial Business">Commercial Business</option>
                  <option value="Syndicate Gang">Syndicate Gang</option>
                  <option value="Trust / NGO">Trust / NGO</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">CIN / GST Registration No.</label>
                <input
                  type="text"
                  placeholder="e.g. CIN-U72200TG2020PTC145000"
                  value={orgReg}
                  onChange={(e) => setOrgReg(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Key Associated Persons</label>
                <input
                  type="text"
                  placeholder="e.g. Raj Kumar, Priya Kumar, Ahmed Khan"
                  value={orgPersons}
                  onChange={(e) => setOrgPersons(e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          )}

          {/* 8. EVIDENCE FORM */}
          {activeTab === "evidence" && (
            <div className="form-section-grid">
              <div className="form-group full-width">
                <label className="form-label">Evidence Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Bank Statement Analysis - August 2026"
                  value={evTitle}
                  onChange={(e) => setEvTitle(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">File Attachment Name</label>
                <input
                  type="text"
                  placeholder="e.g. bank_statement_raj_aug2026.pdf"
                  value={evFileName}
                  onChange={(e) => setEvFileName(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Evidence Type</label>
                <select
                  value={evType}
                  onChange={(e) => setEvType(e.target.value)}
                  className="form-select"
                >
                  <option value="Financial Record">Financial Record</option>
                  <option value="Call Detail Record (CDR)">Call Detail Record (CDR)</option>
                  <option value="CCTV Footage">CCTV Footage</option>
                  <option value="FIR & Legal Docket">FIR & Legal Docket</option>
                  <option value="Forensic Phone Dump">Forensic Phone Dump</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Date Obtained</label>
                <input
                  type="date"
                  value={evDate}
                  onChange={(e) => setEvDate(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Chain of Custody Officer</label>
                <input
                  type="text"
                  value={evCustody}
                  onChange={(e) => setEvCustody(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group full-width">
                <label className="form-label">Evidence Description & Summary</label>
                <textarea
                  rows={2}
                  placeholder="Detailed description of findings inside the document..."
                  value={evDesc}
                  onChange={(e) => setEvDesc(e.target.value)}
                  className="form-textarea"
                />
              </div>
            </div>
          )}

          {/* OFFICER INTEGRITY & VERIFICATION METADATA BLOCK */}
          <div className="officer-audit-box">
            <div className="officer-audit-header">
              <ShieldCheck size={16} style={{ color: "var(--accent-cyan)" }} />
              <span>Officer Verification & Intelligence Source Metadata</span>
            </div>

            <div className="form-section-grid" style={{ marginTop: "0.75rem" }}>
              <div className="form-group">
                <label className="form-label">Information Source *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Call Detail Record, Bank Statement, FIR, Anonymous Tip"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Added By Officer</label>
                <input
                  type="text"
                  required
                  value={addedBy}
                  onChange={(e) => setAddedBy(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Officer Verification Status</label>
                <select
                  value={verificationStatus}
                  onChange={(e) => setVerificationStatus(e.target.value as VerificationStatus)}
                  className="form-select"
                >
                  <option value="VERIFIED">✓ Officer Verified (Confirmed Intelligence)</option>
                  <option value="UNDER_REVIEW">⏳ Under Review (Pending Corroboration)</option>
                  <option value="UNVERIFIED">⚠ Unverified (Raw / Unconfirmed Tip)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">
                  Confidence Score: {Math.round(confidenceScore * 100)}%
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.05"
                  value={confidenceScore}
                  onChange={(e) => setConfidenceScore(Number(e.target.value))}
                  style={{ width: "100%", marginTop: "0.4rem" }}
                />
              </div>
            </div>
          </div>

          {/* Modal Footer Actions */}
          <div className="modal-footer">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
              disabled={submitting}
            >
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Saving & Connecting Graph..." : "Commit Investigation Data"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

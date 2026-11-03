"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Shield,
  Search,
  Brain,
  Globe,
  UserCheck,
  FileText,
  Mail,
  Layers,
  Terminal,
  MessageSquare,
  Building2,
  Compass,
  BarChart3,
  Cpu,
  Settings,
  CheckCircle2,
  AlertTriangle,
  Play,
  Pause,
  XCircle,
  Download,
  Upload,
  RefreshCw,
  ExternalLink,
  Plus,
  Lock,
  Sparkles,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type NavSection =
  | "Overview"
  | "Job Discovery"
  | "Job Intelligence"
  | "Visa Intelligence"
  | "Candidate Profile"
  | "CV Studio"
  | "Cover Letter Studio"
  | "Application Queue"
  | "Application Command Centre"
  | "Interview Intelligence"
  | "Employer Intelligence"
  | "Relocation Intelligence"
  | "Reports and Analytics"
  | "AI Project Manager"
  | "Settings";

const NAV_ITEMS: { name: NavSection; icon: React.ElementType; badge?: string }[] = [
  { name: "Overview", icon: Shield },
  { name: "Job Discovery", icon: Search, badge: "ATLAS" },
  { name: "Job Intelligence", icon: Brain, badge: "ORACLE" },
  { name: "Visa Intelligence", icon: Globe, badge: "LEXICON" },
  { name: "Candidate Profile", icon: UserCheck },
  { name: "CV Studio", icon: FileText, badge: "SCRIBE" },
  { name: "Cover Letter Studio", icon: Mail, badge: "SCRIBE" },
  { name: "Application Queue", icon: Layers, badge: "BULK" },
  { name: "Application Command Centre", icon: Terminal, badge: "CHRONICLE" },
  { name: "Interview Intelligence", icon: MessageSquare },
  { name: "Employer Intelligence", icon: Building2, badge: "SCOUT" },
  { name: "Relocation Intelligence", icon: Compass },
  { name: "Reports and Analytics", icon: BarChart3 },
  { name: "AI Project Manager", icon: Cpu, badge: "PM" },
  { name: "Settings", icon: Settings },
];

export default function ApplyCommandCentre() {
  const [activeSection, setActiveSection] = useState<NavSection>("Overview");
  const [bannerMessage, setBannerMessage] = useState<{ type: "info" | "success" | "error"; text: string } | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Core Data States
  const [overview, setOverview] = useState<any>(null);
  const [jobsData, setJobsData] = useState<any>({ total: 0, jobs: [], categories: [], sponsorship_statuses: [] });
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [visaData, setVisaData] = useState<any>(null);
  const [profileData, setProfileData] = useState<any>(null);
  const [cvVersions, setCvVersions] = useState<any[]>([]);
  const [coverLetters, setCoverLetters] = useState<any[]>([]);
  const [applications, setApplications] = useState<any[]>([]);
  const [bulkSummary, setBulkSummary] = useState<any>(null);
  const [employers, setEmployers] = useState<any[]>([]);
  const [interviewData, setInterviewData] = useState<any>(null);
  const [relocationData, setRelocationData] = useState<any>(null);
  const [pmData, setPmData] = useState<any>(null);
  const [settingsData, setSettingsData] = useState<any>(null);

  // Filter & Form States
  const [jobCountryFilter, setJobCountryFilter] = useState("All");
  const [jobArrangementFilter, setJobArrangementFilter] = useState("All");
  const [jobEnglishOnly, setJobEnglishOnly] = useState(true);
  const [jobSearchQuery, setJobSearchQuery] = useState("");
  const [liveDiscoveryQuery, setLiveDiscoveryQuery] = useState("cybersecurity");

  // New Job Ingestion Form
  const [newJobForm, setNewJobForm] = useState({
    title: "",
    employer_name: "",
    original_url: "",
    country: "United Kingdom",
    location: "London, UK",
    work_arrangement: "Hybrid",
    salary_text: "£35,000 - £42,000",
    description: "",
    required_skills: "Cybersecurity, SOC, SIEM, OSINT, Python",
    language_requirements: "English",
  });

  // Bulk Confirmation Modal/Checkbox
  const [bulkExplicitConfirm, setBulkExplicitConfirm] = useState(false);
  const [commandViewMode, setCommandViewMode] = useState<"kanban" | "table">("kanban");

  // Interview Mock State
  const [selectedInterviewTrack, setSelectedInterviewTrack] = useState("SOC Analyst");
  const [mockQuestion, setMockQuestion] = useState(
    "Walk through how you investigate a suspicious PowerShell execution alert in a SIEM."
  );
  const [mockAnswer, setMockAnswer] = useState("");
  const [mockFeedback, setMockFeedback] = useState<any>(null);

  // Relocation State
  const [selectedCity, setSelectedCity] = useState("London, United Kingdom");
  const [customGrossSalary, setCustomGrossSalary] = useState<string>("");

  const notify = (type: "info" | "success" | "error", text: string) => {
    setBannerMessage({ type, text });
    setTimeout(() => setBannerMessage(null), 6000);
  };

  const fetchAllCoreData = useCallback(async () => {
    try {
      const [ovRes, jobsRes, visaRes, profRes, cvRes, clRes, appRes, bulkRes, empRes, pmRes, setRes] =
        await Promise.all([
          fetch(`${API_BASE}/api/overview`).then((r) => r.json()),
          fetch(
            `${API_BASE}/api/jobs?country=${encodeURIComponent(jobCountryFilter)}&work_arrangement=${encodeURIComponent(
              jobArrangementFilter
            )}&english_only=${jobEnglishOnly}&search=${encodeURIComponent(jobSearchQuery)}`
          ).then((r) => r.json()),
          fetch(`${API_BASE}/api/visa/countries`).then((r) => r.json()),
          fetch(`${API_BASE}/api/profile`).then((r) => r.json()),
          fetch(`${API_BASE}/api/cv/versions`).then((r) => r.json()),
          fetch(`${API_BASE}/api/cover-letters`).then((r) => r.json()),
          fetch(`${API_BASE}/api/applications`).then((r) => r.json()),
          fetch(`${API_BASE}/api/applications/bulk/summary`).then((r) => r.json()),
          fetch(`${API_BASE}/api/employers`).then((r) => r.json()),
          fetch(`${API_BASE}/api/project-manager`).then((r) => r.json()),
          fetch(`${API_BASE}/api/settings`).then((r) => r.json()),
        ]);

      setOverview(ovRes);
      setJobsData(jobsRes);
      if (jobsRes.jobs?.length > 0 && !selectedJob) {
        setSelectedJob(jobsRes.jobs[0]);
      }
      setVisaData(visaRes);
      setProfileData(profRes);
      setCvVersions(cvRes.versions || []);
      setCoverLetters(clRes.cover_letters || []);
      setApplications(appRes.applications || []);
      setBulkSummary(bulkRes);
      setEmployers(empRes.employers || []);
      setPmData(pmRes);
      setSettingsData(setRes);
    } catch (err: any) {
      notify("error", `Backend connection warning: Ensure FastAPI server is running on ${API_BASE}`);
    }
  }, [jobCountryFilter, jobArrangementFilter, jobEnglishOnly, jobSearchQuery, selectedJob]);

  useEffect(() => {
    fetchAllCoreData();
  }, [fetchAllCoreData]);

  useEffect(() => {
    fetch(`${API_BASE}/api/interviews?role_track=${encodeURIComponent(selectedInterviewTrack)}`)
      .then((r) => r.json())
      .then(setInterviewData)
      .catch(() => {});
  }, [selectedInterviewTrack]);

  useEffect(() => {
    const q = customGrossSalary ? `&gross_annual=${encodeURIComponent(customGrossSalary)}` : "";
    fetch(`${API_BASE}/api/relocation?city=${encodeURIComponent(selectedCity)}${q}`)
      .then((r) => r.json())
      .then(setRelocationData)
      .catch(() => {});
  }, [selectedCity, customGrossSalary]);

  // Action Handlers
  const handleIngestManualJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...newJobForm,
          required_skills: newJobForm.required_skills.split(",").map((s) => s.trim()),
        }),
      }).then((r) => r.json());
      if (res.duplicate_prevented) {
        notify("info", `Duplicate prevented: Vacancy already exists (#${res.job.id}).`);
      } else {
        notify("success", `Ingested & scored "${res.job.title}" — Match: ${res.job.match_score}%`);
      }
      setSelectedJob(res.job);
      await fetchAllCoreData();
    } finally {
      setLoading(false);
    }
  };

  const handleLiveDiscovery = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/jobs/discover-live?query=${encodeURIComponent(liveDiscoveryQuery)}&limit=6`,
        { method: "POST" }
      ).then((r) => r.json());
      notify(
        "success",
        `ATLAS Live Discovery completed: +${res.new_jobs_added} new vacancies, ${res.duplicates_skipped} duplicates skipped.`
      );
      await fetchAllCoreData();
    } finally {
      setLoading(false);
    }
  };

  const handleTailorCV = async (jobId: number) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/cv/tailor/${jobId}`, { method: "POST" }).then((r) => r.json());
      notify("success", `SCRIBE generated "${res.version_name}" (ATS Coverage: ${res.ats_keyword_coverage}%).`);
      await fetchAllCoreData();
      setActiveSection("CV Studio");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCoverLetter = async (jobId: number) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/cover-letters/generate/${jobId}`, { method: "POST" }).then((r) =>
        r.json()
      );
      notify("success", `SCRIBE generated "${res.title}".`);
      await fetchAllCoreData();
      setActiveSection("Cover Letter Studio");
    } finally {
      setLoading(false);
    }
  };

  const handlePrepareApplication = async (jobId: number) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/applications/prepare/${jobId}`, { method: "POST" }).then((r) =>
        r.json()
      );
      notify("success", `APPLYBOT prepared Application #${res.id} (Stage: ${res.stage}). Ready for human review.`);
      await fetchAllCoreData();
      setActiveSection("Application Queue");
    } finally {
      setLoading(false);
    }
  };

  const handleApproveApplication = async (appId: number) => {
    const res = await fetch(`${API_BASE}/api/applications/${appId}/approve`, { method: "POST" }).then((r) => r.json());
    notify("success", `Human approval locked for Application #${appId} (SHA-256 Hash: ${res.approval_hash?.slice(0, 10)}...)`);
    await fetchAllCoreData();
  };

  const handleSingleSubmit = async (appId: number) => {
    const res = await fetch(`${API_BASE}/api/applications/${appId}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ simulated_page_content: "", simulate_network_error: false }),
    }).then((r) => r.json());

    if (res.status === "submitted") {
      notify("success", `Submitted Application #${appId}! Confirmation Ref: ${res.confirmation_reference}`);
    } else {
      notify("error", `Submission halted (${res.status}): ${res.reason}`);
    }
    await fetchAllCoreData();
  };

  const handleBulkSubmitApproved = async () => {
    if (!bulkExplicitConfirm) {
      notify("error", "Please check the explicit final confirmation box before running bulk submission.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/applications/bulk/submit-approved`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ explicit_final_confirmation: true }),
      }).then((r) => r.json());
      notify(
        "success",
        `Bulk Submission Complete: ${res.submitted_count} submitted, ${res.blocked_count} blocked, ${res.failed_or_paused_count} paused/failed.`
      );
      setBulkExplicitConfirm(false);
      await fetchAllCoreData();
    } finally {
      setLoading(false);
    }
  };

  const handleQueueControl = async (action: "pause" | "resume" | "cancel") => {
    const res = await fetch(`${API_BASE}/api/applications/bulk/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    }).then((r) => r.json());
    notify("info", `Bulk Queue state changed to: ${res.queue_state.toUpperCase()}`);
    await fetchAllCoreData();
  };

  const handleUploadCVFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/api/cv/upload`, {
      method: "POST",
      body: formData,
    });
    if (res.ok) {
      const data = await res.json();
      notify("success", `Uploaded Master CV "${data.version_name}" (${data.extracted_skills.length} skills extracted).`);
      await fetchAllCoreData();
    } else {
      const err = await res.json();
      notify("error", err.detail || "Upload failed.");
    }
  };

  const handleEvaluateMockAnswer = async () => {
    if (!mockAnswer.trim()) return;
    const res = await fetch(`${API_BASE}/api/interviews/mock-evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: mockQuestion, candidate_answer: mockAnswer }),
    }).then((r) => r.json());
    setMockFeedback(res);
  };

  return (
    <div className="min-h-screen flex bg-[#050914] text-slate-100">
      {/* LEFT COMMAND SIDEBAR */}
      <aside className="w-72 bg-[#080e1e] border-r border-sky-900/40 flex flex-col shrink-0">
        <div className="p-5 border-b border-sky-900/40 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-sky-500/15 border border-sky-400/40 flex items-center justify-center relative">
            <Shield className="w-5 h-5 text-sky-400" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold tracking-wider text-lg text-white">APPLY</h1>
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                v1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono">RECRUITMENT & VISA INTEL</p>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-3 px-2.5 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = activeSection === item.name;
            return (
              <button
                key={item.name}
                onClick={() => setActiveSection(item.name)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  active
                    ? "bg-sky-500/20 text-sky-300 border border-sky-500/40 shadow-sm"
                    : "text-slate-400 hover:bg-slate-900/80 hover:text-slate-200 border border-transparent"
                }`}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <Icon className={`w-4 h-4 shrink-0 ${active ? "text-sky-400" : "text-slate-500"}`} />
                  <span className="truncate">{item.name}</span>
                </div>
                {item.badge && (
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-900 text-amber-400 border border-amber-500/30">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* UK GRADUATE VISA STATUS TELEMETRY FOOTER */}
        <div className="p-3.5 m-2.5 rounded-lg bg-[#050914] border border-sky-900/50 text-[11px] space-y-1.5">
          <div className="flex items-center justify-between text-amber-400 font-mono font-semibold">
            <span>IMMIGRATION GUARD</span>
            <Lock className="w-3.5 h-3.5" />
          </div>
          <p className="text-slate-300">
            UK Status: <span className="text-sky-300 font-medium">{profileData?.immigration?.uk_immigration_status || "Graduate visa"}</span>
          </p>
          <p className="text-slate-400">
            UK Expiry: <span className="text-amber-300 font-mono">{profileData?.immigration?.uk_visa_expiry_date || "2027-10-31"}</span>
          </p>
          <p className="text-[10px] text-emerald-400">India: Unrestricted Right to Work</p>
        </div>
      </aside>

      {/* MAIN OPERATIONS VIEWPORT */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* TOP COMMAND HEADER */}
        <header className="h-16 bg-[#080e1e]/90 border-b border-sky-900/40 px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono uppercase tracking-widest text-sky-400">MODULE //</span>
            <h2 className="text-lg font-semibold text-white">{activeSection}</h2>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
              Candidate: <strong className="text-sky-300">{profileData?.profile?.full_name || "Adi Zala"}</strong> (MSc Cybersecurity &apos;25)
            </span>
            <button
              onClick={fetchAllCoreData}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-sky-500/15 hover:bg-sky-500/25 border border-sky-500/40 text-sky-300 text-xs font-medium"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              Sync Telemetry
            </button>
          </div>
        </header>

        {/* NOTIFICATION BANNER */}
        {bannerMessage && (
          <div
            className={`px-6 py-2.5 text-xs font-mono flex items-center justify-between border-b ${
              bannerMessage.type === "error"
                ? "bg-red-950/80 border-red-700 text-red-200"
                : bannerMessage.type === "success"
                ? "bg-emerald-950/80 border-emerald-700 text-emerald-200"
                : "bg-sky-950/80 border-sky-700 text-sky-200"
            }`}
          >
            <span>{bannerMessage.text}</span>
            <button onClick={() => setBannerMessage(null)} className="text-slate-400 hover:text-white">
              ✕
            </button>
          </div>
        )}

        {/* DYNAMIC MODULE CONTENT */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* ==============================================================
              1. OVERVIEW DASHBOARD
          ============================================================== */}
          {activeSection === "Overview" && overview && (
            <div className="space-y-6">
              {/* Immigration & Policy Alert Strip */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-[#0a1329] to-[#0f1d3d] border border-sky-500/30 flex flex-wrap items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 text-[10px] font-mono uppercase rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                      LEXICON IMMIGRATION ACTIVE
                    </span>
                    <h3 className="text-sm font-semibold text-white">
                      UK Graduate Visa Valid Until {overview.immigration_alert?.uk_visa_expiry_date} | Indian National
                    </h3>
                  </div>
                  <p className="text-xs text-slate-300">{overview.immigration_alert?.uk_policy_note}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setActiveSection("Job Discovery")}
                    className="px-3 py-1.5 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs"
                  >
                    Discover Jobs
                  </button>
                  <button
                    onClick={() => setActiveSection("Application Queue")}
                    className="px-3 py-1.5 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 font-semibold text-xs"
                  >
                    Approval Queue ({overview.metrics.applications_awaiting_approval})
                  </button>
                </div>
              </div>

              {/* 12 Live Telemetry KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3.5">
                {[
                  { label: "Total Jobs Discovered", val: overview.metrics.total_jobs_discovered, color: "text-sky-400" },
                  { label: "New Jobs Today", val: overview.metrics.new_jobs_today, color: "text-emerald-400" },
                  { label: "Matching Profile", val: overview.metrics.jobs_matching_profile, color: "text-sky-300" },
                  { label: "High-Match (78%+)", val: overview.metrics.high_match_opportunities, color: "text-amber-400" },
                  { label: "Sponsorship Confirmed", val: overview.metrics.sponsorship_confirmed_opportunities, color: "text-emerald-400" },
                  { label: "Sponsorship Unverified", val: overview.metrics.sponsorship_unverified_opportunities, color: "text-amber-300" },
                  { label: "In Preparation", val: overview.metrics.applications_in_preparation, color: "text-slate-300" },
                  { label: "Awaiting Approval", val: overview.metrics.applications_awaiting_approval, color: "text-amber-400" },
                  { label: "Approved & Ready", val: overview.metrics.applications_approved_ready, color: "text-sky-400" },
                  { label: "Submitted", val: overview.metrics.applications_submitted, color: "text-emerald-400" },
                  { label: "Interviews Scheduled", val: overview.metrics.interviews_scheduled, color: "text-sky-300" },
                  { label: "Upcoming Follow-Ups", val: overview.metrics.upcoming_follow_ups, color: "text-amber-300" },
                ].map((kpi) => (
                  <div key={kpi.label} className="p-3.5 rounded-xl bg-[#0a0f1e] border border-slate-800/80">
                    <p className="text-[11px] text-slate-400 truncate">{kpi.label}</p>
                    <p className={`text-2xl font-bold font-mono mt-1 ${kpi.color}`}>{kpi.val}</p>
                  </div>
                ))}
              </div>

              {/* Distribution Panels */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-3">
                  <h4 className="text-xs font-mono uppercase tracking-wider text-sky-400">Country-Wise Opportunities</h4>
                  <div className="space-y-2">
                    {overview.country_distribution.map((c: any) => (
                      <div key={c.country} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span>{c.country}</span>
                          <span className="font-mono text-sky-300">{c.count}</span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-900 rounded overflow-hidden">
                          <div
                            className="h-full bg-sky-500"
                            style={{ width: `${Math.min(100, (c.count / Math.max(1, overview.metrics.total_jobs_discovered)) * 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-3">
                  <h4 className="text-xs font-mono uppercase tracking-wider text-amber-400">Sponsorship Classification</h4>
                  <div className="space-y-2">
                    {overview.sponsorship_distribution.map((s: any) => (
                      <div key={s.status} className="flex items-center justify-between text-xs py-1 border-b border-slate-900">
                        <span className="text-slate-300 truncate pr-2">{s.status}</span>
                        <span className="font-mono px-2 py-0.5 rounded bg-slate-900 text-amber-300">{s.count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-3">
                  <h4 className="text-xs font-mono uppercase tracking-wider text-emerald-400">Match Score Distribution</h4>
                  <div className="space-y-2">
                    {overview.match_distribution.map((m: any) => (
                      <div key={m.bucket} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-900">
                        <span className="text-slate-300">{m.bucket}</span>
                        <span className="font-mono px-2 py-0.5 rounded bg-slate-900 text-emerald-300">{m.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recent Job Discoveries & Live Audit Trail */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-mono uppercase tracking-wider text-sky-400">Recent Job Discoveries</h4>
                    <button onClick={() => setActiveSection("Job Discovery")} className="text-xs text-sky-400 hover:underline">
                      View All →
                    </button>
                  </div>
                  <div className="space-y-2.5">
                    {overview.recent_jobs.map((j: any) => (
                      <div
                        key={j.id}
                        className="p-3 rounded-lg bg-[#050914] border border-slate-800/80 flex items-center justify-between gap-3"
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            {j.is_demo && (
                              <span className="px-1.5 py-0.5 text-[9px] font-mono rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                                DEMO
                              </span>
                            )}
                            <p className="text-xs font-semibold text-white truncate">{j.title}</p>
                          </div>
                          <p className="text-[11px] text-slate-400 truncate">
                            {j.employer_name} • {j.country} ({j.work_arrangement}) • {j.sponsorship_status}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <span
                            className={`text-xs font-mono font-bold px-2 py-1 rounded ${
                              j.match_score >= 78
                                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                                : j.match_score >= 55
                                ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                                : "bg-red-500/20 text-red-300 border border-red-500/40"
                            }`}
                          >
                            {j.match_score}%
                          </span>
                          <button
                            onClick={() => handlePrepareApplication(j.id)}
                            className="px-2.5 py-1 rounded bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/40 text-[11px]"
                          >
                            Prepare
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-3">
                  <h4 className="text-xs font-mono uppercase tracking-wider text-amber-400">Recruitment Activity & Audit Timeline</h4>
                  <div className="space-y-2 max-h-80 overflow-y-auto">
                    {overview.recent_activity.map((act: any) => (
                      <div key={act.id} className="p-2.5 rounded bg-[#050914] border border-slate-900 text-xs flex justify-between">
                        <div>
                          <span className="font-mono text-sky-400">[{act.actor}]</span>{" "}
                          <span className="font-semibold text-slate-200">{act.action}</span>{" "}
                          <span className="text-slate-400">({act.entity_type} #{act.entity_id})</span>
                        </div>
                        <span className="text-[10px] font-mono text-slate-500">{act.created_at.slice(0, 19)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ==============================================================
              2. GLOBAL JOB DISCOVERY ENGINE (ATLAS)
          ============================================================== */}
          {activeSection === "Job Discovery" && (
            <div className="space-y-6">
              {/* Live Public API Discovery & Filters Bar */}
              <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <h3 className="text-sm font-semibold text-white">ATLAS — Legal Multi-Source Job Discovery Engine</h3>
                    <p className="text-xs text-slate-400">
                      Respects robots.txt and rate limits. Deduplicates across Employer, Title, Location, and URL.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={liveDiscoveryQuery}
                      onChange={(e) => setLiveDiscoveryQuery(e.target.value)}
                      placeholder="Keyword (e.g. soc, cybersecurity, osint)"
                      className="px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs text-white"
                    />
                    <button
                      onClick={handleLiveDiscovery}
                      disabled={loading}
                      className="flex items-center gap-1.5 px-3.5 py-1.5 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      Fetch Live Public APIs (Remotive & Arbeitnow)
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-2 border-t border-slate-800/80">
                  <input
                    type="text"
                    value={jobSearchQuery}
                    onChange={(e) => setJobSearchQuery(e.target.value)}
                    placeholder="Filter by title, skill, employer..."
                    className="px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                  />
                  <select
                    value={jobCountryFilter}
                    onChange={(e) => setJobCountryFilter(e.target.value)}
                    className="px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                  >
                    <option value="All">All Countries</option>
                    <option value="United Kingdom">United Kingdom</option>
                    <option value="India">India</option>
                    <option value="Germany">Germany</option>
                    <option value="Ireland">Ireland</option>
                    <option value="Netherlands">Netherlands</option>
                    <option value="United Arab Emirates">United Arab Emirates</option>
                    <option value="Canada">Canada</option>
                    <option value="Australia">Australia</option>
                    <option value="New Zealand">New Zealand</option>
                  </select>
                  <select
                    value={jobArrangementFilter}
                    onChange={(e) => setJobArrangementFilter(e.target.value)}
                    className="px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                  >
                    <option value="All">All Work Arrangements</option>
                    <option value="Remote">Remote</option>
                    <option value="Hybrid">Hybrid</option>
                    <option value="On-site">On-site</option>
                  </select>
                  <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={jobEnglishOnly}
                      onChange={(e) => setJobEnglishOnly(e.target.checked)}
                      className="rounded border-slate-600"
                    />
                    English-Acceptable Roles Only
                  </label>
                </div>
              </div>

              {/* Discovered Vacancies List */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-3">
                  {jobsData.jobs?.map((j: any) => (
                    <div
                      key={j.id}
                      className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 hover:border-sky-500/40 transition-all space-y-2.5"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            {j.is_demo && (
                              <span className="px-1.5 py-0.5 text-[10px] font-mono rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                                DEMO
                              </span>
                            )}
                            <h4 className="text-sm font-semibold text-white">{j.title}</h4>
                            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 text-sky-300">
                              {j.country}
                            </span>
                            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-300">
                              {j.work_arrangement}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {j.employer_name} • {j.location} • <span className="text-amber-300">{j.salary_text}</span>
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          <span
                            className={`text-sm font-mono font-bold px-2.5 py-1 rounded ${
                              j.match_score >= 78
                                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                                : j.match_score >= 55
                                ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                                : "bg-red-500/20 text-red-300 border border-red-500/40"
                            }`}
                          >
                            {j.match_score}% Match
                          </span>
                        </div>
                      </div>

                      <p className="text-xs text-slate-300 line-clamp-2">{j.description}</p>

                      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-900 text-[11px]">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-amber-300 font-mono">
                            Sponsorship: {j.sponsorship_status}
                          </span>
                          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                            {j.language_requirements}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              setSelectedJob(j);
                              setActiveSection("Job Intelligence");
                            }}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200"
                          >
                            Inspect Match & Visa
                          </button>
                          <button
                            onClick={() => handleTailorCV(j.id)}
                            className="px-2.5 py-1 rounded bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/40"
                          >
                            Tailor CV
                          </button>
                          <button
                            onClick={() => handlePrepareApplication(j.id)}
                            className="px-2.5 py-1 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40"
                          >
                            Prepare Application
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Ingest New Vacancy Form */}
                <form
                  onSubmit={handleIngestManualJob}
                  className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-3 h-fit"
                >
                  <h4 className="text-xs font-mono uppercase tracking-wider text-sky-400">
                    + Ingest Vacancy for Intelligence Analysis
                  </h4>
                  <input
                    required
                    placeholder="Job Title (e.g. Junior SOC Analyst)"
                    value={newJobForm.title}
                    onChange={(e) => setNewJobForm({ ...newJobForm, title: e.target.value })}
                    className="w-full px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                  />
                  <input
                    required
                    placeholder="Employer Name"
                    value={newJobForm.employer_name}
                    onChange={(e) => setNewJobForm({ ...newJobForm, employer_name: e.target.value })}
                    className="w-full px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                  />
                  <input
                    required
                    placeholder="Original Job URL"
                    value={newJobForm.original_url}
                    onChange={(e) => setNewJobForm({ ...newJobForm, original_url: e.target.value })}
                    className="w-full px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      value={newJobForm.country}
                      onChange={(e) => setNewJobForm({ ...newJobForm, country: e.target.value })}
                      className="px-2.5 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                    >
                      <option value="United Kingdom">United Kingdom</option>
                      <option value="India">India</option>
                      <option value="Germany">Germany</option>
                      <option value="Ireland">Ireland</option>
                      <option value="Netherlands">Netherlands</option>
                      <option value="United Arab Emirates">United Arab Emirates</option>
                      <option value="Canada">Canada</option>
                      <option value="Australia">Australia</option>
                      <option value="New Zealand">New Zealand</option>
                    </select>
                    <select
                      value={newJobForm.work_arrangement}
                      onChange={(e) => setNewJobForm({ ...newJobForm, work_arrangement: e.target.value })}
                      className="px-2.5 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                    >
                      <option value="Hybrid">Hybrid</option>
                      <option value="Remote">Remote</option>
                      <option value="On-site">On-site</option>
                    </select>
                  </div>
                  <input
                    placeholder="Required Skills (comma-separated)"
                    value={newJobForm.required_skills}
                    onChange={(e) => setNewJobForm({ ...newJobForm, required_skills: e.target.value })}
                    className="w-full px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                  />
                  <textarea
                    required
                    rows={4}
                    placeholder="Paste full job description (ORACLE & LEXICON will evaluate skills, language, and sponsorship rules)..."
                    value={newJobForm.description}
                    onChange={(e) => setNewJobForm({ ...newJobForm, description: e.target.value })}
                    className="w-full px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                  />
                  <button
                    type="submit"
                    className="w-full py-2 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs"
                  >
                    Evaluate & Store Vacancy
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* ==============================================================
              3. JOB INTELLIGENCE & AI MATCHING ENGINE (ORACLE)
          ============================================================== */}
          {activeSection === "Job Intelligence" && (
            <div className="space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-[#0a0f1e] border border-slate-800">
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    ORACLE — Transparent Weighted Compatibility & Barrier Analysis
                  </h3>
                  <p className="text-xs text-slate-400">
                    Weights: Skills 30% • Experience 20% • Education 15% • Suitability 15% • Language 10% • Immigration 10%
                  </p>
                </div>
                <select
                  value={selectedJob?.id || ""}
                  onChange={(e) => {
                    const found = jobsData.jobs?.find((j: any) => j.id === Number(e.target.value));
                    if (found) setSelectedJob(found);
                  }}
                  className="px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                >
                  {jobsData.jobs?.map((j: any) => (
                    <option key={j.id} value={j.id}>
                      {j.title} — {j.employer_name} ({j.country}) [{j.match_score}%]
                    </option>
                  ))}
                </select>
              </div>

              {selectedJob && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Left: Component Score Breakdown */}
                  <div className="p-5 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-xs font-mono text-slate-400">OVERALL COMPATIBILITY</span>
                        <p className="text-3xl font-bold font-mono text-sky-400">{selectedJob.match_score}%</p>
                      </div>
                      <span
                        className={`px-2.5 py-1 rounded text-xs font-mono ${
                          selectedJob.match_breakdown?.should_apply
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                            : "bg-red-500/20 text-red-300 border border-red-500/40"
                        }`}
                      >
                        {selectedJob.match_breakdown?.recommendation}
                      </span>
                    </div>

                    <div className="space-y-2.5 pt-2 border-t border-slate-800">
                      {Object.entries(selectedJob.match_breakdown?.component_scores || {}).map(([key, val]: any) => (
                        <div key={key} className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="capitalize text-slate-300">{key.replace(/_/g, " ")}</span>
                            <span className="font-mono text-sky-300">{val}%</span>
                          </div>
                          <div className="w-full h-1.5 bg-slate-900 rounded overflow-hidden">
                            <div className="h-full bg-sky-500" style={{ width: `${val}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="pt-3 border-t border-slate-800 space-y-2">
                      <p className="text-xs font-mono text-emerald-400">
                        Matched Skills: {(selectedJob.match_breakdown?.matched_skills || []).join(", ") || "General Fit"}
                      </p>
                      {selectedJob.match_breakdown?.missing_skills?.length > 0 && (
                        <p className="text-xs font-mono text-amber-300">
                          Unconfirmed / Missing Skills: {selectedJob.match_breakdown.missing_skills.join(", ")}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Right 2 Columns: AI Explanation & Visa Assessment */}
                  <div className="lg:col-span-2 space-y-4">
                    <div className="p-5 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-3">
                      <h4 className="text-xs font-mono uppercase tracking-wider text-sky-400">
                        ORACLE Diagnostic Explanation — {selectedJob.title}
                      </h4>
                      <div className="space-y-2 text-xs">
                        <p className="font-semibold text-emerald-300">Why Candidate Matches:</p>
                        <ul className="list-disc pl-5 space-y-1 text-slate-300">
                          {(selectedJob.match_breakdown?.ai_explanation?.why_matches || []).map((m: string, i: number) => (
                            <li key={i}>{m}</li>
                          ))}
                        </ul>

                        <p className="font-semibold text-amber-300 pt-2">Potential Concerns / Barriers:</p>
                        <ul className="list-disc pl-5 space-y-1 text-slate-300">
                          {(selectedJob.match_breakdown?.ai_explanation?.why_might_not_match || []).map(
                            (m: string, i: number) => (
                              <li key={i}>{m}</li>
                            )
                          )}
                        </ul>

                        <p className="font-semibold text-sky-300 pt-2">What Needs Verification Before Applying:</p>
                        <ul className="list-disc pl-5 space-y-1 text-slate-300">
                          {(selectedJob.match_breakdown?.ai_explanation?.verification_checklist || []).map(
                            (m: string, i: number) => (
                              <li key={i}>{m}</li>
                            )
                          )}
                        </ul>
                      </div>
                    </div>

                    <div className="p-5 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-2 text-xs">
                      <h4 className="text-xs font-mono uppercase tracking-wider text-amber-400">
                        LEXICON Vacancy Immigration & Sponsorship Verdict
                      </h4>
                      <p className="text-slate-200 font-medium">{selectedJob.visa_assessment?.eligibility_summary}</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-2 text-slate-400">
                        <p>
                          Route: <span className="text-slate-200">{selectedJob.visa_assessment?.current_visa_route}</span>
                        </p>
                        <p>
                          Sponsorship Status:{" "}
                          <span className="text-amber-300 font-mono">{selectedJob.sponsorship_status}</span>
                        </p>
                        <p>
                          Salary Rule: <span className="text-slate-200">{selectedJob.visa_assessment?.salary_requirements}</span>
                        </p>
                        <p>
                          Official Reference:{" "}
                          <a
                            href={selectedJob.visa_assessment?.official_government_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-sky-400 underline"
                          >
                            {selectedJob.visa_assessment?.authority_name}
                          </a>
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ==============================================================
              4. VISA & IMMIGRATION INTELLIGENCE (LEXICON)
          ============================================================== */}
          {activeSection === "Visa Intelligence" && visaData && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-[#0a0f1e] border border-sky-500/30 space-y-2">
                <h3 className="text-sm font-semibold text-white">
                  LEXICON — Official Government Immigration & Sponsorship Authority Matrix
                </h3>
                <p className="text-xs text-slate-300">
                  UK Policy: Apply for suitable UK jobs without sponsorship while Graduate visa is valid (until{" "}
                  <strong className="text-amber-300">{visaData.candidate_immigration.uk_visa_expiry_date}</strong>);
                  prioritise licensed Skilled Worker sponsors for post-2027 transition. India Policy: Unrestricted right to
                  work. All other countries: Prioritise verified employer sponsorship.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {visaData.countries.map((c: any) => (
                  <div
                    key={c.id}
                    className={`p-4 rounded-xl bg-[#0a0f1e] border space-y-2.5 text-xs ${
                      c.is_priority ? "border-sky-500/40" : "border-slate-800"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-bold text-white">{c.country}</h4>
                        {c.is_priority && (
                          <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-sky-500/20 text-sky-300 border border-sky-500/40">
                            PRIORITY
                          </span>
                        )}
                      </div>
                      <a
                        href={c.official_source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-sky-400 hover:underline font-mono text-[11px]"
                      >
                        {c.authority_name} <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>

                    <p className="text-amber-300 font-mono text-[11px]">Route: {c.primary_visa_route}</p>
                    <p className="text-slate-300">{c.current_candidate_eligibility_status}</p>
                    <div className="space-y-1 text-[11px] text-slate-400 pt-2 border-t border-slate-900">
                      <p>
                        <strong className="text-slate-200">Salary Threshold:</strong> {c.salary_threshold_info}
                      </p>
                      <p>
                        <strong className="text-slate-200">Occupation Eligibility:</strong> {c.occupation_eligibility_info}
                      </p>
                      <p>
                        <strong className="text-slate-200">Labour Market Test:</strong> {c.labour_market_test_info}
                      </p>
                      <p>
                        <strong className="text-slate-200">Estimated Visa Costs:</strong> {c.estimated_visa_costs}
                      </p>
                      <p className="text-[10px] font-mono text-slate-500">Last Verified: {c.last_verified_date}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ==============================================================
              5. CANDIDATE PROFILE & IMMIGRATION EDITOR
          ============================================================== */}
          {activeSection === "Candidate Profile" && profileData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="p-5 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-4">
                <h3 className="text-sm font-semibold text-white">Verified Candidate Profile</h3>
                <div className="space-y-2 text-xs">
                  <p>
                    <strong className="text-slate-400">Name:</strong> {profileData.profile.full_name}
                  </p>
                  <p>
                    <strong className="text-slate-400">Headline:</strong> {profileData.profile.headline}
                  </p>
                  <p>
                    <strong className="text-slate-400">GitHub:</strong>{" "}
                    <a href={profileData.profile.github_url} target="_blank" rel="noreferrer" className="text-sky-400 underline">
                      {profileData.profile.github_url}
                    </a>
                  </p>
                  <p>
                    <strong className="text-slate-400">Portfolio Website:</strong>{" "}
                    <a href={profileData.profile.website_url} target="_blank" rel="noreferrer" className="text-sky-400 underline">
                      {profileData.profile.website_url}
                    </a>
                  </p>
                  <p className="text-slate-300 pt-2">{profileData.profile.summary}</p>
                </div>

                <div className="pt-3 border-t border-slate-800 space-y-2">
                  <h4 className="text-xs font-mono uppercase text-sky-400">Education</h4>
                  {profileData.profile.education.map((ed: any, idx: number) => (
                    <div key={idx} className="p-2.5 rounded bg-[#050914] border border-slate-900 text-xs">
                      <p className="font-semibold text-white">{ed.degree}</p>
                      <p className="text-slate-400">
                        {ed.institution} • Completed: {ed.completion_date}
                      </p>
                    </div>
                  ))}
                </div>

                <div className="pt-3 border-t border-slate-800 space-y-2">
                  <h4 className="text-xs font-mono uppercase text-amber-400">Security & Engineering Projects</h4>
                  {profileData.profile.projects.map((pr: any, idx: number) => (
                    <div key={idx} className="p-2.5 rounded bg-[#050914] border border-slate-900 text-xs">
                      <p className="font-semibold text-white">
                        {pr.name} <span className="text-amber-300 font-mono text-[10px]">({pr.status})</span>
                      </p>
                      <p className="text-slate-400">{pr.description}</p>
                    </div>
                  ))}
                </div>

                <div className="pt-3 border-t border-slate-800 space-y-2">
                  <h4 className="text-xs font-mono uppercase text-emerald-400">
                    Employment History (Strict Factual Classification)
                  </h4>
                  {profileData.profile.employment_history.map((em: any, idx: number) => (
                    <div key={idx} className="p-2.5 rounded bg-[#050914] border border-slate-900 text-xs space-y-1">
                      <p className="font-semibold text-white">
                        {em.role} — {em.employer}
                      </p>
                      <p className="text-[11px] font-mono text-amber-300">{em.category}</p>
                      <p className="text-slate-400">{em.responsibilities}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Editable Immigration Profile */}
              <div className="p-5 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-4 h-fit">
                <h3 className="text-sm font-semibold text-white">Editable Immigration & Visa Status</h3>
                <p className="text-xs text-slate-400">
                  Update your visa status or expiry date whenever your immigration position changes.
                </p>
                <form
                  onSubmit={async (e) => {
                    e.preventDefault();
                    await fetch(`${API_BASE}/api/profile/immigration`, {
                      method: "PUT",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify(profileData.immigration),
                    });
                    notify("success", "Immigration profile saved and synced to LEXICON engine.");
                    await fetchAllCoreData();
                  }}
                  className="space-y-3 text-xs"
                >
                  <div>
                    <label className="block text-slate-400 mb-1">Nationality</label>
                    <input
                      value={profileData.immigration.nationality}
                      onChange={(e) =>
                        setProfileData({
                          ...profileData,
                          immigration: { ...profileData.immigration, nationality: e.target.value },
                        })
                      }
                      className="w-full px-3 py-1.5 rounded bg-[#050914] border border-slate-700"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Current Location</label>
                    <input
                      value={profileData.immigration.current_location}
                      onChange={(e) =>
                        setProfileData({
                          ...profileData,
                          immigration: { ...profileData.immigration, current_location: e.target.value },
                        })
                      }
                      className="w-full px-3 py-1.5 rounded bg-[#050914] border border-slate-700"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-slate-400 mb-1">UK Immigration Status</label>
                      <input
                        value={profileData.immigration.uk_immigration_status}
                        onChange={(e) =>
                          setProfileData({
                            ...profileData,
                            immigration: { ...profileData.immigration, uk_immigration_status: e.target.value },
                          })
                        }
                        className="w-full px-3 py-1.5 rounded bg-[#050914] border border-slate-700"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">UK Graduate Visa Expiry Date</label>
                      <input
                        type="date"
                        value={profileData.immigration.uk_visa_expiry_date}
                        onChange={(e) =>
                          setProfileData({
                            ...profileData,
                            immigration: { ...profileData.immigration, uk_visa_expiry_date: e.target.value },
                          })
                        }
                        className="w-full px-3 py-1.5 rounded bg-[#050914] border border-slate-700"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">UK Work Eligibility Rules</label>
                    <textarea
                      rows={3}
                      value={profileData.immigration.uk_work_eligibility}
                      onChange={(e) =>
                        setProfileData({
                          ...profileData,
                          immigration: { ...profileData.immigration, uk_work_eligibility: e.target.value },
                        })
                      }
                      className="w-full px-3 py-1.5 rounded bg-[#050914] border border-slate-700"
                    />
                  </div>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold"
                  >
                    Save Immigration Profile
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* ==============================================================
              6. CV STUDIO (SCRIBE)
          ============================================================== */}
          {activeSection === "CV Studio" && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    SCRIBE — Factual CV Management, ATS Keyword Tailoring & Side-by-Side Comparison
                  </h3>
                  <p className="text-xs text-slate-400">
                    Never invents employment history, qualifications, certifications, or dates. Travelodge UK is strictly preserved as operational/hospitality experience.
                  </p>
                </div>
                <label className="flex items-center gap-2 px-3.5 py-2 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs cursor-pointer">
                  <Upload className="w-4 h-4" />
                  Upload Master CV (.PDF, .DOCX, .TXT)
                  <input type="file" accept=".pdf,.docx,.txt" onChange={handleUploadCVFile} className="hidden" />
                </label>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {cvVersions.map((cv: any) => (
                  <div key={cv.id} className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                            cv.is_master
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                              : "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                          }`}
                        >
                          {cv.is_master ? "MASTER CV" : `TAILORED VERSION #${cv.id}`}
                        </span>
                        <h4 className="text-sm font-semibold text-white mt-1">{cv.version_name}</h4>
                      </div>
                      <div className="flex items-center gap-2">
                        <a
                          href={`${API_BASE}/api/cv/${cv.id}/export/pdf`}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-sky-300"
                        >
                          <Download className="w-3.5 h-3.5" /> PDF
                        </a>
                        <a
                          href={`${API_BASE}/api/cv/${cv.id}/export/docx`}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-amber-300"
                        >
                          <Download className="w-3.5 h-3.5" /> DOCX
                        </a>
                      </div>
                    </div>

                    <p className="text-xs text-slate-400">{cv.tailoring_notes}</p>
                    <pre className="p-3 rounded bg-[#050914] border border-slate-900 text-[11px] text-slate-300 font-mono whitespace-pre-wrap max-h-72 overflow-y-auto">
                      {cv.raw_text}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ==============================================================
              7. COVER LETTER & APPLICATION ANSWER STUDIO (SCRIBE)
          ============================================================== */}
          {activeSection === "Cover Letter Studio" && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    SCRIBE — Country-Adapted Cover Letters, STAR Examples & Screening Answers
                  </h3>
                  <p className="text-xs text-slate-400">
                    Generates natural, human-written cover letters and work-eligibility statements grounded in verified profile data.
                  </p>
                </div>
                {selectedJob && (
                  <button
                    onClick={() => handleGenerateCoverLetter(selectedJob.id)}
                    className="px-3.5 py-2 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs"
                  >
                    + Generate Cover Letter for &ldquo;{selectedJob.title}&rdquo;
                  </button>
                )}
              </div>

              {coverLetters.length === 0 ? (
                <div className="p-8 rounded-xl bg-[#0a0f1e] border border-slate-800 text-center text-xs text-slate-400">
                  No cover letters generated yet. Click the button above or select &ldquo;Prepare Application&rdquo; on any job vacancy.
                </div>
              ) : (
                <div className="space-y-4">
                  {coverLetters.map((cl: any) => (
                    <div key={cl.id} className="p-5 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-4">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-semibold text-white">{cl.title}</h4>
                        <span className="text-xs font-mono text-sky-300">{cl.country_adapted}</span>
                      </div>
                      <pre className="p-4 rounded bg-[#050914] border border-slate-900 text-xs text-slate-200 whitespace-pre-wrap font-sans leading-relaxed">
                        {cl.cover_letter_text}
                      </pre>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        <div className="p-3 rounded bg-[#050914] border border-slate-900">
                          <p className="font-mono text-amber-400 mb-1">Work Eligibility Declaration:</p>
                          <p className="text-slate-300">{cl.work_eligibility_response}</p>
                        </div>
                        <div className="p-3 rounded bg-[#050914] border border-slate-900">
                          <p className="font-mono text-sky-400 mb-1">Relocation Declaration:</p>
                          <p className="text-slate-300">{cl.relocation_response}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ==============================================================
              8. APPLICATION QUEUE & BULK SUBMISSION ENGINE (SECTIONS 13 & 14)
          ============================================================== */}
          {activeSection === "Application Queue" && (
            <div className="space-y-6">
              {/* SUBMIT ALL APPROVED APPLICATIONS — COMMAND PANEL */}
              <div className="p-5 rounded-xl bg-gradient-to-r from-[#0a1329] to-[#0f1d3d] border border-amber-500/40 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                      HUMAN-IN-THE-LOOP SAFEGUARD ACTIVE
                    </span>
                    <h3 className="text-base font-bold text-white mt-1">
                      SUBMIT ALL APPROVED APPLICATIONS
                    </h3>
                    <p className="text-xs text-slate-300">
                      Only applications with a valid SHA-256 human approval hash, active deadline, and verified eligibility may enter the submission queue.
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleQueueControl("pause")}
                      className="flex items-center gap-1 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 text-xs"
                    >
                      <Pause className="w-3.5 h-3.5" /> Pause Queue
                    </button>
                    <button
                      onClick={() => handleQueueControl("resume")}
                      className="flex items-center gap-1 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-sky-300 text-xs"
                    >
                      <Play className="w-3.5 h-3.5" /> Resume Queue
                    </button>
                    <button
                      onClick={() => handleQueueControl("cancel")}
                      className="flex items-center gap-1 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-red-300 text-xs"
                    >
                      <XCircle className="w-3.5 h-3.5" /> Cancel Queue
                    </button>
                  </div>
                </div>

                {bulkSummary && (
                  <div className="grid grid-cols-2 md:grid-cols-6 gap-3 pt-2">
                    <div className="p-2.5 rounded bg-[#050914]/90 border border-slate-800 text-xs">
                      <span className="text-slate-400 block">Queue State</span>
                      <strong className="font-mono text-sky-300 uppercase">{bulkSummary.queue_state}</strong>
                    </div>
                    <div className="p-2.5 rounded bg-[#050914]/90 border border-slate-800 text-xs">
                      <span className="text-slate-400 block">Total Evaluated</span>
                      <strong className="font-mono text-white">{bulkSummary.total_applications_evaluated}</strong>
                    </div>
                    <div className="p-2.5 rounded bg-[#050914]/90 border border-slate-800 text-xs">
                      <span className="text-slate-400 block">Ready to Submit</span>
                      <strong className="font-mono text-emerald-400">{bulkSummary.applications_ready_to_submit_count}</strong>
                    </div>
                    <div className="p-2.5 rounded bg-[#050914]/90 border border-slate-800 text-xs">
                      <span className="text-slate-400 block">Requiring Sponsorship</span>
                      <strong className="font-mono text-amber-300">{bulkSummary.jobs_requiring_sponsorship}</strong>
                    </div>
                    <div className="p-2.5 rounded bg-[#050914]/90 border border-slate-800 text-xs">
                      <span className="text-slate-400 block">Unresolved Warnings</span>
                      <strong className="font-mono text-red-400">{bulkSummary.applications_with_unresolved_warnings}</strong>
                    </div>
                    <div className="p-2.5 rounded bg-[#050914]/90 border border-slate-800 text-xs">
                      <span className="text-slate-400 block">Countries</span>
                      <strong className="font-mono text-slate-200">{bulkSummary.countries?.join(", ") || "None"}</strong>
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-sky-900/60">
                  <label className="flex items-center gap-2 text-xs text-amber-200 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={bulkExplicitConfirm}
                      onChange={(e) => setBulkExplicitConfirm(e.target.checked)}
                      className="rounded"
                    />
                    I have reviewed all prepared answers, attached CVs/cover letters, and work eligibility declarations, and grant explicit final confirmation to submit all approved applications.
                  </label>
                  <button
                    onClick={handleBulkSubmitApproved}
                    disabled={loading}
                    className="px-4 py-2 rounded bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg"
                  >
                    SUBMIT ALL APPROVED APPLICATIONS ({bulkSummary?.applications_ready_to_submit_count || 0})
                  </button>
                </div>
              </div>

              {/* Individual Application Review & Approval Cards */}
              <div className="space-y-4">
                {applications.map((app: any) => (
                  <div key={app.id} className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-3 text-xs">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <span className="font-mono text-sky-400 mr-2">APP #{app.id}</span>
                        <strong className="text-sm text-white">{app.job_title}</strong> —{" "}
                        <span className="text-slate-300">{app.employer_name}</span> ({app.country})
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2.5 py-1 rounded font-mono ${
                            app.stage === "Submitted"
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                              : app.human_approved
                              ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                              : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                          }`}
                        >
                          Stage: {app.stage}
                        </span>
                        {!app.human_approved && app.stage !== "Submitted" && (
                          <button
                            onClick={() => handleApproveApplication(app.id)}
                            className="px-3 py-1 rounded bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold"
                          >
                            Approve Application
                          </button>
                        )}
                        {app.human_approved && app.stage === "Approved" && (
                          <button
                            onClick={() => handleSingleSubmit(app.id)}
                            className="px-3 py-1 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold"
                          >
                            Submit Now
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3 rounded bg-[#050914] border border-slate-900">
                      <div>
                        <p className="text-slate-400">
                          Original URL:{" "}
                          <a href={app.job_url} target="_blank" rel="noreferrer" className="text-sky-400 underline">
                            {app.job_url}
                          </a>
                        </p>
                        <p className="text-slate-400 mt-1">
                          Attached Documents: CV Version #{app.cv_version_id} | Cover Letter #{app.cover_letter_id}
                        </p>
                        <p className="text-slate-400 mt-1">Sponsorship Info: {app.sponsorship_summary}</p>
                      </div>
                      <div>
                        <p className="text-amber-300 font-mono">Work Eligibility Answer:</p>
                        <p className="text-slate-300">{app.work_eligibility_statement}</p>
                        {app.confirmation_reference && (
                          <p className="text-emerald-400 font-mono mt-1">
                            Confirmation Ref: {app.confirmation_reference}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ==============================================================
              9. APPLICATION COMMAND CENTRE (KANBAN & TABLE)
          ============================================================== */}
          {activeSection === "Application Command Centre" && (
            <div className="space-y-5">
              <div className="flex items-center justify-between p-4 rounded-xl bg-[#0a0f1e] border border-slate-800">
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    CHRONICLE — Central Application Lifecycle Command Centre
                  </h3>
                  <p className="text-xs text-slate-400">
                    Track every stage from Discovered to Submitted, including confirmation references and audit logs.
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCommandViewMode("kanban")}
                    className={`px-3 py-1.5 rounded text-xs font-medium ${
                      commandViewMode === "kanban" ? "bg-sky-500 text-slate-950" : "bg-slate-800 text-slate-300"
                    }`}
                  >
                    Kanban Board
                  </button>
                  <button
                    onClick={() => setCommandViewMode("table")}
                    className={`px-3 py-1.5 rounded text-xs font-medium ${
                      commandViewMode === "table" ? "bg-sky-500 text-slate-950" : "bg-slate-800 text-slate-300"
                    }`}
                  >
                    Table View
                  </button>
                </div>
              </div>

              {commandViewMode === "kanban" ? (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {["Awaiting approval", "Approved", "Submitted", "Needs human intervention"].map((colStage) => (
                    <div key={colStage} className="p-3.5 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-3">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                        <span className="text-xs font-mono uppercase text-sky-400">{colStage}</span>
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900">
                          {applications.filter((a) => a.stage === colStage).length}
                        </span>
                      </div>
                      <div className="space-y-2.5">
                        {applications
                          .filter((a) => a.stage === colStage)
                          .map((a) => (
                            <div key={a.id} className="p-3 rounded-lg bg-[#050914] border border-slate-800/80 text-xs space-y-1">
                              <p className="font-semibold text-white">{a.job_title}</p>
                              <p className="text-slate-400">
                                {a.employer_name} • {a.country}
                              </p>
                              {a.confirmation_reference && (
                                <p className="text-[11px] font-mono text-emerald-400">Ref: {a.confirmation_reference}</p>
                              )}
                            </div>
                          ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#0a0f1e]">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#050914] text-slate-400 font-mono uppercase">
                      <tr>
                        <th className="p-3">ID</th>
                        <th className="p-3">Employer</th>
                        <th className="p-3">Job Title</th>
                        <th className="p-3">Country</th>
                        <th className="p-3">Stage</th>
                        <th className="p-3">Approved</th>
                        <th className="p-3">Confirmation Ref</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {applications.map((a) => (
                        <tr key={a.id}>
                          <td className="p-3 font-mono">#{a.id}</td>
                          <td className="p-3 text-white font-medium">{a.employer_name}</td>
                          <td className="p-3">{a.job_title}</td>
                          <td className="p-3">{a.country}</td>
                          <td className="p-3 font-mono text-sky-300">{a.stage}</td>
                          <td className="p-3">{a.human_approved ? "Yes (Locked)" : "Pending"}</td>
                          <td className="p-3 font-mono text-emerald-400">{a.confirmation_reference || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ==============================================================
              10. INTERVIEW INTELLIGENCE & CYBERSECURITY MOCK LAB
          ============================================================== */}
          {activeSection === "Interview Intelligence" && interviewData && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    Cybersecurity & IT Interview Intelligence + Interactive Mock Evaluator
                  </h3>
                  <p className="text-xs text-slate-400">
                    Tailored to MSc Cybersecurity, Om (Recon), NETRA (OSINT), and Travelodge UK operational experience.
                  </p>
                </div>
                <select
                  value={selectedInterviewTrack}
                  onChange={(e) => setSelectedInterviewTrack(e.target.value)}
                  className="px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                >
                  {interviewData.available_tracks.map((t: string) => (
                    <option key={t} value={t}>
                      Track: {t}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="p-5 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-4 text-xs">
                  <h4 className="font-mono uppercase text-sky-400">Technical & Role Questions ({selectedInterviewTrack})</h4>
                  {interviewData.session.technical_questions.map((tq: any, i: number) => (
                    <div key={i} className="p-3 rounded bg-[#050914] border border-slate-900 space-y-1.5">
                      <p className="font-semibold text-white">Q: {tq.question}</p>
                      <p className="text-slate-400">
                        <strong className="text-emerald-400">Framework:</strong> {tq.suggested_answer_framework}
                      </p>
                      <button
                        onClick={() => setMockQuestion(tq.question)}
                        className="text-[11px] text-sky-400 hover:underline"
                      >
                        Practice this question in Mock Evaluator →
                      </button>
                    </div>
                  ))}
                </div>

                {/* Interactive Mock Interview Evaluator */}
                <div className="p-5 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-4 text-xs">
                  <h4 className="font-mono uppercase text-amber-400">Interactive Mock Interview Simulator</h4>
                  <p className="text-white font-semibold">Active Question: {mockQuestion}</p>
                  <textarea
                    rows={5}
                    value={mockAnswer}
                    onChange={(e) => setMockAnswer(e.target.value)}
                    placeholder="Type your spoken/written interview answer here using STAR structure and referencing SIEM, OSINT, Om, NETRA, or troubleshooting steps..."
                    className="w-full p-3 rounded bg-[#050914] border border-slate-700 text-xs"
                  />
                  <button
                    onClick={handleEvaluateMockAnswer}
                    className="px-4 py-2 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold"
                  >
                    Evaluate Mock Response
                  </button>

                  {mockFeedback && (
                    <div className="p-4 rounded bg-[#050914] border border-sky-500/40 space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-mono text-sky-300">Overall Score:</span>
                        <span className="text-lg font-bold font-mono text-emerald-400">{mockFeedback.overall_score}/100</span>
                      </div>
                      <div className="grid grid-cols-5 gap-2 text-center font-mono text-[11px]">
                        {Object.entries(mockFeedback.scores).map(([k, v]: any) => (
                          <div key={k} className="p-1.5 rounded bg-slate-900">
                            <span className="block text-slate-400 capitalize">{k.slice(0, 8)}</span>
                            <strong className="text-white">{v}</strong>
                          </div>
                        ))}
                      </div>
                      <p className="text-slate-300">{mockFeedback.constructive_feedback}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ==============================================================
              11. EMPLOYER INTELLIGENCE (SCOUT)
          ============================================================== */}
          {activeSection === "Employer Intelligence" && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800">
                <h3 className="text-sm font-semibold text-white">
                  SCOUT — Employer Sponsorship Capability, Citations & Watchlist
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {employers.map((emp: any) => (
                  <div key={emp.id} className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-bold text-white">{emp.name}</h4>
                      <button
                        onClick={async () => {
                          await fetch(`${API_BASE}/api/employers/${emp.id}/toggle-watchlist`, { method: "POST" });
                          await fetchAllCoreData();
                        }}
                        className={`px-2.5 py-1 rounded font-mono text-[11px] ${
                          emp.is_watchlisted
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {emp.is_watchlisted ? "★ Watchlisted" : "☆ Add to Watchlist"}
                      </button>
                    </div>
                    <p className="text-slate-400">
                      {emp.country} • {emp.industry} • Size: {emp.company_size}
                    </p>
                    <p className="text-slate-300">{emp.overview}</p>
                    <p className="font-mono text-sky-300">Sponsorship Capability: {emp.sponsorship_capability_status}</p>
                    <p className="text-slate-400">Hiring Process: {emp.hiring_process}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ==============================================================
              12. RELOCATION INTELLIGENCE
          ============================================================== */}
          {activeSection === "Relocation Intelligence" && relocationData && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-[#0a0f1e] border border-amber-500/30 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    International City Cost-of-Living, Tax, Rent & Visa Budget Calculator
                  </h3>
                  <p className="text-xs text-amber-300 font-mono">
                    {relocationData.selected_city.is_estimate_disclaimer}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={selectedCity}
                    onChange={(e) => setSelectedCity(e.target.value)}
                    className="px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs"
                  >
                    {relocationData.available_cities.map((c: string) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                  <input
                    type="number"
                    placeholder="Custom Gross Annual Salary"
                    value={customGrossSalary}
                    onChange={(e) => setCustomGrossSalary(e.target.value)}
                    className="px-3 py-1.5 rounded bg-[#050914] border border-slate-700 text-xs w-48"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-2">
                  <h4 className="font-mono uppercase text-sky-400">Estimated Income ({relocationData.selected_city.currency})</h4>
                  <p className="flex justify-between">
                    <span className="text-slate-400">Gross Annual:</span>
                    <strong className="font-mono">{relocationData.selected_city.gross_annual_salary.toLocaleString()}</strong>
                  </p>
                  <p className="flex justify-between">
                    <span className="text-slate-400">Est. Effective Tax Rate:</span>
                    <strong className="font-mono">{relocationData.selected_city.estimated_effective_tax_rate_percent}%</strong>
                  </p>
                  <p className="flex justify-between">
                    <span className="text-slate-400">Est. Net Monthly Take-Home:</span>
                    <strong className="font-mono text-emerald-400">
                      {relocationData.selected_city.estimated_net_monthly_salary.toLocaleString()}
                    </strong>
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-2">
                  <h4 className="font-mono uppercase text-amber-400">Monthly Living Cost Estimates</h4>
                  <p className="flex justify-between">
                    <span className="text-slate-400">Rent:</span>
                    <strong className="font-mono">
                      {relocationData.selected_city.monthly_cost_breakdown_estimates.rent.toLocaleString()}
                    </strong>
                  </p>
                  <p className="flex justify-between">
                    <span className="text-slate-400">Transport & Food:</span>
                    <strong className="font-mono">
                      {(
                        relocationData.selected_city.monthly_cost_breakdown_estimates.transport +
                        relocationData.selected_city.monthly_cost_breakdown_estimates.food
                      ).toLocaleString()}
                    </strong>
                  </p>
                  <p className="flex justify-between border-t border-slate-800 pt-1">
                    <span className="text-slate-300">Estimated Monthly Savings:</span>
                    <strong className="font-mono text-sky-300">
                      {relocationData.selected_city.estimated_monthly_savings.toLocaleString()}
                    </strong>
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-2">
                  <h4 className="font-mono uppercase text-emerald-400">Upfront Relocation Buffer</h4>
                  <p className="flex justify-between">
                    <span className="text-slate-400">Est. Visa Fees:</span>
                    <strong className="font-mono">
                      {relocationData.selected_city.upfront_relocation_costs_estimate.visa_fees.toLocaleString()}
                    </strong>
                  </p>
                  <p className="flex justify-between">
                    <span className="text-slate-400">Recommended Total Buffer:</span>
                    <strong className="font-mono text-amber-300">
                      {relocationData.selected_city.upfront_relocation_costs_estimate.total_recommended_relocation_buffer.toLocaleString()}
                    </strong>
                  </p>
                  <p className="text-[11px] text-slate-400 pt-1">{relocationData.selected_city.notes}</p>
                </div>
              </div>
            </div>
          )}

          {/* ==============================================================
              13. REPORTS & ANALYTICS
          ============================================================== */}
          {activeSection === "Reports and Analytics" && (
            <div className="p-6 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-4">
              <h3 className="text-sm font-semibold text-white">Executive Recruitment & Sponsorship Reports</h3>
              <p className="text-xs text-slate-400">
                Download live, verifiable recruitment intelligence, country comparisons, and application audit summaries in PDF or CSV format.
              </p>
              <div className="flex flex-wrap gap-3">
                <a
                  href={`${API_BASE}/api/reports/export/pdf`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2 px-4 py-2 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs"
                >
                  <Download className="w-4 h-4" /> Export Executive Recruitment Report (PDF)
                </a>
                <a
                  href={`${API_BASE}/api/reports/export/csv`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2 px-4 py-2 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 font-semibold text-xs"
                >
                  <Download className="w-4 h-4" /> Export Full Jobs & Sponsorship Matrix (CSV)
                </a>
              </div>
            </div>
          )}

          {/* ==============================================================
              14. AI PROJECT MANAGER DASHBOARD (SECTION 19)
          ============================================================== */}
          {activeSection === "AI Project Manager" && pmData && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800">
                <h3 className="text-sm font-semibold text-white">
                  PROJECT MANAGER — Autonomous Repository Inspection, Agent Fleet & Security Readiness
                </h3>
                <p className="text-xs text-slate-400 font-mono mt-0.5">Root: {pmData.repository_root}</p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                {Object.entries(pmData.codebase_metrics).map(([k, v]: any) => (
                  <div key={k} className="p-3.5 rounded-xl bg-[#0a0f1e] border border-slate-800">
                    <span className="text-slate-400 capitalize">{k.replace(/_/g, " ")}</span>
                    <p className="text-xl font-bold font-mono text-sky-400 mt-1">{v}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-2.5">
                  <h4 className="text-xs font-mono uppercase text-sky-400">9-Agent Fleet Status</h4>
                  {pmData.agents.map((ag: any) => (
                    <div key={ag.code} className="p-2.5 rounded bg-[#050914] border border-slate-900 text-xs flex justify-between">
                      <div>
                        <strong className="text-amber-300 font-mono">{ag.code}</strong> —{" "}
                        <span className="text-white">{ag.name}</span>
                        <p className="text-[11px] text-slate-400">{ag.responsibility}</p>
                      </div>
                      <span className="text-emerald-400 font-mono text-[11px]">{ag.status}</span>
                    </div>
                  ))}
                </div>

                <div className="p-4 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-2.5">
                  <h4 className="text-xs font-mono uppercase text-emerald-400">Engineering & Security Roadmap Tasks</h4>
                  {pmData.tasks.map((t: any) => (
                    <div key={t.id} className="p-3 rounded bg-[#050914] border border-slate-900 text-xs space-y-1">
                      <div className="flex justify-between">
                        <strong className="text-white">{t.title}</strong>
                        <span className="text-emerald-400 font-mono">{t.status}</span>
                      </div>
                      <p className="text-slate-400">{t.description}</p>
                      <p className="text-[10px] font-mono text-sky-300">{t.verification_evidence}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ==============================================================
              15. SETTINGS & PRIVACY CONTROLS (SECTIONS 21 & 22)
          ============================================================== */}
          {activeSection === "Settings" && settingsData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="p-5 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-4 text-xs">
                <h3 className="text-sm font-semibold text-white">AI Provider & Model Configuration</h3>
                <p className="text-slate-400">
                  Supports deterministic zero-cost offline fallback, local Ollama, Gemini, Claude, and OpenAI-compatible APIs. Keys are encrypted at rest with Fernet.
                </p>
                <div className="space-y-3">
                  <div>
                    <label className="block text-slate-400 mb-1">Active AI Provider</label>
                    <select
                      value={settingsData.ai_provider}
                      onChange={(e) => setSettingsData({ ...settingsData, ai_provider: e.target.value })}
                      className="w-full px-3 py-1.5 rounded bg-[#050914] border border-slate-700"
                    >
                      <option value="deterministic">Deterministic Rule Engine (Free / Instant / Offline)</option>
                      <option value="ollama">Ollama Local LLM (http://localhost:11434)</option>
                      <option value="gemini">Google Gemini API</option>
                      <option value="claude">Anthropic Claude API</option>
                      <option value="openai">OpenAI-Compatible API</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Model Name</label>
                    <input
                      value={settingsData.ai_model}
                      onChange={(e) => setSettingsData({ ...settingsData, ai_model: e.target.value })}
                      className="w-full px-3 py-1.5 rounded bg-[#050914] border border-slate-700"
                    />
                  </div>
                  <button
                    onClick={async () => {
                      await fetch(`${API_BASE}/api/settings`, {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(settingsData),
                      });
                      notify("success", "AI & Automation settings persisted to database.");
                      await fetchAllCoreData();
                    }}
                    className="px-4 py-2 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold"
                  >
                    Save Settings
                  </button>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-[#0a0f1e] border border-slate-800 space-y-4 text-xs h-fit">
                <h3 className="text-sm font-semibold text-white">Security, Privacy & Data Portability</h3>
                <p className="text-slate-400">
                  Human Approval Checkpoint is permanently enforced (`require_human_approval = true`). Export your full personal dataset at any time.
                </p>
                <a
                  href={`${API_BASE}/api/privacy/export-all`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 font-semibold"
                >
                  <Download className="w-4 h-4" /> Export All Personal Data (JSON)
                </a>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

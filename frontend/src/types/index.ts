export type UserRole = "admin" | "recruiter";

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  company_id: number | null;
  is_active: boolean;
}

export type JobStatus = "draft" | "published" | "closed" | "archived";
export type JobType = "full_time" | "part_time" | "internship" | "contract" | "temporary";
export type JobModality = "on_site" | "remote" | "hybrid";

export interface JobListItem {
  id: number;
  title: string;
  code: string;
  status: JobStatus;
  department: string | null;
  location: string | null;
  created_at: string;
}

export interface Job extends JobListItem {
  criteria_version: number;
  company_id: number;
  description: string;
  job_type: JobType;
  modality: JobModality;
  min_experience_years: number;
  education_level: string | null;
  published_at: string | null;
  closed_at: string | null;
}

export type RequirementCategory =
  | "education" | "experience" | "technical_skill" | "technology"
  | "tool" | "language" | "certification" | "soft_skill" | "other";

export interface JobRequirement {
  id: number;
  job_id: number;
  name: string;
  description: string | null;
  category: RequirementCategory;
  weight: number;
  expected_level: string;
  is_mandatory: boolean;
}

export interface JobDetail extends Job {
  requirements: JobRequirement[];
}

export type ApplicationSource = "upload" | "email";
export type ApplicationStatus =
  | "received" | "in_analysis" | "analyzed" | "recommended" | "in_evaluation"
  | "interview_selected" | "interviewed" | "rejected" | "hired";

export interface Candidate {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  location: string | null;
}

export interface Resume {
  version: number;
  id: number;
  original_filename: string;
  content_type: string | null;
  file_size_bytes: number | null;
  uploaded_at: string;
}

export interface Application {
  analysis_status: string;
  id: number;
  candidate_id: number;
  job_id: number;
  source: ApplicationSource;
  status: ApplicationStatus;
  score: number | null;
  recruiter_notes: string | null;
  created_at: string;
}

export interface ApplicationDetail extends Application {
  analysis_id: number | null;
  analysis_execution_id: string | null;
  analysis_method: string | null;
  analysis_error: string | null;
  latest_resume_id: number | null;
  stale: boolean;
  recommendation_label: string | null;
  candidate: Candidate;
  resumes: Resume[];
}

export type RecommendationLabel =
  | "Recomendado" | "Avaliar" | "Baixa compatibilidade" | "Requisito obrigatório ausente";

export interface RequirementBreakdownItem {
  requirement_id: number;
  name: string;
  category: RequirementCategory;
  is_mandatory: boolean;
  weight: number;
  met: boolean;
  match_score: number;
  contribution: number;
  evidence: string | null;
}

export interface AnalysisResult {
  stale: boolean;
  criteria_version: number;
  id: number;
  application_id: number;
  overall_score: number;
  recommendation_label: RecommendationLabel;
  mandatory_missing: string[];
  breakdown: RequirementBreakdownItem[];
  computed_at: string;
}

export interface RankingItem {
  analysis_method: string | null;
  analysis_error: string | null;
  stale: boolean;
  analysis_status: string;
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  candidate_email: string;
  score: number | null;
  recommendation_label: RecommendationLabel | null;
  mandatory_missing: string[];
  status: ApplicationStatus;
}

export type InterviewResult = "scheduled" | "completed" | "cancelled" | "no_show";

export interface Interview {
  id: number;
  application_id: number;
  scheduled_at: string;
  interviewers: string | null;
  location_or_link: string | null;
  notes: string | null;
  result: InterviewResult;
  result_notes: string | null;
}

export type RecruiterRating = "very_suitable" | "suitable" | "partially_suitable" | "not_suitable";

export interface RecruiterFeedback {
  application_id: number;
  system_recommended: boolean;
  selected_for_interview: boolean;
  hired: boolean;
  rating: RecruiterRating | null;
  comments: string | null;
}

export interface ProcessingLog {
  id: number;
  source: ApplicationSource;
  candidate_email: string | null;
  document_name: string | null;
  application_id: number | null;
  status: "processed" | "error";
  error_message: string | null;
  created_at: string;
}

export interface EmailAccountRead {
  id: number;
  email_address: string;
  provider: "gmail" | "outlook" | "imap";
  status: "connected" | "error" | "disconnected";
  sync_frequency_minutes: number;
  last_sync_at: string | null;
  last_sync_error: string | null;
  messages_processed_count: number;
  cvs_found_count: number;
  cvs_analyzed_count: number;
  errors_count: number;
  created_at: string;
}
